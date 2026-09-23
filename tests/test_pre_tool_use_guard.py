import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_guard.py"

spec = importlib.util.spec_from_file_location("pre_tool_use_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PreToolUseGuardTests(unittest.TestCase):
    def run_hook(self, command):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)
            payload = {"tool_name": "Bash", "tool_input": {"command": command}}
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                cwd=ROOT,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_path.read_text() if log_path.exists() else ""
            return result, log_text

    def test_blocks_required_patterns(self):
        cases = [
            "rm -rf build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users",
        ]
        for command in cases:
            with self.subTest(command=command):
                result, log_text = self.run_hook(command)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Blocked dangerous bash command", result.stderr)
                self.assertIn(command.replace("\n", "\\n"), log_text)

    def test_allows_delete_from_with_where(self):
        result, log_text = self.run_hook("DELETE FROM users WHERE id = 1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(log_text, "")

    def test_allows_normal_commands(self):
        for command in ["ls -la", "git status --short", "python -m unittest"]:
            with self.subTest(command=command):
                result, log_text = self.run_hook(command)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(log_text, "")

    def test_extracts_top_level_command_shape(self):
        self.assertEqual(guard.extract_command({"command": "ls"}), "ls")


if __name__ == "__main__":
    unittest.main()
