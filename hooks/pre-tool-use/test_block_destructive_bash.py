import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).with_name("block-destructive-bash.py")


def load_hook():
    spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BlockDestructiveBashTests(unittest.TestCase):
    def setUp(self):
        self.hook = load_hook()

    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf dist",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "sqlite3 app.db 'TRUNCATE audit_log'",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(self.hook.find_block_reason(command))

    def test_allows_normal_commands_and_delete_with_where(self):
        allowed = [
            "ls -la",
            "rm -r build",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
            "npm test",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(self.hook.find_block_reason(command))

    def test_cli_logs_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {"tool_input": {"command": "rm -rf cache", "cwd": "/tmp/project"}}
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home, "USERPROFILE": home},
            )

            self.assertEqual(result.returncode, 1)
            response = json.loads(result.stdout)
            self.assertEqual(response["decision"], "block")
            self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], "rm -rf cache")
            self.assertEqual(log_entry["project_path"], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
