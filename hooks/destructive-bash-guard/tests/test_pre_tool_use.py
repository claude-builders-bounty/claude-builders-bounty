import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "pre_tool_use.py"


def run_hook(command):
    payload = {
        "tool_name": "Bash",
        "cwd": "/tmp/project",
        "tool_input": {
            "command": command,
        },
    }
    with tempfile.TemporaryDirectory() as home:
        env = os.environ.copy()
        env["HOME"] = home
        env["USERPROFILE"] = home
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        return result, log_text


class DestructiveBashGuardTest(unittest.TestCase):
    def test_blocks_rm_rf(self):
        result, log_text = run_hook("rm -rf /tmp/demo")
        self.assertEqual(result.returncode, 2)
        self.assertIn("rm -rf /tmp/demo", log_text)

    def test_blocks_drop_table(self):
        result, log_text = run_hook("psql -c 'DROP TABLE users'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DROP TABLE users", log_text)

    def test_blocks_force_push(self):
        result, log_text = run_hook("git push origin main --force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("git push origin main --force", log_text)

    def test_blocks_truncate(self):
        result, log_text = run_hook("psql -c 'TRUNCATE audit_events'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("TRUNCATE audit_events", log_text)

    def test_blocks_delete_without_where(self):
        result, log_text = run_hook("psql -c 'DELETE FROM users'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DELETE FROM users", log_text)

    def test_allows_delete_with_where(self):
        result, log_text = run_hook("psql -c 'DELETE FROM users WHERE id = 1'")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(log_text, "")

    def test_allows_normal_command(self):
        result, log_text = run_hook("ls -la && git status --short")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(log_text, "")


if __name__ == "__main__":
    unittest.main()
