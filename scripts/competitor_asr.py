"""Transcribe the local media in the competitor inventory with resumable Coli chunks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

from competitor_intake import ROOT

CHUNK = 45
OVERLAP = 1


def run(*command):
    result = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Exit code {result.returncode}")
    return result.stdout


def save(path, content):
    temporary = path.with_suffix(".partial")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def transcribe(source, output, runtime, tools, trial):
    ffmpeg = tools / "ffmpeg.exe"
    ffprobe = tools / "ffprobe.exe"
    info = json.loads(run(ffprobe, "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", source))
    duration = float(info["format"]["duration"])
    with source.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    chunks = []
    with tempfile.TemporaryDirectory() as directory:
        wave = Path(directory) / "chunk.wav"
        starts = range(0, math.ceil(duration), CHUNK)
        for index, start in enumerate(starts):
            if trial and index > 0:
                break
            path = output / f"{index:03}.json"
            offset = max(0, start - OVERLAP)
            end = min(duration, start + CHUNK + OVERLAP)
            settings = dict(source_sha256=digest, offset=offset, end=end)
            if path.is_file():
                chunk = json.loads(path.read_text(encoding="utf-8"))
                if any(chunk[key] != value for key, value in settings.items()):
                    raise ValueError(f"Source or timing changed: {path}")
            else:
                run(ffmpeg, "-nostdin", "-v", "error", "-y", "-ss", str(offset),
                    "-i", source, "-t", str(end - offset), "-map", "0:a:0",
                    "-ar", "16000", "-ac", "1", wave)
                for _ in range(2):
                    result = subprocess.run(
                        [runtime["coli_bin"], "asr", "-j", "--model", "sensevoice",
                         "--language", "zh", wave],
                        capture_output=True, encoding="utf-8", timeout=180,
                    )
                    if result.stderr:
                        save(output / f"{index:03}.stderr.log", result.stderr)
                    result.check_returncode()
                    chunk = json.loads(result.stdout)
                    if chunk["tokens"] or end - offset <= 5:
                        break
                tokens, times = chunk["tokens"], chunk["timestamps"]
                if len(tokens) != len(times) or (chunk["text"] and not tokens):
                    raise ValueError(f"Invalid token alignment: {source} at {offset}")
                if not tokens and end - offset > 5:
                    raise ValueError(f"Empty recognition: {source} at {offset}")
                chunk.update(settings)
                save(path, json.dumps(chunk, ensure_ascii=False))
            chunks.append(chunk)
    return duration, chunks


def markdown(video, source, duration, chunks):
    parts = [
        f"# {video}\n",
        f"> Coli SenseVoice ASR · {source.name} · {duration:.3f} s · 待听校。"
        "时间取保留词元起点，原始识别保存在 raw/asr。\n",
    ]
    for index, chunk in enumerate(chunks):
        start = index * CHUNK
        tokens = [
            (token, chunk["offset"] + time)
            for token, time in zip(chunk["tokens"], chunk["timestamps"])
            if start <= chunk["offset"] + time < start + CHUNK
        ]
        if tokens:
            seconds = int(tokens[0][1])
            words = "".join(token for token, _ in tokens).replace("▁", " ").strip()
            parts.append(f"[{seconds // 60:02}:{seconds % 60:02}] {words}\n")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--trial", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    runtime_file = Path(os.environ["LOCALAPPDATA"]) / "story-studio/runtime.json"
    runtime = json.loads(runtime_file.read_text(encoding="utf-8-sig"))
    tools = next(Path(path) for path in runtime["tool_dirs"]
                 if (Path(path) / "ffprobe.exe").is_file())
    os.environ["PATH"] = str(tools) + os.pathsep + os.environ["PATH"]
    raw = ROOT / "raw"
    with args.inventory.open(encoding="utf-8-sig", newline="") as handle:
        inventory = list(csv.DictReader(handle))
    def process(row):
        video = row["video_id"]
        source = args.inventory.parent / row["local_file"]
        if source.suffix.lower() not in {".m4a", ".mp4"} or (args.ids and video not in args.ids):
            return None
        output = raw / "asr" / video
        target = output / ("trial.md" if args.trial else "transcript.md")
        try:
            duration, chunks = transcribe(source, output, runtime, tools, args.trial)
            save(target, markdown(video, source, duration, chunks))
            print(video, round(duration, 3), len(chunks), target.name, flush=True)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            print(video, "ERROR", exc, flush=True)
            return video, str(exc)
        return None

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        failures = dict(result for result in pool.map(process, inventory) if result)
    save(raw / "asr" / ("trial_errors.json" if args.trial else "errors.json"),
         json.dumps(failures, ensure_ascii=False, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
