"""Tests for the block-destructive pre-tool-use hook (stdlib only)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE.parent / "block_destructive.py"
spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

BLOCK = [
    "rm -rf /",
    "rm -fr ./build",
    "sudo rm -rf node_modules",
    "mysql -e 'DROP TABLE users'",
    "psql -c 'TRUNCATE TABLE orders'",
    "sqlite3 app.db 'DELETE FROM customers'",
    "git push --force origin main",
    "git push -f",
    "mkfs.ext4 /dev/sda1",
    "dd if=/dev/zero of=/dev/sda bs=1M",
    ":(){ :|:& };:",
    "chmod -R 777 /var/www",
]
ALLOW = [
    "ls -la",
    "npm run build",
    "git push origin main",
    "git push --force-with-lease origin main",
    "rm build/output.txt",
    "DELETE FROM customers WHERE id = 3",
    "grep -r TODO src/",
    "python manage.py migrate",
]


class TestRules(unittest.TestCase):
    def test_blocks(self):
        for c in BLOCK:
            self.assertIsNotNone(hook.find_reason(c), f"should block: {c}")

    def test_allows(self):
        for c in ALLOW:
            self.assertIsNone(hook.find_reason(c), f"should allow: {c}")


class TestProcess(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                              text=True, capture_output=True)

    def test_blocked_exit_code_and_message(self):
        r = self._run({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "/tmp/x"})
        self.assertEqual(r.returncode, 2)
        self.assertIn("BLOCKED", r.stderr)

    def test_allowed_exit_code(self):
        r = self._run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        self.assertEqual(r.returncode, 0)

    def test_non_bash_ignored(self):
        r = self._run({"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}})
        self.assertEqual(r.returncode, 0)

    def test_malformed_payload_does_not_crash(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json",
                           text=True, capture_output=True)
        self.assertEqual(r.returncode, 0)

    def test_logs_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "blocked.log"
            hook.LOG = log
            hook.log_block("rm -rf", "rm -rf /", "/tmp/proj")
            body = log.read_text()
            self.assertIn("/tmp/proj", body)
            self.assertIn("rm -rf /", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
