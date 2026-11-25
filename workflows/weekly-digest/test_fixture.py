"""Run the workflow with a real n8n CLI and disposable loopback HTTP and SMTP fixtures."""

import argparse
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socketserver
import subprocess
import tempfile
import threading
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
NOW = datetime.now(timezone.utc)
RECENT = (NOW - timedelta(days=1)).isoformat()
OLD = (NOW - timedelta(days=9)).isoformat()
NARRATIVE = "Fixture narrative: two commits, one closed issue, and one merged pull request."


class FixtureAPI(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, has_next=False):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if has_next:
            self.send_header("Link", '<http://127.0.0.1/fixture?page=2>; rel="next"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        page = int(parse_qs(parsed.query).get("page", ["1"])[0])
        kind = parsed.path.rsplit("/", 1)[-1]
        self.server.hits.append([kind, page])
        if kind == "commits":
            self.reply([{"sha": str(page) * 40, "commit": {"committer": {"date": RECENT},
                        "message": "Fixture commit " + str(page)}}], page == 1)
        elif kind == "issues":
            self.reply([{"number": 5, "closed_at": RECENT, "title": "Closed an issue"},
                        {"number": 7, "closed_at": RECENT, "pull_request": {}, "title": "PR in issues feed"},
                        {"number": 9, "closed_at": OLD, "title": "Closed in previous window"}])
        elif kind == "pulls":
            self.reply([{"number": 7, "updated_at": RECENT, "merged_at": RECENT, "title": "Merge a fix"},
                        {"number": 8, "updated_at": RECENT, "merged_at": None, "title": "Closed unmerged"}])
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/v1/messages":
            self.send_error(404)
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.request_payload = payload
        self.reply({"stop_reason": "end_turn", "content": [{"type": "text", "text": NARRATIVE}]})


class MailCapture(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"220 fixture SMTP ready\r\n")
        while line := self.rfile.readline():
            verb = line.split()[0].upper()
            if verb == b"EHLO":
                self.wfile.write(b"250 localhost\r\n")
            elif verb == b"DATA":
                self.wfile.write(b"354 end with dot\r\n")
                parts = []
                while (chunk := self.rfile.readline()) not in (b".\r\n", b""):
                    parts.append(chunk)
                self.server.messages.append(b"".join(parts))
                self.wfile.write(b"250 captured\r\n")
            elif verb == b"QUIT":
                self.wfile.write(b"221 closing\r\n")
                break
            else:
                self.wfile.write(b"250 OK\r\n")


def run(cli, output, profile=None):
    api = ThreadingHTTPServer(("127.0.0.1", 0), FixtureAPI)
    smtp = socketserver.ThreadingTCPServer(("127.0.0.1", 0), MailCapture)
    api.hits, smtp.messages = [], []
    for server in (api, smtp):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if profile:
            profile.mkdir(parents=True, exist_ok=False)
        with (nullcontext(str(profile)) if profile else tempfile.TemporaryDirectory()) as tmp:
            temp = Path(tmp)
            env = dict(os.environ, N8N_USER_FOLDER=str(temp), N8N_HOST="127.0.0.1",
                       N8N_LISTEN_ADDRESS="127.0.0.1", N8N_DIAGNOSTICS_ENABLED="false",
                       N8N_VERSION_NOTIFICATIONS_ENABLED="false", N8N_PERSONALIZATION_ENABLED="false",
                       N8N_RUNNERS_BROKER_LISTEN_ADDRESS="127.0.0.1",
                       N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS="false", N8N_LOG_LEVEL="warn",
                       EXECUTIONS_DATA_SAVE_ON_SUCCESS="all", EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS="true")
            doc = json.loads((HERE / "weekly-digest.json").read_text(encoding="utf-8"))
            doc["id"] = "WeeklyDigestTest1"
            for node in doc["nodes"]:
                params = node["parameters"]
                if node["name"].startswith("GitHub ") or node["name"] == "Claude narrative":
                    params["url"] = params["url"].replace("https://api.github.com", f"http://127.0.0.1:{api.server_port}").replace(
                        "https://api.anthropic.com", f"http://127.0.0.1:{api.server_port}")
                if node["name"] == "Claude narrative":
                    params.pop("authentication")
                    params.pop("genericAuthType")
                if node["name"] == "Email digest":
                    node["credentials"] = {"smtp": {"id":"WeeklyFixtureSMTP","name":"Loopback SMTP fixture"}}
            cred = [{"id":"WeeklyFixtureSMTP","name":"Loopback SMTP fixture","type":"smtp",
                     "data":{"host":"127.0.0.1","port":smtp.server_address[1],"secure":False,
                             "disableStartTls":True, "user":"","password":""}}]
            (temp / "workflow.json").write_text(json.dumps(doc), encoding="utf-8")
            (temp / "credentials.json").write_text(json.dumps(cred), encoding="utf-8")

            def invoke(*args):
                result = subprocess.run([*cli, *args], cwd=temp, env=env, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", timeout=240)
                if result.returncode:
                    raise RuntimeError(result.stdout[-6000:])
                return result.stdout

            invoke("import:credentials", "--input=" + str(temp / "credentials.json"))
            invoke("import:workflow", "--input=" + str(temp / "workflow.json"))
            log = invoke("execute", "--id=WeeklyDigestTest1", "--rawOutput")
            counts = json.loads(api.request_payload["messages"][0]["content"])["counts"]
            assert counts == {"commits": 2, "closedIssues": 1, "mergedPRs": 1}, counts
            assert api.request_payload["model"] == "claude-sonnet-4-6"
            assert ["commits", 2] in api.hits, api.hits
            assert len(smtp.messages) == 1
            delivered = BytesParser(policy=policy.default).parsebytes(smtp.messages[0])
            assert NARRATIVE in delivered.get_content()
            assert str(delivered["To"]) == "team@example.invalid"
            report = {"result": "passed","n8n_version":invoke("--version").strip(),
                      "finished_utc":datetime.now(timezone.utc).isoformat(),"counts":counts,
                      "github_fixture_requests":api.hits,"fixture_emails":len(smtp.messages),
                      "live_claude_requests":0,"real_emails_sent":0}
            if output:
                output.mkdir(parents=True, exist_ok=True)
                (output / "execution.txt").write_text(log,encoding="utf-8")
                (output / "receipt.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            print(json.dumps(report, indent=2))
    finally:
        for server in (api, smtp):
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n8n", default="n8n", help="n8n executable or the path to its JS entry point")
    parser.add_argument("--node", help="Node executable when passing an n8n JS entry point")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--keep-profile", type=Path, help="Use a new directory and keep the isolated n8n history for inspection")
    opts = parser.parse_args()
    run(([opts.node] if opts.node else []) + [opts.n8n], opts.output, opts.keep_profile)
