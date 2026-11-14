#!/usr/bin/env python3
"""Call DeepSeek tools using the official API and an environment credential."""
import argparse
import http.client
import io
import json
import mimetypes
import os
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave
from pathlib import Path

ORIGIN = "https://api.deepseek.com"
DOCUMENT_LIMIT = 100 * 1024 * 1024
AUDIO_LIMIT = 8 * 1024 * 1024
MAX_WAV = 96 * 1024 * 1024
MESSAGES = "/anthropic/v1/messages"
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


class APIError(Exception):
    def __init__(self, message, status=None):
        super().__init__(f"HTTP {status}: {message}" if status is not None else message)
        self.status = status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def error_message(data):
    error = data.get("error", {})
    return str(error.get("message") or error.get("type") or "API error") if isinstance(error, dict) else str(error)


class DeepSeek:
    def __init__(self, key, timeout):
        self.key = key
        self.timeout = timeout
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, path, payload=None, *, binary=None, method="POST", wav=False, extra_headers=None):
        headers = {"Authorization": f"Bearer {self.key}"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if binary is not None:
            body, headers["Content-Type"] = binary
        headers.update(extra_headers or {})
        request = urllib.request.Request(ORIGIN + path, body, headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                is_wav = wav and response.headers.get_content_type() in ("audio/wav", "audio/wave", "audio/x-wav")
                limit = MAX_WAV if is_wav else 32 * 1024 * 1024
                output = response.read(limit + 1)
                status = response.status
        except urllib.error.HTTPError as exc:
            with exc:
                raw = exc.read(32 * 1024)
            try:
                message = error_message(json.loads(raw))
            except (ValueError, AttributeError):
                message = exc.reason
            raise APIError(str(message), exc.code) from None
        if len(output) > limit:
            raise APIError("Response exceeded the local size limit")
        if is_wav:
            return output
        try:
            decoded = json.loads(output)
        except (ValueError, UnicodeError):
            raise APIError("Expected a valid JSON response", status) from None
        if not isinstance(decoded, dict):
            raise APIError("Expected a JSON object", status)
        if decoded.get("error"):
            raise APIError(error_message(decoded), status)
        if wav:
            raise APIError("Expected a WAV response", status)
        return decoded

    def message(self, content, args, tool=None, document=False):
        if isinstance(content, str):
            require_text(content)
        payload = {
            "model": "deepseek-flash",
            "max_tokens": args.max_tokens,
            "thinking": {"type": "enabled" if args.thinking else "disabled"},
            "messages": [{"role": "user", "content": content}],
        }
        if tool:
            payload["tools"] = [{"type": tool, "name": tool}]
        if args.safety_high:
            payload["safety_check"] = {"level": "high"}
        headers = {"anthropic-version": "2023-06-01"}
        if document:
            headers["anthropic-beta"] = "files-api-2025-04-14"
        return self.request(MESSAGES, payload, extra_headers=headers)


def file_form(path, fields, limit):
    if not path.is_file():
        raise ValueError(f"Expected a local file: {path}")
    if path.stat().st_size > limit:
        raise ValueError(f"File exceeds {limit // (1024 * 1024)} MiB")
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if not data or len(data) > limit:
        raise ValueError("File is empty or exceeds the size limit")
    filename = re.sub(r"[^A-Za-z0-9_.-]", "_", path.stem)[:100] or "upload"
    suffix = re.sub(r"[^A-Za-z0-9.]", "", path.suffix)[:16]
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    boundary = uuid.uuid4().hex
    chunks = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        for name, value in fields
    ]
    chunks.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}{suffix}"\r\n'
        f'Content-Type: {mime}\r\n\r\n'.encode()
    )
    chunks.extend((data, f'\r\n--{boundary}--\r\n'.encode()))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def document_qa(api, args):
    require_text(args.question)
    if args.file.suffix.lower() in DOCUMENT_EXTENSIONS:
        purpose = "rich_layout_recognition" if args.layout else "text_recognition"
        limit = DOCUMENT_LIMIT
    elif args.layout:
        raise ValueError("--layout applies to PDF, Word, PowerPoint, and images")
    else:
        purpose, limit = "user_data", 32 * 1024 * 1024
    fields = [("purpose", purpose), ("expires_after[anchor]", "created_at"), ("expires_after[seconds]", "3600")]
    upload = api.request("/files", binary=file_form(args.file, fields, limit))
    file_id = upload.get("id")
    if not isinstance(file_id, str) or not re.fullmatch(r"file-api-[A-Za-z0-9_-]+", file_id):
        raise APIError("Upload response did not contain a valid file id")
    content = [
        {"type": "document", "source": {"type": "file", "file_id": file_id}},
        {"type": "text", "text": args.question},
    ]
    try:
        answer = api.message(content, args, document=True)
    finally:
        try:
            cleanup = api.request("/files/" + file_id, method="DELETE")
            if cleanup.get("deleted") is not True:
                raise APIError("Deletion was not confirmed")
        except (APIError, OSError, ValueError, http.client.HTTPException) as exc:
            detail = str(exc).replace(api.key, "[redacted]")
            print(f"Temporary upload {file_id}: {detail}. One-hour expiry requested.", file=sys.stderr)
            cleanup = {"id": file_id, "deleted": False}
    return {"response": answer, "cleanup": cleanup}


