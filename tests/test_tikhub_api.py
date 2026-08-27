#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "skills" / "tikhub-search" / "scripts" / "tikhub_api.py"


class Handler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self):
        Handler.attempts += 1
        if Handler.attempts == 1:
            self.send_response(500)
            payload = {"code": 500, "message": "temporary"}
        else:
            self.send_response(200)
            payload = {
                "code": 200,
                "request_id": "req-test",
                "data": {
                    "ok": True,
                    "authorization": self.headers.get("Authorization"),
                },
            }
        body = json.dumps(payload).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class ClientTests(unittest.TestCase):
    def test_dry_run_does_not_require_key(self):
        result = subprocess.run(
            [sys.executable, str(CLIENT), "GET", "/api/v1/test", "--query", "q=hello"],
            text=True,
            capture_output=True,
            check=False,
            env={key: value for key, value in os.environ.items() if key != "TIKHUB_API_KEY"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"mode": "dry-run"', result.stdout)
        self.assertIn("q=hello", result.stdout)

    def test_retry_and_secret_free_envelope(self):
        Handler.attempts = 0
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "response.json"
                base = f"http://127.0.0.1:{server.server_port}"
                environment = os.environ.copy()
                environment["TIKHUB_API_KEY"] = "redact-me"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLIENT),
                        "--execute",
                        "--allow-custom-base",
                        "--base-url",
                        base,
                        "--output",
                        str(output),
                        "--retries",
                        "1",
                        "--timeout",
                        "2",
                        "GET",
                        "/api/v1/test",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                saved = output.read_text(encoding="utf-8")
                self.assertNotIn("redact-me", saved)
                payload = json.loads(saved)
                self.assertEqual(payload["_meta"]["attempts"], 2)
                self.assertEqual(payload["response"]["request_id"], "req-test")
                self.assertEqual(
                    payload["response"]["data"]["authorization"], "<redacted>"
                )
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
