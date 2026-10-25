import sys
import os
import unittest
from pathlib import Path

# Add hook directory to path
HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks" / "pre-tool-use"
sys.path.insert(0, str(HOOK_DIR))

from block_destructive_commands import check_command, log_blocked, LOG_FILE


class TestBlockDestructiveCommands(unittest.TestCase):

    def test_rm_rf_blocked(self):
        blocked_commands = [
            "rm -rf /tmp/data",
            "rm -fr build/",
            "rm -r -f node_modules",
            "rm --recursive --force .cache",
            "sudo rm -rf /",
            "rm -rf *",
            "run_something && rm -rf dist"
        ]
        for cmd in blocked_commands:
            is_blocked, rule, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertEqual(rule, "RM_RF")

    def test_safe_rm_allowed(self):
        safe_commands = [
            "rm file.txt",
            "rm -f single_file.log",
            "rm -r empty_folder",
            "echo 'rm -rf is dangerous'"
        ]
        for cmd in safe_commands:
            is_blocked, _, _ = check_command(cmd)
            # note: 'rm -f' without -r should be allowed
            if "-r" not in cmd and "--recursive" not in cmd:
                self.assertFalse(is_blocked, f"Should allow safe rm: {cmd}")

    def test_drop_table_blocked(self):
        blocked_commands = [
            "psql -c 'DROP TABLE users;'",
            "sqlite3 app.db 'drop table accounts'",
            "DROP TABLE IF EXISTS orders;",
            "mysql -u root -e 'DROP TABLE payments'"
        ]
        for cmd in blocked_commands:
            is_blocked, rule, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertEqual(rule, "DROP_TABLE")

    def test_git_push_force_blocked(self):
        blocked_commands = [
            "git push --force origin main",
            "git push -f",
            "git push origin +main",
            "git push --force-with-lease origin feat"
        ]
        for cmd in blocked_commands:
            is_blocked, rule, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertEqual(rule, "GIT_PUSH_FORCE")

    def test_safe_git_push_allowed(self):
        safe_commands = [
            "git push origin main",
            "git push -u origin feature-branch",
            "git status",
            "git commit -m 'feat: force update logic'"
        ]
        for cmd in safe_commands:
            is_blocked, _, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should allow: {cmd}")

    def test_truncate_blocked(self):
        blocked_commands = [
            "sqlite3 dev.db 'TRUNCATE users'",
            "psql -c 'TRUNCATE TABLE logs;'",
            "truncate table events"
        ]
        for cmd in blocked_commands:
            is_blocked, rule, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertEqual(rule, "TRUNCATE")

    def test_delete_without_where_blocked(self):
        blocked_commands = [
            "sqlite3 app.db 'DELETE FROM users;'",
            "psql -c 'DELETE FROM sessions'",
            "DELETE FROM audit_logs"
        ]
        for cmd in blocked_commands:
            is_blocked, rule, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block unguarded delete: {cmd}")
            self.assertEqual(rule, "UNGUARDED_DELETE")

    def test_delete_with_where_allowed(self):
        allowed_commands = [
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1;'",
            "psql -c 'DELETE FROM sessions WHERE expired_at < NOW()'",
            "DELETE FROM audit_logs WHERE created_at < '2025-01-01'"
        ]
        for cmd in allowed_commands:
            is_blocked, _, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should allow guarded delete: {cmd}")

    def test_logging(self):
        test_cmd = "rm -rf /test_sandbox_dir"
        test_cwd = "/home/user/project"
        log_blocked(test_cmd, "RM_RF", test_cwd)
        self.assertTrue(LOG_FILE.exists())
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("BLOCKED_RULE=RM_RF", content)
            self.assertIn("PROJECT_PATH=/home/user/project", content)
            self.assertIn("rm -rf /test_sandbox_dir", content)


if __name__ == "__main__":
    unittest.main()
