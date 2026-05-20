import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "destructive_command_guard.py"

spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
assert spec is not None
assert spec.loader is not None
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_allows_normal_bash_command(self):
        self.assertIsNone(guard.find_block_reason("echo hello && git status"))

    def test_blocks_rm_rf(self):
        block = guard.find_block_reason("rm -rf /tmp/demo")
        self.assertIsNotNone(block)
        self.assertEqual(block[0], "recursive force delete")

    def test_blocks_rm_fr_variant(self):
        block = guard.find_block_reason("rm -fr ./build")
        self.assertIsNotNone(block)
        self.assertEqual(block[0], "recursive force delete")

    def test_blocks_drop_table_case_insensitive(self):
        block = guard.find_block_reason("psql -c 'DROP TABLE users;'")
        self.assertIsNotNone(block)
        self.assertEqual(block[0], "drop table")

    def test_blocks_force_push_forms(self):
        for command in ["git push --force", "git push origin main -f", "git push --force-with-lease"]:
            with self.subTest(command=command):
                block = guard.find_block_reason(command)
                self.assertIsNotNone(block)
                self.assertEqual(block[0], "force push")

    def test_blocks_truncate(self):
        block = guard.find_block_reason("mysql -e 'TRUNCATE users;'")
        self.assertIsNotNone(block)
        self.assertEqual(block[0], "truncate")

    def test_blocks_delete_without_where(self):
        block = guard.find_block_reason("psql -c 'DELETE FROM users;'")
        self.assertIsNotNone(block)
        self.assertEqual(block[0], "delete without where")

    def test_allows_delete_with_where(self):
        self.assertIsNone(guard.find_block_reason("psql -c 'DELETE FROM users WHERE id = 1;'"))

    def test_extracts_command_from_tool_input(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "echo ok"}}
        self.assertEqual(guard.extract_command(payload), "echo ok")

    def test_script_exit_codes(self):
        safe_payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo safe"}})
        blocked_payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/demo"}})

        safe = subprocess.run([sys.executable, str(HOOK)], input=safe_payload, text=True, capture_output=True)
        self.assertEqual(safe.returncode, 0, safe.stderr)

        blocked = subprocess.run([sys.executable, str(HOOK)], input=blocked_payload, text=True, capture_output=True)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("Blocked destructive Bash command", blocked.stderr)


if __name__ == "__main__":
    unittest.main()
