from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "block-destructive-bash.py"


class HookTests(unittest.TestCase):
    def run_hook(self, command: str, home: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        env = os.environ.copy()
        if home is not None:
            env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def assert_blocked(self, command: str, expected_reason: str) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            result = self.run_hook(command, home=pathlib.Path(home_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn(expected_reason, output["permissionDecisionReason"])

    def test_blocks_required_patterns(self) -> None:
        cases = [
            ("rm -rf build", "rm -rf"),
            ("rm -r -f build", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "git push --force"),
            ("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE"),
            ("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM without a WHERE"),
        ]
        for command, reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, reason)

    def test_allows_normal_bash_commands(self) -> None:
        safe_commands = [
            "npm test",
            "rm build/output.txt",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
            "grep -R TODO src",
        ]
        for command in safe_commands:
            with self.subTest(command=command):
                result = self.run_hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_logs_blocked_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home = pathlib.Path(home_dir)
            result = self.run_hook("rm -rf dist", home=home)
            self.assertEqual(result.returncode, 0, result.stderr)

            log_path = home / ".claude" / "hooks" / "blocked.log"
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["command"], "rm -rf dist")
            self.assertEqual(records[0]["project_path"], "/tmp/example-project")
            self.assertIn("timestamp", records[0])

    def test_install_writes_claude_settings_hook(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home = pathlib.Path(home_dir)
            env = os.environ.copy()
            env["HOME"] = str(home)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--install"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            settings = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
            hook_group = settings["hooks"]["PreToolUse"][0]
            self.assertEqual(hook_group["matcher"], "Bash")
            self.assertEqual(hook_group["hooks"][0]["type"], "command")
            self.assertTrue(hook_group["hooks"][0]["command"].endswith("block-destructive-bash.py"))


if __name__ == "__main__":
    unittest.main()
