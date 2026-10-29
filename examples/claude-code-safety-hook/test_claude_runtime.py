"""Opt-in real Claude CLI test with synthetic local model responses, not a live model.

Set CLAUDE_BINARY to an absolute executable path. No credentials are required:
the model endpoint is a loopback fixture and every hazardous-looking command
targets an inert executable in a temporary project.
"""
from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parent
# Literal expected reasons are independent of the classifier under test.
CASES = (
    ("rm", "rm", ("-rf", "fixture-target"), "rm", "recursive forced removal"),
    ("git", "git", ("push", "--force", "fixture-remote"), "git", "forced git push"),
    ("drop", "psql", ("-c", "DROP TABLE fixture_table;"), "sql-drop", "SQL DROP TABLE"),
    ("truncate", "psql", ("-c", "TRUNCATE TABLE fixture_table;"), "sql-truncate", "SQL TRUNCATE"),
    ("delete", "psql", ("-c", "DELETE FROM fixture_table;"), "sql-delete", "DELETE FROM without an outer WHERE"),
    ("where", "psql", ("-c", "DELETE FROM fixture_table WHERE id=1;"), None, None),
)


class ModelFixture:
    """Implement the streaming messages protocol without saving request bodies."""

    def __init__(self, commands: list[str]):
        self.commands = commands
        self.results: dict[str, dict] = {}
        self.errors: list[str] = []
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                try:
                    if self.path.split("?")[0] != "/v1/messages":
                        self.send_error(404)
                        return
                    size = int(self.headers.get("Content-Length", 0))
                    if not 0 < size < 8 * 1024 * 1024:
                        raise ValueError("invalid request size")
                    request = json.loads(self.rfile.read(size))
                    for message in request.get("messages", []):
                        content = message.get("content", [])
                        for block in content if isinstance(content, list) else []:
                            key = block.get("tool_use_id", "")
                            if block.get("type") == "tool_result" and key.startswith("toolu_fixture_"):
                                # Keep tool outcomes only, never prompts or auth headers.
                                fixture.results[key] = {
                                    "is_error": block.get("is_error", False),
                                    "content": block.get("content", ""),
                                }
                    index = len(fixture.results)
                    if index < len(commands):
                        block = {"type": "tool_use", "id": f"toolu_fixture_{index}", "name": "Bash", "input": {}}
                        delta = {"type": "input_json_delta", "partial_json": json.dumps({"command": commands[index], "description": "Inert local hook regression fixture"})}
                        stop = "tool_use"
                    else:
                        block = {"type": "text", "text": ""}
                        delta = {"type": "text_delta", "text": "Synthetic local fixture complete."}
                        stop = "end_turn"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    self.event("message_start", {"message": {"id": f"msg_fixture_{index}", "type": "message", "role": "assistant", "model": request.get("model"), "content": [], "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 50, "output_tokens": 0}}})
                    self.event("content_block_start", {"index": 0, "content_block": block})
                    self.event("content_block_delta", {"index": 0, "delta": delta})
                    self.event("content_block_stop", {"index": 0})
                    self.event("message_delta", {"delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 10}})
                    self.event("message_stop", {})
                except Exception as exc:
                    fixture.errors.append(type(exc).__name__)
                    self.close_connection = True

            def event(self, name, payload):
                payload["type"] = name
                self.wfile.write(f"event: {name}\ndata: {json.dumps(payload)}\n\n".encode())
                self.wfile.flush()

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


@unittest.skipUnless("CLAUDE_BINARY" in os.environ, "set CLAUDE_BINARY to opt into the real CLI with synthetic model responses")
class ClaudeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = Path(os.environ["CLAUDE_BINARY"])
        if not cls.binary.is_absolute() or not cls.binary.is_file() or not os.access(cls.binary, os.X_OK):
            raise ValueError("CLAUDE_BINARY must be an absolute executable file path")

    def run_cli(self, home, project, commands, install_hook):
        home.mkdir()
        (home / "tmp").mkdir()
        env = dict(os.environ)
        for key in list(env):
            if key.startswith(("ANTHROPIC_", "CLAUDE_")):
                del env[key]
        # Per-child isolation only: the test runner's HOME is never modified.
        env.update({
            "HOME": str(home), "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "TMPDIR": str(home / "tmp"), "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "ANTHROPIC_API_KEY": "sk-ant-local-fixture-not-a-real-key",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1",
            "DISABLE_AUTOUPDATER": "1", "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        })
        if install_hook:
            result = subprocess.run([sys.executable, str(ROOT / "install.py")], cwd=project, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        with ModelFixture(commands) as fixture:
            env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{fixture.server.server_port}"
            argv = [str(self.binary), "-p", "Exercise the synthetic local fixture.",
                    "--model", "claude-sonnet-4-6", "--system-prompt", "You are a synthetic local protocol fixture.",
                    "--tools", "Bash", "--allowedTools", "Bash", "--permission-prompts", "none",
                    "--output-format", "stream-json", "--verbose", "--include-hook-events",
                    "--no-session-persistence", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                    "--setting-sources", "user", "--disable-slash-commands", "--no-chrome"]
            result = subprocess.run(argv, cwd=project, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, (result.stderr + result.stdout)[-2000:])
        self.assertEqual(fixture.errors, [])
        self.assertEqual(set(fixture.results), {f"toolu_fixture_{i}" for i in range(len(commands))}, result.stdout[-2000:])
        events = [json.loads(line) for line in result.stdout.splitlines()]
        responses = [event for event in events if event.get("subtype") == "hook_response" and event.get("hook_event") == "PreToolUse"]
        return [fixture.results[f"toolu_fixture_{i}"] for i in range(len(commands))], responses

    def test_installed_hook_denies_five_patterns_and_preserves_normal_execution(self):
        with tempfile.TemporaryDirectory(prefix="claude-hook-runtime-") as directory:
            root = Path(directory).resolve()
            project = root / "project"
            project.mkdir()
            commands, markers = [], []
            for name, program, args, _, _ in CASES:
                marker = project / f"{name}.marker"
                executable = project / "inert" / name / program
                executable.parent.mkdir(parents=True)
                executable.write_text("#!/bin/sh\nprintf 'executed\\n' > " + shlex.quote(str(marker)) + "\n")
                executable.chmod(0o700)
                commands.append(shlex.join((str(executable), *args)))
                markers.append(marker)
            markers.append(project / "printf.marker")
            commands.append("printf 'executed\\n' > " + shlex.quote(str(markers[-1])))

            # Identical commands/project: prove permissions alone do not deny them.
            control, control_hooks = self.run_cli(root / "control-home", project, commands, False)
            self.assertEqual(control_hooks, [])
            self.assertTrue(all(not result["is_error"] for result in control))
            for marker in markers:
                self.assertEqual(marker.read_text(), "executed\n")
                marker.unlink()

            results, hooks = self.run_cli(root / "hook-home", project, commands, True)
            self.assertEqual([event["exit_code"] for event in hooks], [2, 2, 2, 2, 2, 0, 0])
            for index, (_, _, _, reason, message) in enumerate(CASES):
                with self.subTest(command=commands[index]):
                    self.assertEqual(results[index]["is_error"], reason is not None)
                    self.assertEqual(markers[index].exists(), reason is None)
                    if reason:
                        self.assertIn("PreToolUse:Bash", results[index]["content"])
                        self.assertIn(message, results[index]["content"])
                        self.assertIn(message, hooks[index]["stderr"])
            self.assertFalse(results[-1]["is_error"])
            self.assertEqual(markers[-1].read_text(), "executed\n")
            self.assertEqual(markers[-2].read_text(), "executed\n")

            log = root / "hook-home" / ".claude/hooks/blocked.log"
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(len(records), 5)
            for index, record in enumerate(records):
                self.assertEqual(record["command"], commands[index])
                self.assertEqual(record["project_path"], str(project))
                self.assertEqual(record["reason"], CASES[index][3])
                self.assertRegex(record["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
