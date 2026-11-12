#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Claude Code Pre-Tool-Use Destructive Blocker Hook
"""
import unittest
import sys
import os
import tempfile
import json
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from block_destructive import evaluate_command, log_blocked


class TestDestructiveBlocker(unittest.TestCase):

    # 1. rm -rf variations
    def test_blocks_rm_rf(self):
        vectors = [
            "rm -rf /tmp/data",
            "rm -fr build/",
            "rm -r -f node_modules",
            "rm -f -r dist",
            "rm -Rf legacy_data",
            "rm -rfv target/",
            "rm --recursive --force .cache",
            "rm --force --recursive temp",
            "sudo rm -rf /etc/test",
            "rm -r -f -v tmp_dir",
        ]
        for cmd in vectors:
            blocked, reason = evaluate_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be blocked!")
            self.assertIn("rm -rf", reason.lower())

    # 2. DROP TABLE variations
    def test_blocks_drop_table(self):
        vectors = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "psql -c 'DROP TABLE audit_trail'",
            "DROP TABLE \"orders\"",
            "DROP TABLE schema.customers;",
        ]
        for cmd in vectors:
            blocked, reason = evaluate_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be blocked!")
            self.assertIn("drop table", reason.lower())

    # 3. git push --force / -f
    def test_blocks_force_push(self):
        vectors = [
            "git push --force",
            "git push -f",
            "git push origin main --force",
            "git push origin feat/test -f",
            "git push --force-with-lease origin main",
            "git push upstream -f",
        ]
        for cmd in vectors:
            blocked, reason = evaluate_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be blocked!")
            self.assertIn("git push --force", reason.lower())

    # 4. TRUNCATE variations
    def test_blocks_truncate(self):
        vectors = [
            "TRUNCATE users",
            "TRUNCATE TABLE accounts;",
            "truncate table logs",
            "mysql -e 'TRUNCATE TABLE sessions'",
        ]
        for cmd in vectors:
            blocked, reason = evaluate_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be blocked!")
            self.assertIn("truncate", reason.lower())

    # 5. DELETE FROM without WHERE
    def test_blocks_delete_without_where(self):
        vectors = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM orders",
            "psql -c 'DELETE FROM sessions;'",
        ]
        for cmd in vectors:
            blocked, reason = evaluate_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be blocked!")
            self.assertIn("delete from", reason.lower())

    # 6. DELETE FROM with WHERE should be ALLOWED
    def test_allows_delete_with_where(self):
        vectors = [
            "DELETE FROM users WHERE status = 'inactive';",
            "delete from accounts where id = 42;",
            "DELETE FROM orders WHERE created_at < NOW() - INTERVAL '30 days'",
            "psql -c 'DELETE FROM sessions WHERE expired = true;'",
        ]
        for cmd in vectors:
            allowed, reason = evaluate_command(cmd)
            self.assertTrue(allowed, f"Expected '{cmd}' with WHERE clause to be allowed!")

    # 7. Normal/Safe bash commands should be ALLOWED
    def test_allows_normal_bash_commands(self):
        vectors = [
            "ls -la",
            "git status",
            "git push origin main",
            "git push",
            "rm file.txt",
            "rm temp_test.py",
            "pytest -v",
            "python3 -m unittest",
            "npm install",
            "docker ps",
            "SELECT * FROM users WHERE active = true",
            "cat ~/.claude/config.json",
            "echo 'Hello world'",
        ]
        for cmd in vectors:
            allowed, reason = evaluate_command(cmd)
            self.assertTrue(allowed, f"Expected normal command '{cmd}' to be allowed!")

    # 8. Test logging to blocked.log
    def test_logging_behavior(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            log_blocked("rm -rf /tmp/foo", "/test/project", "Test reason", log_path=tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("PROJECT=/test/project", content)
            self.assertIn("REASON=Test reason", content)
            self.assertIn("ATTEMPTED_COMMAND=rm -rf /tmp/foo", content)
            self.assertIn("T", content)  # ISO timestamp
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # 9. CLI & JSON Stdin integration test
    def test_cli_execution_with_json_payload(self):
        script_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "block_destructive.py")
        payload = json.dumps({
            "tool": "Bash",
            "input": {"command": "rm -rf /data"},
            "context": {"project_dir": "/my/project"}
        })

        proc = subprocess.run(
            [sys.executable, script_path],
            input=payload,
            text=True,
            capture_output=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[BLOCKED BY CLAUDE CODE PRE-TOOL-USE HOOK]", proc.stderr)
        self.assertIn("rm -rf /data", proc.stderr)

    def test_cli_execution_safe_json_payload(self):
        script_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "block_destructive.py")
        payload = json.dumps({
            "tool": "Bash",
            "input": {"command": "git status"},
            "context": {"project_dir": "/my/project"}
        })

        proc = subprocess.run(
            [sys.executable, script_path],
            input=payload,
            text=True,
            capture_output=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), "")


if __name__ == "__main__":
    unittest.main()
