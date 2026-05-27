import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))

import block_destructive_bash


class BlockDestructiveBashTest(unittest.TestCase):
    def run_hook(self, payload, home):
        old_stdin = sys.stdin
        old_home = os.environ.get("HOME")
        sys.stdin = io.StringIO(json.dumps(payload))
        os.environ["HOME"] = str(home)
        try:
            with redirect_stdout(io.StringIO()) as stdout:
                exit_code = block_destructive_bash.main()
            return exit_code, stdout.getvalue()
        finally:
            sys.stdin = old_stdin
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home

    def test_blocks_required_patterns(self):
        blocked_commands = [
            "rm -rf build",
            "rm -fr build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "sqlite3 app.db 'TRUNCATE sessions'",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            for command in blocked_commands:
                exit_code, output = self.run_hook(
                    {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/repo"},
                    home,
                )
                self.assertEqual(exit_code, 0)
                response = json.loads(output)
                hook_output = response["hookSpecificOutput"]
                self.assertEqual(hook_output["permissionDecision"], "deny")
                self.assertIn("Blocked dangerous Bash command", hook_output["permissionDecisionReason"])

            log_lines = (home / ".claude" / "hooks" / "blocked.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(log_lines), len(blocked_commands))
            self.assertEqual(json.loads(log_lines[0])["project_path"], "/repo")

    def test_allows_safe_bash_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, output = self.run_hook(
                {"tool_name": "Bash", "tool_input": {"command": "npm test && git status"}, "cwd": "/repo"},
                Path(temp_dir),
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(output, "")

    def test_allows_delete_with_where(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, output = self.run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "sqlite3 app.db 'DELETE FROM users WHERE id = 1'"},
                    "cwd": "/repo",
                },
                Path(temp_dir),
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
