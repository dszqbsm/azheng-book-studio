"""Check DevPoolAi access or generate one image over a selected Windows interface."""

import argparse
import base64
import http.client
import io
import json
import os
import socket
import struct
from pathlib import Path
from uuid import uuid4

from PIL import Image


HOST = "xuseny.online"
MODEL = "gpt-image-2.6"
KEY_NAME = "DEVPOOL_API_KEY"
IP_UNICAST_IF = 31  # Windows Winsock option at IPPROTO_IP level.


def api_key():
    key = os.environ.get(KEY_NAME, "").strip()
    if not key and os.name == "nt":
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as environment:
            try:
                key = winreg.QueryValueEx(environment, KEY_NAME)[0].strip()
            except FileNotFoundError:
                pass
    if not key:
        raise ValueError(f"{KEY_NAME} is missing")
    return key


class DevPoolConnection(http.client.HTTPSConnection):
    def __init__(self, interface_index):
        super().__init__(HOST, timeout=12)
        if interface_index is not None:
            if os.name != "nt":
                raise ValueError("Binding by interface index requires Windows")
            self._create_connection = self.bind_interface(interface_index)

    @staticmethod
    def bind_interface(interface_index):
        def connect(address, timeout, source_address):
            host, port = address
            destination = socket.gethostbyname(host)
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                connection.settimeout(timeout)
                connection.setsockopt(
                    socket.IPPROTO_IP, IP_UNICAST_IF, struct.pack("!I", interface_index)
                )
                connection.connect((destination, port))
                return connection
            except OSError:
                connection.close()
                raise

        return connect


def request(method, endpoint, interface_index, payload=None, content_type="application/json"):
    headers = {"Authorization": f"Bearer {api_key()}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = content_type
        if content_type == "application/json":
            payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    conn = DevPoolConnection(interface_index)
    try:
        conn.connect()
        conn.sock.settimeout(240 if method == "POST" else 15)
        conn.request(method, endpoint, body=payload, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f"DevPoolAi returned HTTP {response.status} for {endpoint}")
        return json.load(response)
    finally:
        conn.close()


def reference_form(fields, references):
    boundary = uuid4().hex
    delimiter = f"--{boundary}\r\n".encode("ascii")
    parts = []
    for field, value in fields.items():
        header = f'Content-Disposition: form-data; name="{field}"\r\n\r\n'
        parts.extend((delimiter, header.encode("ascii"), str(value).encode("utf-8"), b"\r\n"))

    for index, reference in enumerate(references, start=1):
        contents = reference.read_bytes()
        with Image.open(io.BytesIO(contents)) as image:
            image_format = image.format
            if image_format not in ("PNG", "JPEG", "WEBP"):
                raise ValueError(f"Unsupported reference image format: {image_format}")
            image.verify()
        header = (
            f'Content-Disposition: form-data; name="image[]"; '
            f'filename="reference-{index}.{image_format.lower()}"\r\n'
            f"Content-Type: {Image.MIME[image_format]}\r\n\r\n"
        )
        parts.extend((delimiter, header.encode("ascii"), contents, b"\r\n"))
    parts.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def generate(args):
    if args.out.exists():
        raise FileExistsError(f"Output already exists: {args.out}")

    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": 1,
        "output_format": "png",
    }
    if args.reference:
        body, content_type = reference_form(payload, args.reference)
        result = request("POST", "/v1/images/edits", args.interface_index, body, content_type)
    else:
        result = request("POST", "/v1/images/generations", args.interface_index, payload)
    images = result.get("data") or []
    if len(images) != 1 or not images[0].get("b64_json"):
        raise ValueError("DevPoolAi did not return one base64 image")
    contents = base64.b64decode(images[0]["b64_json"], validate=True)
    with Image.open(io.BytesIO(contents)) as image:
        if image.format != "PNG":
            raise ValueError(f"Expected PNG, received {image.format}")
        image.load()
        width, height = image.size
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("xb") as output:
        output.write(contents)
    print(f"Saved {width}x{height} PNG: {args.out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface-index", type=int)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    image_parser = commands.add_parser("generate")
    image_parser.add_argument("--prompt", required=True)
    image_parser.add_argument("--out", type=Path, required=True)
    image_parser.add_argument("--size", default="1024x1024")
    image_parser.add_argument("--quality", choices=("low", "medium", "high", "auto"), default="low")
    image_parser.add_argument("--reference", type=Path, action="append", help="Image to guide the output")
    args = parser.parse_args()

    try:
        if args.command == "check":
            models = request("GET", "/v1/models", args.interface_index)
            if not any(model.get("id") == MODEL for model in models.get("data", [])):
                raise ValueError(f"Model list did not include {MODEL}")
            print(f"HTTP 200: {MODEL}")
        else:
            generate(args)
    except (OSError, ValueError, http.client.HTTPException) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
