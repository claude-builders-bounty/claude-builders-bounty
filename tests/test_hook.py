import unittest
import os
import sys
import tempfile
import json
from datetime import datetime

# Import evaluate_command from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from pre_tool_use_safety import evaluate_command

class TestClaudeSafetyHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_blocked.log")

    def test_blocks_rm_rf(self):
        cmds = [
            "rm -rf /",
            "rm -f -r /tmp/test",
            "rm --recursive --force ./dist",
            "sudo rm -rf /var/log"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertFalse(allowed, f"Should block: {cmd}")
            self.assertIn("rm -rf", msg)

    def test_blocks_git_force_push(self):
        cmds = [
            "git push --force origin main",
            "git push origin main -f",
            "git push --force"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertFalse(allowed, f"Should block: {cmd}")
            self.assertIn("git push --force", msg)

    def test_blocks_drop_table(self):
        cmds = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "psql -c 'DROP TABLE transactions;'"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertFalse(allowed, f"Should block: {cmd}")
            self.assertIn("DROP TABLE", msg)

    def test_blocks_truncate(self):
        cmds = [
            "TRUNCATE TABLE logs;",
            "truncate users;"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertFalse(allowed, f"Should block: {cmd}")

    def test_blocks_unqualified_delete(self):
        cmds = [
            "DELETE FROM users;",
            "delete from accounts;"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertFalse(allowed, f"Should block: {cmd}")
            self.assertIn("WHERE", msg)

    def test_allows_safe_delete_with_where(self):
        cmds = [
            "DELETE FROM users WHERE id = 5;",
            "delete from accounts where status = 'inactive';"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertTrue(allowed, f"Should allow safe delete: {cmd}")

    def test_allows_normal_bash_commands(self):
        cmds = [
            "ls -la",
            "git status",
            "npm test",
            "python3 -m unittest",
            "echo 'Hello World'",
            "rm myfile.txt",
            "git push origin feature-branch"
        ]
        for cmd in cmds:
            allowed, msg = evaluate_command(cmd, self.temp_dir, self.log_file)
            self.assertTrue(allowed, f"Should allow safe command: {cmd}")

    def test_log_file_formatting(self):
        evaluate_command("rm -rf /test", self.temp_dir, self.log_file)
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("rm -rf", content)
        self.assertIn(self.temp_dir, content)

if __name__ == "__main__":
    unittest.main()
