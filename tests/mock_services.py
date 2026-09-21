#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG = Path('/tmp/b5-mock-requests.jsonl')

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers.get('content-length', '0'))
        body = self.rfile.read(size)
        with LOG.open('ab') as f:
            f.write(json.dumps({'path': self.path, 'body': body.decode('utf-8')}).encode() + b'\n')
        if self.path == '/v1/messages':
            payload = {'id':'msg_test','type':'message','role':'assistant','content':[{'type':'text','text':'## Weekly Development Summary\n\nNo activity was invented. Runtime integration succeeded.'}], 'model':'claude-sonnet-4-20250514','stop_reason':'end_turn'}
        elif self.path == '/discord':
            payload = {'delivered': True}
        else:
            self.send_error(404); return
        data = json.dumps(payload).encode()
        self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, fmt, *args):
        pass

if __name__ == '__main__':
    LOG.unlink(missing_ok=True)
    ThreadingHTTPServer(('127.0.0.1', 18080), Handler).serve_forever()
