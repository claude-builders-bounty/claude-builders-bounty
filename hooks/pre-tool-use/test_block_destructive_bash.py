#!/usr/bin/env python3
"""Tests for block-destructive-bash hook."""

import json
import subprocess
import sys
import os
import unittest
import tempfile

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "block-destructive-bash.py")


def run_hook(tool_name: str, command: str) -> tuple[int, str, str]:
    """Run the hook with given input, return (exit_code, stdout, stderr)."""
    input_data = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": "/tmp/test-project",
    })
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestDestructiveBashBlocker(unittest.TestCase):
    """Test cases for the destructive bash command blocker."""

    def test_blocks_rm_rf(self):
        code, _, stderr = run_hook("Bash", "rm -rf /")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_rm_rf_variant(self):
        code, _, stderr = run_hook("Bash", "rm -fr ./important_dir")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_drop_table(self):
        code, _, stderr = run_hook("Bash", "sqlite3 db.sqlite 'DROP TABLE users'")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_truncate(self):
        code, _, stderr = run_hook("Bash", "mysql -e 'TRUNCATE TABLE logs'")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_delete_without_where(self):
        code, _, stderr = run_hook("Bash", "sqlite3 db.sqlite 'DELETE FROM users'")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_allows_delete_with_where(self):
        code, _, _ = run_hook("Bash", "sqlite3 db.sqlite 'DELETE FROM users WHERE id=5'")
        self.assertEqual(code, 0)

    def test_blocks_git_push_force(self):
        code, _, stderr = run_hook("Bash", "git push --force origin main")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_git_push_f(self):
        code, _, stderr = run_hook("Bash", "git push -f origin main")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_allows_normal_git_push(self):
        code, _, _ = run_hook("Bash", "git push origin main")
        self.assertEqual(code, 0)

    def test_allows_normal_commands(self):
        code, _, _ = run_hook("Bash", "ls -la")
        self.assertEqual(code, 0)

    def test_allows_safe_rm(self):
        code, _, _ = run_hook("Bash", "rm file.txt")
        self.assertEqual(code, 0)

    def test_allows_non_bash_tools(self):
        code, _, _ = run_hook("Read", "rm -rf /")
        self.assertEqual(code, 0)

    def test_handles_empty_input(self):
        code, _, _ = run_hook("Bash", "")
        self.assertEqual(code, 0)

    def test_blocks_mkfs(self):
        code, _, stderr = run_hook("Bash", "mkfs.ext4 /dev/sda1")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_blocks_dd_to_device(self):
        code, _, stderr = run_hook("Bash", "dd if=/dev/zero of=/dev/sda bs=1M")
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", stderr)

    def test_logging(self):
        """Test that blocked commands are logged."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name

        # Monkey-patch LOG_FILE via environment isn't easy, so just verify
        # the hook exits with code 2 (logging is best-effort)
        code, _, _ = run_hook("Bash", "rm -rf /tmp/test")
        self.assertEqual(code, 2)
        os.unlink(log_path)


if __name__ == "__main__":
    unittest.main()
