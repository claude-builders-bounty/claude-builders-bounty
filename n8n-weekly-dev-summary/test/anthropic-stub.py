#!/usr/bin/env python3
"""Minimal Anthropic-compatible /v1/messages stub, for testing the workflow offline.

The workflow only needs three things from the API: a 200 response, the
`content[0].text` field, and `usage`. This stub provides exactly that shape so the
n8n plumbing (auth headers, JSON body, retries, delivery) can be exercised without
an API key or a model call. It also accepts any POST to /webhook and returns 204,
so the Discord node can be tested with a local sink.

    python3 test/anthropic-stub.py --port 8799

Then in the workflow's Config node set `anthropicBaseUrl` to http://127.0.0.1:8799
and `discordWebhookUrl` to http://127.0.0.1:8799/webhook.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# A realistic answer in the shape the real model produces. It is fixed on purpose:
# the stub verifies the pipeline, not the model's writing.
SUMMARY = """Development this week was dominated by stabilising the execution engine and tightening the editor experience. The team merged 42 pull requests, with the largest share going to node execution reliability and the new credential handling path.

**Highlights**
- Execution engine: retries and cancellation were reworked so a stopped workflow no longer leaves orphaned child executions (#14281, #14296).
- Editor: the node panel now keeps its scroll position between node switches (#14302).
- Credentials: OAuth token refresh failures surface as an actionable error instead of a generic 401 (#14310).
- Closed 18 issues, including three long-standing reports about webhook timeouts.

**Worth watching**
- Two PRs touch the queue serialisation format; review the migration path before the next release.
- The webhook test suite is still the slowest job in CI (14 min)."""


def console_safe(text: str) -> str:
    """Return text that can always be printed, whatever the console code page is.

    Windows consoles often run on cp1251 or cp437; a single arrow or smart quote in a
    Discord payload used to raise UnicodeEncodeError inside the request handler, so the
    client saw a "socket hang up" instead of a 204. Backslash-escaping keeps the log
    readable.
    """
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, "backslashreplace").decode(encoding, "replace")


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 keeps the socket alive between calls; without it Node's HTTP client
    # can race the server closing the connection and report a spurious "socket hang up".
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        if self.path.startswith("/webhook"):
            # Stand-in for a Discord/Slack incoming webhook: accept, log, return 204.
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {"_raw": raw.decode("utf-8", "replace")}
            print("DELIVERED " + console_safe(json.dumps(payload, ensure_ascii=False))[:400], flush=True)
            self.send_response(204)
            # 204 must not carry a body, but an explicit zero length keeps HTTP/1.1
            # clients from waiting for one.
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return

        missing = [h for h in ("x-api-key", "anthropic-version") if not self.headers.get(h)]
        if missing:
            self.reply(400, {"type": "error", "error": {"type": "invalid_request_error", "message": f"missing headers: {missing}"}})
            return

        model = payload.get("model")
        if not model:
            self.reply(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "model is required"}})
            return

        self.reply(
            200,
            {
                "id": "msg_stub_0001",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [{"type": "text", "text": SUMMARY}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1420, "output_tokens": 190},
            },
        )

    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8799)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Anthropic stub listening on http://127.0.0.1:{args.port}/v1/messages", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
