import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast

SCRIPT = Path(__file__).with_name("destructive-command-guard.py")
spec = importlib.util.spec_from_file_location("guard", SCRIPT)
assert spec is not None
assert spec.loader is not None
guard = cast(Any, importlib.util.module_from_spec(spec))
spec.loader.exec_module(guard)


class DestructiveCommandGuardTest(unittest.TestCase):
    def test_blocks_required_patterns(self):
        commands = [
            "rm -rf build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_allows_normal_commands_and_safe_delete(self):
        commands = [
            "git status",
            "rm -r build",
            "git push origin main",
            "git push origin feature/fix-login",
            "SELECT * FROM users",
            "DELETE FROM users WHERE id = 1",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_extracts_command_from_common_hook_payloads(self):
        payloads = [
            {"tool_input": {"command": "git status"}},
            {"toolUse": {"input": {"command": "rm -rf /tmp/x"}}},
            {"parameters": {"cmd": "TRUNCATE logs"}},
        ]
        self.assertEqual(
            [guard.find_command(payload) for payload in payloads],
            ["git status", "rm -rf /tmp/x", "TRUNCATE logs"],
        )

    def test_log_block_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            old_log_path = guard.LOG_PATH
            guard.LOG_PATH = Path(directory) / "blocked.log"
            try:
                guard.log_block("rm -rf build", "/repo", "danger")
                entry = json.loads(guard.LOG_PATH.read_text().strip())
            finally:
                guard.LOG_PATH = old_log_path
        self.assertEqual(entry["attempted_command"], "rm -rf build")
        self.assertEqual(entry["project_path"], "/repo")
        self.assertEqual(entry["reason"], "danger")
        self.assertIn("timestamp", entry)


if __name__ == "__main__":
    unittest.main()
