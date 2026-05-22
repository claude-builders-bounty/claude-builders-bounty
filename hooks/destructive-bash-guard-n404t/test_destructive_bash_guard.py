import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import destructive_bash_guard as guard


def run_hook(command: str) -> tuple[int, str, str]:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    stdin = io.StringIO(json.dumps(payload))
    stderr = io.StringIO()
    with tempfile.TemporaryDirectory() as home:
        with patch.dict(os.environ, {"HOME": home}), patch("sys.stdin", stdin), redirect_stderr(stderr):
            guard.LOG_PATH = Path(home) / ".claude" / "hooks" / "blocked.log"
            code = guard.main()
            log = guard.LOG_PATH.read_text() if guard.LOG_PATH.exists() else ""
    return code, stderr.getvalue(), log


class DestructiveBashGuardTest(unittest.TestCase):
    def test_safe_command_passes(self):
        code, err, log = run_hook("python -m pytest")
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(log, "")

    def test_blocks_rm_rf(self):
        code, err, log = run_hook("rm -rf dist")
        self.assertEqual(code, 2)
        self.assertIn("rm -rf", err)
        self.assertIn("rm -rf dist", log)

    def test_blocks_drop_table(self):
        code, _, log = run_hook("psql -c 'DROP TABLE users;'")
        self.assertEqual(code, 2)
        self.assertIn("DROP TABLE", log)

    def test_blocks_force_push(self):
        code, _, log = run_hook("git push --force origin main")
        self.assertEqual(code, 2)
        self.assertIn("git push --force", log)

    def test_blocks_truncate(self):
        code, _, log = run_hook("psql -c 'TRUNCATE audit_log;'")
        self.assertEqual(code, 2)
        self.assertIn("TRUNCATE", log)

    def test_blocks_delete_without_where(self):
        code, _, log = run_hook("psql -c 'DELETE FROM users;'")
        self.assertEqual(code, 2)
        self.assertIn("DELETE FROM", log)

    def test_allows_delete_with_where(self):
        code, err, log = run_hook("psql -c 'DELETE FROM users WHERE id = 1;'")
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
