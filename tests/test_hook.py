from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block-destructive.py"


def run_hook(command: str, cwd: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": cwd,
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["CLAUDE_HOOK_LOG"] = str(log_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class HookTests(unittest.TestCase):
    def test_blocks_required_patterns_and_logs_fields(self) -> None:
        blocked = [
            "rm -rf ./build",
            "psql app -c 'DROP TABLE accounts'",
            "git push origin main --force",
            "sqlite3 app.db 'TRUNCATE TABLE events'",
            "sqlite3 app.db 'DELETE FROM events;'",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            for command in blocked:
                result = run_hook(command, tmp, log_path)
                self.assertEqual(result.returncode, 2, command)
                self.assertIn("BLOCKED", result.stderr)
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), len(blocked))
            self.assertTrue({"timestamp", "attempted_command", "project_path"} <= records[0].keys())

    def test_allows_safe_and_scoped_delete(self) -> None:
        safe = [
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM events WHERE id = 1;'",
            "printf hello",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for command in safe:
                result = run_hook(command, tmp, Path(tmp) / "blocked.log")
                self.assertEqual(result.returncode, 0, command)

    def test_allows_non_bash_and_malformed_input(self) -> None:
        env = os.environ.copy()
        with tempfile.TemporaryDirectory() as tmp:
            env["CLAUDE_HOOK_LOG"] = str(Path(tmp) / "blocked.log")
            payloads = [
                "",
                "not json",
                json.dumps({"tool_name": "Read", "tool_input": {"command": "rm -rf /"}}),
            ]
            for payload in payloads:
                result = subprocess.run(
                    [sys.executable, str(HOOK)],
                    input=payload,
                    text=True,
                    capture_output=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, payload)


if __name__ == "__main__":
    unittest.main()
