#!/usr/bin/env python3
import unittest
from block_destructive import check_command

class TestSecurityHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, reason = check_command("rm -rf /tmp/data")
        self.assertFalse(blocked)
        self.assertIn("rm -rf", reason)

        blocked, _ = check_command("rm -f file.txt")
        self.assertFalse(blocked)

    def test_blocks_drop_table(self):
        blocked, reason = check_command("DROP TABLE users;")
        self.assertFalse(blocked)
        self.assertIn("DROP", reason)

    def test_blocks_git_force_push(self):
        blocked, reason = check_command("git push origin main --force")
        self.assertFalse(blocked)
        self.assertIn("force-push", reason)

        blocked, _ = check_command("git push -f origin main")
        self.assertFalse(blocked)

    def test_blocks_truncate(self):
        blocked, _ = check_command("TRUNCATE TABLE logs")
        self.assertFalse(blocked)

    def test_blocks_delete_without_where(self):
        blocked, _ = check_command("DELETE FROM customers")
        self.assertFalse(blocked)

        blocked, _ = check_command("DELETE FROM customers;")
        self.assertFalse(blocked)

    def test_allows_safe_commands(self):
        safe_commands = [
            "ls -la",
            "git status",
            "git push origin feature-branch",
            "npm test",
            "SELECT * FROM users WHERE id = 1;",
            "DELETE FROM sessions WHERE expired_at < NOW();",
            "rmdir empty_dir",
        ]
        for cmd in safe_commands:
            allowed, _ = check_command(cmd)
            self.assertTrue(allowed, f"Expected safe command to be allowed: {cmd}")

if __name__ == "__main__":
    unittest.main()
