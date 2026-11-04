"""Doubao V3 bidirectional WebSocket TTS to a verified MP3; no automatic retries."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
from dataclasses import dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import uuid




URL = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
CONNECTION_EVENTS = {1, 2, 50, 51, 52}


class TtsError(RuntimeError):
    pass


def pack(event: int, body: dict, session_id: str = "") -> bytes:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    frame = b"\x11\x14\x10\x00" + struct.pack(">I", event)
    if event not in CONNECTION_EVENTS:
        session = session_id.encode("utf-8")
        frame += struct.pack(">I", len(session)) + session
    return frame + struct.pack(">I", len(payload)) + payload


@dataclass
class Message:
    kind: int
    event: int
    session_id: str
    payload: bytes


def unpack(frame: bytes) -> Message:
    if not isinstance(frame, bytes) or len(frame) < 4 or frame[0] >> 4 != 1:
        raise TtsError("Invalid TTS binary frame")
    offset = (frame[0] & 15) * 4
    kind, flags, compression = frame[1] >> 4, frame[1] & 15, frame[2] & 15
    if offset < 4 or offset > len(frame) or kind not in {9, 11, 15}:
        raise TtsError("Unsupported TTS frame header")
    def take(size):
        nonlocal offset
        if size < 0 or offset + size > len(frame):
            raise TtsError("Truncated TTS frame")
        value = frame[offset:offset + size]
        offset += size
        return value
    def number():
        return struct.unpack(">I", take(4))[0]
    def blob():
        return take(number())
    error = number() if kind == 15 else None
    if kind != 15 and flags & 3 in {1, 3}:
        take(4)  # Optional sequence number, before the event.
    event, session_id = 0, ""
    if flags & 4:
        event = number()
        if event in {50, 51, 52}:
            blob()  # Connection ID, not a session ID.
        elif event not in CONNECTION_EVENTS:
            try:
                session_id = blob().decode("utf-8")
            except UnicodeError:
                raise TtsError("Invalid TTS session ID") from None
    payload = blob()
    if offset != len(frame):
        raise TtsError("Unexpected data after TTS frame")
    if compression == 1:
        try:
            payload = gzip.decompress(payload)
        except (OSError, EOFError):
            raise TtsError("Invalid compressed TTS payload") from None
    elif compression != 0:
        raise TtsError("Unsupported TTS compression")
    if error is not None:
        raise TtsError(f"TTS service error code {error}")
    if event in {51, 151, 153}:
        code = None
        with contextlib.suppress(ValueError, AttributeError):
            body = json.loads(payload)
            candidate = body.get("code", body.get("status_code"))
            if type(candidate) is int:
                code = candidate
        raise TtsError(f"TTS service rejected the connection or session (event {event}, code {code})")
    return Message(kind, event, session_id, payload)


def text_chunks(text: str, max_bytes: int = 800):
    """Transport chunks preserve every character; this is not a total service limit."""
    chunk, size = [], 0
    for char in text:
        width = len(char.encode("utf-8"))
        if chunk and size + width > max_bytes:
            yield "".join(chunk)
            chunk, size = [], 0
        chunk.append(char)
        size += width
    if chunk:
        yield "".join(chunk)


def request_body(profile: dict, event: int, text: str | None = None) -> dict:
    params = {"speaker": profile["speaker"], "audio_params": {
        "format": "mp3", "sample_rate": 24000, "speech_rate": profile.get("speech_rate", 0),
        "loudness_rate": profile.get("loudness_rate", 0), "enable_subtitle": False}}
    if profile.get("model"):
        params["model"] = profile["model"]
    if text is not None:
        params["text"] = text
    return {"user": {"uid": "story-studio"}, "namespace": "BidirectionalTTS", "event": event, "req_params": params}


async def receive(socket) -> Message:
    return unpack(await asyncio.wait_for(socket.recv(), timeout=120))


async def expect(socket, event: int, session: str = "") -> None:
    message = await receive(socket)
    if message.kind != 9 or message.event != event or (session and message.session_id != session):
        raise TtsError("Unexpected TTS session state")


async def stream_session(socket, text: str, profile: dict, target) -> int:
    session = str(uuid.uuid4())
    await socket.send(pack(1, {}))
    await expect(socket, 50)
    await socket.send(pack(100, request_body(profile, 100), session))
    await expect(socket, 150, session)
    async def send_text():
        for chunk in text_chunks(text):
            await socket.send(pack(200, request_body(profile, 200, chunk), session))
            await asyncio.sleep(0)
        await socket.send(pack(102, {}, session))
    sender = asyncio.create_task(send_text())
    size = 0
    try:
        while True:
            message = await receive(socket)
            if message.session_id != session and not (message.kind == 11 and not message.session_id and message.event == 0):
                raise TtsError("TTS response belongs to a different session")
            if message.kind == 11 and message.event in {0, 352}:
                target.write(message.payload)
                size += len(message.payload)
            elif message.kind == 9 and message.event == 152:
                await sender
                if not size:
                    raise TtsError("TTS completed without audio")
                break
            elif message.kind != 9 or message.event not in {154, 350, 351, 359}:
                raise TtsError("Unexpected TTS response event")
        # Audio is complete after SessionFinished. A later connection-close error
        # must not discard completed audio or trigger another paid request.
        with contextlib.suppress(Exception):
            await socket.send(pack(2, {}))
            await expect(socket, 52)
        return size
    finally:
        if not sender.done():
            sender.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await sender


async def synthesize(text: str, profile: dict, key: str, partial: Path) -> None:
    from websockets.asyncio.client import connect
    headers = {"X-Api-Key": key, "X-Api-Resource-Id": profile["resource_id"],
               "X-Api-Connect-Id": str(uuid.uuid4())}
    # A single connection attempt; never use connect as an automatic-retry iterator.
    async with connect(URL, additional_headers=headers, open_timeout=30, close_timeout=5,
                       max_size=10 * 1024 * 1024) as socket:
        with partial.open("xb") as output:
            await asyncio.wait_for(stream_session(socket, text, profile, output), timeout=1800)


def validate_audio(path: Path, ffprobe: str, ffmpeg: str) -> float:
    result = subprocess.run([ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                            capture_output=True, text=True, encoding="utf-8", check=True, timeout=120)
    info = json.loads(result.stdout)
    duration = float(info.get("format", {}).get("duration", 0))
    if duration <= 0 or not any(stream.get("codec_name") == "mp3" for stream in info.get("streams", [])):
        raise TtsError("TTS result is not a nonempty MP3")
    subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
                   capture_output=True, check=True, timeout=600)
    return duration

