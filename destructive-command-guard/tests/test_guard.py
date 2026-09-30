import unittest
import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pre_tool_use_guard import check_command, log_blocked

class TestDestructiveCommandGuard(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test_blocked.log")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_rm_rf_blocked(self):
        cases = [
            "rm -rf /tmp/test",
            "rm -r -f node_modules",
            "rm -fr build",
            "rm --recursive --force cache",
            "bash -c 'rm -rf /var/log'"
        ]
        for cmd in cases:
            blocked, rule, _ = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked")
            self.assertEqual(rule, "Recursive forced deletion")

    def test_git_push_force_blocked(self):
        cases = [
            "git push --force",
            "git push origin main --force",
            "git push origin -f",
            "git push -f upstream branch",
            "git push --force-with-lease"
        ]
        for cmd in cases:
            blocked, rule, _ = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked")
            self.assertEqual(rule, "Git force push")

    def test_sql_drop_table_blocked(self):
        cases = [
            "DROP TABLE users;",
            "drop table if exists orders",
            "sqlite3 test.db 'DROP TABLE migrations;'"
        ]
        for cmd in cases:
            blocked, rule, _ = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked")
            self.assertEqual(rule, "SQL DROP TABLE")

    def test_sql_truncate_blocked(self):
        cases = [
            "TRUNCATE TABLE users;",
            "truncate table logs",
            "TRUNCATE sessions"
        ]
        for cmd in cases:
            blocked, rule, _ = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked")
            self.assertEqual(rule, "SQL TRUNCATE")

    def test_sql_delete_without_where_blocked(self):
        cases = [
            "DELETE FROM users;",
            "delete from accounts",
            "psql -c 'DELETE FROM payments'"
        ]
        for cmd in cases:
            blocked, rule, _ = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked")
            self.assertEqual(rule, "SQL DELETE without WHERE clause")

    def test_safe_commands_allowed(self):
        safe_commands = [
            "ls -la",
            "git status",
            "git push origin feature-branch",
            "npm run build",
            "pytest tests/",
            "python main.py",
            "cat README.md",
            "echo 'rm -rf text inside harmless string'",
            "DELETE FROM users WHERE id = 123;",
            "delete from orders where status = 'cancelled';"
        ]
        for cmd in safe_commands:
            blocked, _, _ = check_command(cmd)
            self.assertFalse(blocked, f"Expected safe command '{cmd}' to pass without being blocked")

    def test_audit_logging(self):
        cmd = "rm -rf test_dir"
        proj = "/workspace/my-app"
        log_blocked(cmd, proj, "Recursive forced deletion", "Test reason", log_file=self.log_file)

        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["blocked_command"], cmd)
            self.assertEqual(entry["project_path"], proj)
            self.assertIn("timestamp", entry)
            self.assertEqual(entry["rule"], "Recursive forced deletion")

if __name__ == "__main__":
    unittest.main()
