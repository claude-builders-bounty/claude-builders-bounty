from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class MockHandler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        if self.path == "/v1/messages":
            self._json({
                "id": "msg_mock_weekly_summary",
                "type": "message",
                "role": "assistant",
                "model": "claude-sonnet-4-20250514",
                "content": [{
                    "type": "text",
                    "text": "Highlights: mock n8n execution collected GitHub activity and generated a weekly summary successfully."
                }],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 42, "output_tokens": 24}
            })
            return
        if self.path == "/webhook":
            self._json({"ok": True, "received": len(body)})
            return
        self._json({"error": "not found", "path": self.path}, status=404)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args), flush=True)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), MockHandler)
    print("mock endpoints listening on http://127.0.0.1:8765", flush=True)
    server.serve_forever()
