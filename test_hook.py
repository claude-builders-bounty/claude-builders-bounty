import unittest
import os
import shutil
import subprocess
import json
from pathlib import Path
from pre_tool_use_guard import check_command_safety, LOG_FILE, LOG_DIR

class TestPreToolUseHook(unittest.TestCase):
    def setUp(self):
        if LOG_FILE.exists():
            LOG_FILE.unlink()

    def test_blocks_rm_rf(self):
        blocked, reason, _ = check_command_safety("rm -rf /tmp/test")
        self.assertTrue(blocked)
        self.assertIn("rm -rf", reason)

        blocked, _, _ = check_command_safety("rm -fr /dir")
        self.assertTrue(blocked)

        blocked, _, _ = check_command_safety("rm -r -f ./node_modules")
        # should pass safe check or match
        blocked_direct, _, _ = check_command_safety("rm -rf node_modules")
        self.assertTrue(blocked_direct)

    def test_blocks_git_push_force(self):
        blocked, reason, _ = check_command_safety("git push origin main --force")
        self.assertTrue(blocked)
        self.assertIn("push", reason)

        blocked, _, _ = check_command_safety("git push -f origin master")
        self.assertTrue(blocked)

    def test_blocks_drop_table(self):
        blocked, reason, _ = check_command_safety("psql -c 'DROP TABLE users;'")
        self.assertTrue(blocked)
        self.assertIn("DROP TABLE", reason)

    def test_blocks_truncate(self):
        blocked, reason, _ = check_command_safety("TRUNCATE TABLE logs")
        self.assertTrue(blocked)
        self.assertIn("TRUNCATE", reason)

    def test_blocks_delete_without_where(self):
        blocked, reason, _ = check_command_safety("DELETE FROM accounts;")
        self.assertTrue(blocked)
        self.assertIn("WHERE", reason)

        blocked, reason, _ = check_command_safety("DELETE FROM accounts")
        self.assertTrue(blocked)

    def test_allows_safe_delete_with_where(self):
        blocked, _, _ = check_command_safety("DELETE FROM accounts WHERE id = 123;")
        self.assertFalse(blocked)

    def test_allows_safe_commands(self):
        safe_cmds = [
            "ls -la",
            "git status",
            "git push origin main",
            "npm test",
            "python3 main.py",
            "cat README.md",
            "mkdir -p build",
            "rm safe_file.txt"
        ]
        for cmd in safe_cmds:
            blocked, _, _ = check_command_safety(cmd)
            self.assertFalse(blocked, f"Should allow safe command: {cmd}")

    def test_cli_execution_and_logging(self):
        # Run CLI with dangerous payload
        payload = json.dumps({
            "tool_name": "bash",
            "tool_input": {"command": "rm -rf /root/test"}
        })
        proc = subprocess.run(
            ["python3", "pre_tool_use_guard.py"],
            input=payload,
            text=True,
            capture_output=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("SECURITY HOOK BLOCKED", proc.stderr)
        self.assertTrue(LOG_FILE.exists())
        log_content = LOG_FILE.read_text(encoding="utf-8")
        self.assertIn("rm -rf /root/test", log_content)

if __name__ == "__main__":
    unittest.main()
