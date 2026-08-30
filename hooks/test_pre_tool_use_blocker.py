#!/usr/bin/env python3
import unittest
from pre_tool_use_blocker import evaluate_hook, check_command_blocked

class TestPreToolUseBlocker(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIsNotNone(check_command_blocked("rm -rf /tmp/data"))
        self.assertIsNotNone(check_command_blocked("rm -fr node_modules"))
        self.assertIsNotNone(check_command_blocked("rm --recursive --force ."))

    def test_blocks_drop_table(self):
        self.assertIsNotNone(check_command_blocked("DROP TABLE users;"))
        self.assertIsNotNone(check_command_blocked("psql -c 'DROP DATABASE production'"))

    def test_blocks_truncate(self):
        self.assertIsNotNone(check_command_blocked("TRUNCATE TABLE logs;"))
        self.assertIsNotNone(check_command_blocked("TRUNCATE sessions;"))

    def test_blocks_unscoped_delete(self):
        self.assertIsNotNone(check_command_blocked("DELETE FROM users;"))
        self.assertIsNotNone(check_command_blocked("DELETE FROM accounts"))

    def test_allows_scoped_delete(self):
        self.assertIsNone(check_command_blocked("DELETE FROM users WHERE id = 5;"))

    def test_blocks_git_force_push(self):
        self.assertIsNotNone(check_command_blocked("git push origin main --force"))
        self.assertIsNotNone(check_command_blocked("git push -f upstream master"))

    def test_allows_safe_bash_commands(self):
        self.assertIsNone(check_command_blocked("ls -la"))
        self.assertIsNone(check_command_blocked("git status"))
        self.assertIsNone(check_command_blocked("npm run build"))
        self.assertIsNone(check_command_blocked("cargo test"))
        self.assertIsNone(check_command_blocked("rm safe_file.txt"))

    def test_evaluate_hook_output_structure(self):
        # Safe command
        res = evaluate_hook({"tool_name": "Bash", "tool_input": {"command": "npm test"}})
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "allow")

        # Destructive command
        res = evaluate_hook({"tool_name": "Bash", "tool_input": {"command": "rm -rf build/"}})
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "block")
        self.assertIn("DESTRUCTIVE", res["hookSpecificOutput"]["reason"])

if __name__ == "__main__":
    unittest.main()
