#!/usr/bin/env python3
"""
Test suite for the destructive command blocker hook.
"""

import unittest
import sys
import io
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from pre_tool_use import check_command, log_blocked, ALWAYS_BLOCK, NEEDS_WHERE


class TestCheckCommand(unittest.TestCase):
    
    def test_rm_rf_blocked(self):
        blocked, reason = check_command("rm -rf /tmp/test")
        self.assertTrue(blocked)
        self.assertIn("rm", reason.lower())
    
    def test_rm_f_blocked(self):
        blocked, reason = check_command("rm -f important.txt")
        self.assertTrue(blocked)
    
    def test_git_push_force_blocked(self):
        blocked, reason = check_command("git push origin main --force")
        self.assertTrue(blocked)
        self.assertIn("force", reason.lower())
    
    def test_drop_table_blocked(self):
        blocked, reason = check_command("DROP TABLE users")
        self.assertTrue(blocked)
        self.assertIn("drop", reason.lower())
    
    def test_truncate_table_blocked(self):
        blocked, reason = check_command("TRUNCATE TABLE logs")
        self.assertTrue(blocked)
        self.assertIn("truncate", reason.lower())
    
    def test_delete_without_where_blocked(self):
        blocked, reason = check_command("DELETE FROM users")
        self.assertTrue(blocked)
        self.assertIn("where", reason.lower())
    
    def test_delete_with_where_allowed(self):
        blocked, reason = check_command("DELETE FROM users WHERE id = 1")
        self.assertFalse(blocked)
        self.assertIn("safe", reason.lower())
    
    def test_mkfs_blocked(self):
        blocked, _ = check_command("mkfs.ext4 /dev/sda1")
        self.assertTrue(blocked)
    
    def test_dd_blocked(self):
        blocked, _ = check_command("dd if=/dev/zero of=/dev/sda")
        self.assertTrue(blocked)
    
    def test_safe_command(self):
        blocked, reason = check_command("echo 'hello world'")
        self.assertFalse(blocked)
        self.assertIn("no destructive", reason.lower())
    
    def test_ls_allowed(self):
        blocked, _ = check_command("ls -la /tmp")
        self.assertFalse(blocked)
    
    def test_rm_log_exception(self):
        # rm -f *.log is explicitly allowed
        blocked, _ = check_command("rm -f debug.log")
        self.assertFalse(blocked)


class TestLogBlocked(unittest.TestCase):
    
    def test_log_creates_file(self):
        log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
        log_blocked("test command", "test reason", "/tmp/test")
        self.assertTrue(log_path.exists())
        
        # Verify log entry
        with open(log_path) as f:
            lines = f.readlines()
            last_line = lines[-1]
            entry = json.loads(last_line)
            self.assertEqual(entry["attempted_command"], "test command")
            self.assertEqual(entry["reason"], "test reason")
            self.assertEqual(entry["project_path"], "/tmp/test")
            self.assertIn("timestamp", entry)


class TestMain(unittest.TestCase):
    
    def test_main_passes_bash(self):
        """Test that main() passes through non-destructive Bash commands."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'hello'"},
            "project_path": "/tmp"
        }
        
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(input_data))
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        from pre_tool_use import main
        main()
        
        output = sys.stdout.getvalue().strip()
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        
        result = json.loads(output)
        self.assertEqual(result["tool_input"]["command"], "echo 'hello'")
        self.assertNotIn("_hook_blocked", result)
    
    def test_main_blocks_destructive(self):
        """Test that main() blocks destructive commands."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/test"},
            "project_path": "/tmp"
        }
        
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(input_data))
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        from pre_tool_use import main
        main()
        
        output = sys.stdout.getvalue().strip()
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        
        result = json.loads(output)
        self.assertTrue(result.get("_hook_blocked"))
        self.assertIn("BLOCKED", result["tool_input"]["command"])
    
    def test_main_passes_non_bash(self):
        """Test that non-Bash tools pass through."""
        input_data = {
            "tool_name": "ReadFile",
            "tool_input": {"path": "/tmp/file.txt"},
            "project_path": "/tmp"
        }
        
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(input_data))
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        from pre_tool_use import main
        main()
        
        output = sys.stdout.getvalue().strip()
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        
        result = json.loads(output)
        self.assertEqual(result["tool_name"], "ReadFile")
        self.assertNotIn("_hook_blocked", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
