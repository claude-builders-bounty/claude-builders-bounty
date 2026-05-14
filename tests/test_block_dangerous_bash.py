from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "block_dangerous_bash.py"


def run_hook(
    command: str, *, tool_name: str = "Bash", home: str | None = None
) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = {**os.environ, "HOME": home or tempfile.mkdtemp()}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


class DangerousBashHookTest(unittest.TestCase):
    def assert_denied(self, command: str, reason_fragment: str) -> None:
        result = run_hook(command)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(reason_fragment, output["permissionDecisionReason"])

    def test_blocks_rm_rf(self) -> None:
        self.assert_denied("rm -rf build", "recursive and force")

    def test_logs_blocked_attempt(self) -> None:
        home = tempfile.mkdtemp()
        result = run_hook("rm -rf build", home=home)
        self.assertEqual(result.returncode, 0)

        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["attempted_command"], "rm -rf build")
        self.assertEqual(entry["project_path"], "/tmp/example-project")

    def test_blocks_drop_table(self) -> None:
        self.assert_denied("sqlite3 app.db 'DROP TABLE users;'", "DROP TABLE")

    def test_blocks_truncate(self) -> None:
        self.assert_denied('psql -c "TRUNCATE TABLE audit_events;"', "TRUNCATE")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_denied('sqlite3 app.db "DELETE FROM sessions;"', "DELETE FROM")

    def test_allows_delete_with_where(self) -> None:
        result = run_hook('sqlite3 app.db "DELETE FROM sessions WHERE expires_at < datetime();"')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_force_push(self) -> None:
        self.assert_denied("git push origin main --force", "rewrite remote")

    def test_allows_normal_commands(self) -> None:
        for command in ["ls -la", "git push origin main", "python3 -m pytest", "rm -r build"]:
            result = run_hook(command)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_ignores_other_tools(self) -> None:
        result = run_hook("rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
