import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hooks import block_destructive_bash as hook


class BlockDestructiveBashTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked_commands = [
            "rm -rf /tmp/example",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users",
        ]

        for command in blocked_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.blocked_reason(command))

    def test_allows_normal_commands(self):
        allowed_commands = [
            "ls -la",
            "git push origin feature/example",
            "DELETE FROM users WHERE id = 1",
            "python -m unittest discover tests",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.blocked_reason(command))

    def test_extracts_command_from_claude_payload(self):
        payload = {"tool_input": {"command": "rm -rf build"}}
        self.assertEqual(hook.extract_command(payload), "rm -rf build")

    def test_logs_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            hook.log_blocked_attempt("rm -rf build", "/project", log_path)
            entry = log_path.read_text(encoding="utf-8")

        self.assertIn("/project", entry)
        self.assertIn("rm -rf build", entry)

    def test_hook_exits_nonzero_for_blocked_command(self):
        script = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"
        payload = {"tool_input": {"command": "git push --force origin main"}, "cwd": "/repo"}

        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                ["python3", str(script)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )
            log_file = Path(home) / ".claude" / "hooks" / "blocked.log"

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Blocked destructive bash command", result.stderr)
            self.assertTrue(log_file.exists())


if __name__ == "__main__":
    unittest.main()
