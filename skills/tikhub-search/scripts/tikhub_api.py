#!/usr/bin/env python3
"""Guarded TikHub REST client with dry-run, retries, and auditable output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OFFICIAL_HOSTS = {"api.tikhub.io", "api.tikhub.dev"}
TRANSIENT_STATUS = {429, 500, 502, 503, 504}
SECRET_KEYS = {"authorization", "api_key", "apikey", "token", "access_token"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call a TikHub REST endpoint. Defaults to a no-cost dry run."
    )
    parser.add_argument("--execute", action="store_true", help="Perform the request")
    parser.add_argument("--output", type=Path, help="Required JSON output path when executing")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("TIKHUB_API_BASE_URL", "https://api.tikhub.io"),
        help="TikHub API base URL (default: TIKHUB_API_BASE_URL or api.tikhub.io)",
    )
    parser.add_argument(
        "--allow-custom-base",
        action="store_true",
        help="Allow a non-TikHub base URL; intended for local testing only",
    )
    parser.add_argument(
        "--api-key-env",
        default="TIKHUB_API_KEY",
        help="Environment variable containing the Bearer token",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Query parameter; repeat as needed",
    )
    body = parser.add_mutually_exclusive_group()
    body.add_argument("--data", help="Inline JSON request body")
    body.add_argument("--data-file", type=Path, help="JSON request body file")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument(
        "--retries",
        type=int,
        choices=range(0, 4),
        default=3,
        metavar="0..3",
        help="Retries after the first transient failure (default: 3)",
    )
    parser.add_argument("method", choices=("GET", "POST"))
    parser.add_argument("path", help="Endpoint path beginning with /api/")
    return parser.parse_args()


def parse_query(values: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in values:
        if "=" not in item:
            raise ValueError(f"query parameter must be KEY=VALUE: {item!r}")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError("query parameter key cannot be empty")
        if key.lower() in SECRET_KEYS:
            raise ValueError(
                f"secret-like query parameter {key!r} is not allowed; use Bearer authentication"
            )
        pairs.append((key, value))
    return pairs


def load_body(args: argparse.Namespace) -> Any | None:
    if args.data is not None:
        return json.loads(args.data)
    if args.data_file is not None:
        with args.data_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return None


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in SECRET_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def redact_exact_secret(value: Any, secret: str) -> Any:
    if isinstance(value, dict):
        return {key: redact_exact_secret(item, secret) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_exact_secret(item, secret) for item in value]
    if isinstance(value, str) and secret:
        return value.replace(secret, "<redacted>")
    return value


def build_url(base_url: str, path: str, query: list[tuple[str, str]]) -> str:
    if not path.startswith("/api/"):
        raise ValueError("path must begin with /api/")
    if "#" in path:
        raise ValueError("path fragments are not allowed")
    base = base_url.rstrip("/") + "/"
    url = urllib.parse.urljoin(base, path.lstrip("/"))
    split = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(split.query, keep_blank_values=True)
    encoded = urllib.parse.urlencode(existing + query)
    return urllib.parse.urlunsplit((split.scheme, split.netloc, split.path, encoded, ""))


def validate_base(base_url: str, allow_custom: bool) -> None:
    split = urllib.parse.urlsplit(base_url)
    if allow_custom:
        if split.scheme not in {"http", "https"} or not split.hostname:
            raise ValueError("custom base URL must be a valid HTTP(S) URL")
        return
    if split.scheme != "https" or split.hostname not in OFFICIAL_HOSTS:
        raise ValueError(
            "base URL must be https://api.tikhub.io or https://api.tikhub.dev; "
            "use --allow-custom-base only for a trusted test server"
        )


def decode_response(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_non_json_body": text}


def write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def request_once(
    method: str,
    url: str,
    api_key: str,
    body_bytes: bytes | None,
    timeout: float,
) -> tuple[int, dict[str, str], bytes]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "tikhub-search-skill/0.2.1",
    }
    if body_bytes is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def main() -> int:
    args = parse_args()
    try:
        validate_base(args.base_url, args.allow_custom_base)
        query = parse_query(args.query)
        body = load_body(args)
        if args.method == "GET" and body is not None:
            raise ValueError("GET requests cannot include a JSON body")
        url = build_url(args.base_url, args.path, query)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    safe_preview = {
        "mode": "execute" if args.execute else "dry-run",
        "method": args.method,
        "url": url,
        "body": redact(body),
        "timeout_seconds": args.timeout,
        "max_retries": args.retries,
    }
    if not args.execute:
        print(json.dumps(safe_preview, ensure_ascii=False, indent=2))
        print("Dry run only. Add --execute and --output to perform this request.")
        return 0

    if args.output is None:
        print("error: --output is required with --execute", file=sys.stderr)
        return 2
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        print(f"error: environment variable {args.api_key_env} is empty", file=sys.stderr)
        return 2

    body_bytes = None
    if body is not None:
        body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()

    started = datetime.now(timezone.utc)
    attempts = 0
    status = 0
    response_headers: dict[str, str] = {}
    raw = b""
    last_error: str | None = None

    for attempt in range(args.retries + 1):
        attempts = attempt + 1
        try:
            status, response_headers, raw = request_once(
                args.method, url, api_key, body_bytes, args.timeout
            )
            if status not in TRANSIENT_STATUS or attempt == args.retries:
                break
            last_error = f"HTTP {status}"
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = str(error)
            if attempt == args.retries:
                break
        delay = min(8.0, 2**attempt) + random.uniform(0.0, 0.4)
        print(
            f"Transient failure ({last_error}); retrying in {delay:.1f}s "
            f"[{attempt + 1}/{args.retries}]",
            file=sys.stderr,
        )
        time.sleep(delay)

    finished = datetime.now(timezone.utc)
    response = decode_response(raw) if raw else {"_transport_error": last_error}
    response = redact_exact_secret(redact(response), api_key)
    api_code = response.get("code") if isinstance(response, dict) else None
    success = 200 <= status < 300 and (api_code is None or api_code == 200)
    request_record = {
        "query": redact(dict(query)),
        "body": redact(body),
        "body_sha256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
    }
    envelope = {
        "_meta": {
            "client": "tikhub-search-skill/0.2.1",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "method": args.method,
            "url": url,
            "http_status": status,
            "attempts": attempts,
            "request": request_record,
            "response_content_type": response_headers.get("Content-Type"),
            "success": success,
        },
        "response": response,
    }
    write_atomic(args.output, envelope)

    request_id = response.get("request_id") if isinstance(response, dict) else None
    message = response.get("message") if isinstance(response, dict) else None
    print(
        json.dumps(
            {
                "output": str(args.output),
                "http_status": status,
                "api_code": api_code,
                "request_id": request_id,
                "message": message,
                "attempts": attempts,
                "success": success,
            },
            ensure_ascii=False,
        )
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
