import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_blocker.py"


class PreToolUseBlockerTest(unittest.TestCase):
    def run_hook(self, payload, project_path="C:/work/example"):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            env["CLAUDE_PROJECT_DIR"] = project_path
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_lines = (
                log_path.read_text(encoding="utf-8").splitlines()
                if log_path.exists()
                else []
            )
            return proc, log_lines

    def test_blocks_required_destructive_patterns_and_logs_context(self):
        commands = [
            "rm -rf ./dist",
            "psql -c 'DROP TABLE users'",
            "git push origin main --force",
            "sqlite3 app.db 'TRUNCATE users'",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        for command in commands:
            with self.subTest(command=command):
                proc, log_lines = self.run_hook(
                    {"tool_name": "Bash", "tool_input": {"command": command}},
                    project_path="/repo/app",
                )

                self.assertEqual(proc.returncode, 2)
                self.assertIn("Blocked by Claude Code safety hook", proc.stderr)
                self.assertEqual(len(log_lines), 1)
                log = json.loads(log_lines[0])
                self.assertEqual(log["command"], command)
                self.assertEqual(log["project_path"], "/repo/app")
                self.assertIn("timestamp", log)
                self.assertIn("reason", log)

    def test_allows_normal_commands_and_delete_with_where(self):
        commands = [
            "ls -la",
            "git status --short",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        ]

        for command in commands:
            with self.subTest(command=command):
                proc, log_lines = self.run_hook(
                    {"tool_name": "Bash", "tool_input": {"command": command}}
                )

                self.assertEqual(proc.returncode, 0)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(log_lines, [])

    def test_ignores_non_bash_tools(self):
        proc, log_lines = self.run_hook(
            {"tool_name": "Read", "tool_input": {"command": "rm -rf ./dist"}}
        )

        self.assertEqual(proc.returncode, 0)
        self.assertEqual(log_lines, [])


if __name__ == "__main__":
    unittest.main()