def normalize_wav(raw):
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("DeepSeek did not return a RIFF WAV file")
    wav = bytearray(raw)
    riff_size = struct.unpack_from("<I", wav, 4)[0]
    if riff_size in (0, 0xFFFFFFFF):
        struct.pack_into("<I", wav, 4, len(wav) - 8)
    elif riff_size + 8 != len(wav):
        raise ValueError("WAV length does not match its RIFF header")
    offset = 12
    while offset + 8 <= len(wav):
        kind, size = struct.unpack_from("<4sI", wav, offset)
        available = len(wav) - offset - 8
        if kind == b"data":
            if size in (0, 0xFFFFFFFF):
                size = available
                struct.pack_into("<I", wav, offset + 4, size)
            if not 0 < size <= available:
                raise ValueError("WAV data was empty or incomplete")
            break
        if size > available:
            raise ValueError("WAV chunk was incomplete")
        offset += 8 + size + size % 2
    else:
        raise ValueError("WAV data chunk is missing")
    with wave.open(io.BytesIO(wav), "rb") as audio:
        frame_bytes = audio.getsampwidth() * audio.getnchannels()
        frames = audio.getnframes()
        if not frames or frames * frame_bytes != size:
            raise ValueError("WAV data is not aligned to audio frames")
        duration = frames / audio.getframerate()
    return wav, round(duration, 3)


def require_text(text, limit=None):
    if not text.strip() or (limit is not None and len(text) > limit):
        raise ValueError("Text must be non-empty" + (f" and at most {limit} characters" if limit else ""))
    return text


def public_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Provide a public HTTP(S) URL without credentials")
    return url


def dispatch(api, args):
    action = args.command
    if action == "search":
        return api.request("/v1/tools/search", {"query": require_text(args.query, 128), "count": args.count, "need_content": args.content})
    if action == "fetch":
        return api.request("/v1/tools/fetch", {"url": public_url(args.url)})
    if action == "web":
        question = require_text(args.query)
        return api.message("Use DeepSeek web search and cite sources in the answer.\n\n" + question, args, "deepseek_web_search")
    if action == "read":
        prompt = f"Read this page using the link tool: {public_url(args.url)}\n\n{require_text(args.question)}"
        return api.message(prompt, args, "deepseek_read_url")
    if action == "chat":
        return api.message(args.question, args)
    if action == "document":
        return document_qa(api, args)
    if action == "ocr":
        return api.request("/v1/tools/ocr", binary=file_form(args.file, [("purpose", args.mode)], DOCUMENT_LIMIT))
    if action == "asr":
        return api.request("/v1/tools/asr", binary=file_form(args.file, [], AUDIO_LIMIT))
    if args.output.suffix.lower() != ".wav":
        raise ValueError("TTS output must have a .wav extension")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(f"Output already exists: {args.output}")
    if not args.output.parent.is_dir():
        raise ValueError(f"Create the output directory first: {args.output.parent}")
    speech = require_text(args.text, 10000)
    if len(speech) + len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U000323af]", speech)) > 10000:
        raise ValueError("TTS accepts up to 10,000 billable characters. Han characters count as two.")
    payload = {"text": speech, "voice_id": args.voice, "format": "wav"}
    wav, duration = normalize_wav(api.request("/v1/tools/tts", payload, wav=True))
    with args.output.open("xb") as target:
        target.write(wav)
    return {"file": str(args.output), "duration_seconds": duration, "bytes": len(wav), "voice": args.voice}


def bounded_int(low, high):
    def parse(value):
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"expected an integer between {low} and {high}")
        return number
    return parse


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--timeout", type=bounded_int(1, 600), default=180, help="socket timeout in seconds (default: 180)")
    commands = root.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search", help="structured webpage search")
    search.add_argument("query")
    search.add_argument("--count", type=bounded_int(1, 50), default=5)
    search.add_argument("--content", action="store_true", help="include available page content")
    commands.add_parser("fetch", help="fetch a page as Markdown").add_argument("url")
    web = commands.add_parser("web", help="answer with server-side web search")
    web.add_argument("query")
    read = commands.add_parser("read", help="answer about a specified URL")
    read.add_argument("url")
    read.add_argument("question")
    chat = commands.add_parser("chat", help="ask a question")
    chat.add_argument("question")
    doc = commands.add_parser("document", help="upload a document, ask a question, and clean up")
    doc.add_argument("file", type=Path)
    doc.add_argument("question")
    doc.add_argument("--layout", action="store_true", help="parse document text and figures")
    for command in (web, read, chat, doc):
        command.add_argument("--thinking", action="store_true")
        command.add_argument("--safety-high", action="store_true")
        command.add_argument("--max-tokens", type=bounded_int(1, 32768), default=2048)
    ocr = commands.add_parser("ocr", help="extract text from an image or document")
    ocr.add_argument("file", type=Path)
    ocr.add_argument("--mode", choices=("text_recognition", "rich_layout_recognition"), default="text_recognition")
    tts = commands.add_parser("tts", help="synthesize a WAV file")
    tts.add_argument("text")
    tts.add_argument("--voice", choices=("stella", "tide"), default="stella")
    tts.add_argument("--output", type=Path, required=True)
    commands.add_parser("asr", help="transcribe PCM WAV or Ogg Opus").add_argument("file", type=Path)
    return root


def main():
    root = parser()
    args = root.parse_args()
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        root.exit(2, "Set DEEPSEEK_API_KEY in the environment.\n")
    try:
        result = dispatch(DeepSeek(key, args.timeout), args)
        print(json.dumps(result, ensure_ascii=False, indent=2).replace(key, "[redacted]"))
    except (APIError, OSError, ValueError, http.client.HTTPException, wave.Error, EOFError) as exc:
        detail = str(exc).replace(key, "[redacted]")
        root.exit(1, f"DeepSeek: {detail}\n")


if __name__ == "__main__":
    main()
