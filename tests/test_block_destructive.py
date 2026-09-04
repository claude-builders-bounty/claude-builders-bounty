#!/usr/bin/env python3
"""
Comprehensive Unit & Integration Test Suite for Claude Code PreToolUse Hook.
"""

import sys
import os
import json
import tempfile
import unittest
import subprocess
from pathlib import Path

# Add hook directory to path for direct imports
HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks" / "block-destructive"
sys.path.insert(0, str(HOOK_DIR))

import block_destructive


class TestPatternMatching(unittest.TestCase):
    """Test individual security rules and pattern detection logic."""

    def test_blocks_rm_rf_variants(self):
        cases = [
            "rm -rf /",
            "rm -fr /tmp",
            "rm -r -f node_modules",
            "rm -f -r build",
            "rm -R -f dist",
            "rm --recursive --force target",
            "rm --force --recursive target",
            "rm -rfv .",
            "rm -vrf .",
            "rm /var/data -rf",
            "sudo rm -rf /etc/hosts",
            "env rm -rf /tmp/data",
            "/bin/rm -rf /cache",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")
                rule, _ = result
                self.assertEqual(rule, "rm_rf")

    def test_allows_safe_rm(self):
        cases = [
            "rm file.txt",
            "rm -f temp.log",
            "rm -r docs/",
            "rm --help",
            "git rm file.py",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNone(result, f"Expected '{cmd}' to be allowed, but got: {result}")

    def test_blocks_drop_table_variants(self):
        cases = [
            "DROP TABLE users;",
            "drop table if exists session_data",
            "DROP TABLE `accounts`",
            'DROP TABLE "orders"',
            "DROP DATABASE production;",
            "DROP SCHEMA public CASCADE;",
            "psql -d mydb -c 'DROP TABLE customers;'",
            'mysql -u root -e "DROP TABLE sensitive_info;"',
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")
                rule, _ = result
                self.assertEqual(rule, "drop_table")

    def test_blocks_git_push_force(self):
        cases = [
            "git push --force",
            "git push -f",
            "git push origin main --force",
            "git push --force origin main",
            "git push --force-with-lease origin branch",
            "git push --force-if-includes",
            "git push origin +main",
            "git push origin +HEAD:main",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")
                rule, _ = result
                self.assertEqual(rule, "git_force")

    def test_allows_safe_git_push(self):
        cases = [
            "git push",
            "git push origin main",
            "git push -u origin feat/login",
            "git status",
            "git commit -m 'feat: update schema'",
            "git diff HEAD~1",
            "git pull origin main",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNone(result, f"Expected '{cmd}' to be allowed, but got: {result}")

    def test_blocks_sql_truncate(self):
        cases = [
            "TRUNCATE TABLE users;",
            "TRUNCATE users;",
            "truncate table `audit_logs`",
            'TRUNCATE "payments"',
            "truncate sessions",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")
                rule, _ = result
                self.assertEqual(rule, "truncate")

    def test_allows_coreutils_truncate(self):
        cases = [
            "truncate -s 0 debug.log",
            "truncate --size=0 app.log",
            "truncate -s 10M file.bin",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNone(result, f"Expected '{cmd}' to be allowed, but got: {result}")

    def test_blocks_delete_without_where(self):
        cases = [
            "DELETE FROM users;",
            "DELETE FROM users",
            "delete from `accounts`;",
            'DELETE FROM "sessions"',
            "DELETE FROM db.audit_records",
            "psql -c 'DELETE FROM orders;'",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")
                rule, _ = result
                self.assertEqual(rule, "delete_without_where")

    def test_allows_delete_with_where(self):
        cases = [
            "DELETE FROM users WHERE id = 123;",
            "DELETE FROM accounts WHERE active = 0;",
            "delete from sessions where expired_at < NOW();",
            "DELETE FROM orders WHERE user_id = 5 AND status = 'cancelled';",
            "DELETE FROM items WHERE id IN (SELECT item_id FROM old_items WHERE date < '2020-01-01');",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNone(result, f"Expected '{cmd}' to be allowed, but got: {result}")

    def test_blocks_bonus_threats(self):
        cases = [
            ":(){ :|:& };:",
            "while true; do : & done",
            "mkfs.ext4 /dev/sda1",
            "dd if=/dev/zero of=/dev/sda bs=1M",
            "chmod -R 777 /",
            "chown -R root /etc",
            "shutdown -h now",
            "reboot",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected '{cmd}' to be blocked")


class TestCompoundAndEvasion(unittest.TestCase):
    """Test compound command chains, subshells, and wrapper bypass attempts."""

    def test_blocks_chained_operators(self):
        cases = [
            "echo 'building' && rm -rf /",
            "git status || rm -rf build",
            "ls -la; DROP TABLE users;",
            "cat file.txt | git push --force",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected compound command '{cmd}' to be blocked")

    def test_blocks_subshell_executions(self):
        cases = [
            "echo $(rm -rf /)",
            "echo `git push --force`",
            "bash -c 'rm -rf /tmp'",
            "sh -c 'DROP TABLE accounts'",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNotNone(result, f"Expected subshell command '{cmd}' to be blocked")

    def test_allows_text_and_grep_commands(self):
        cases = [
            "echo 'DROP TABLE users'",
            "grep 'rm -rf' documentation.md",
            "git commit -m 'refactor: remove DROP TABLE note'",
            "cat query.sql",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                result = block_destructive.check_command(cmd)
                self.assertIsNone(result, f"Expected '{cmd}' to be allowed, but got: {result}")


class TestAuditLogging(unittest.TestCase):
    """Test logging to ~/.claude/hooks/blocked.log."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.tmp_dir.name) / "blocked.log"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_logs_blocked_attempt_format(self):
        cmd = "rm -rf /var/log"
        cwd = "/home/developer/app"
        rule = "rm_rf"
        reason = "Destructive file deletion: 'rm -rf' detected"

        block_destructive.log_blocked_attempt(cmd, cwd, rule, reason, self.log_file)

        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("[RULE: rm_rf]", content)
        self.assertIn(f"BLOCKED: {cmd}", content)
        self.assertIn(f"[PATH: {cwd}]", content)
        self.assertIn(reason, content)

    def test_logs_append_multiple_attempts(self):
        block_destructive.log_blocked_attempt("rm -rf /", "/dir1", "rm_rf", "reason1", self.log_file)
        block_destructive.log_blocked_attempt("DROP TABLE test;", "/dir2", "drop_table", "reason2", self.log_file)

        lines = self.log_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("rm -rf /", lines[0])
        self.assertIn("DROP TABLE test;", lines[1])


class TestClaudeCodeProtocol(unittest.TestCase):
    """Test stdin JSON IPC protocol, exit codes (2 for block, 0 for allow)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.tmp_dir.name) / "blocked.log"
        self.hook_script = str(HOOK_DIR / "block_destructive.py")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def run_hook_stdin(self, payload: dict) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)
        return subprocess.run(
            [sys.executable, self.hook_script],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env
        )

    def test_destructive_bash_command_exits_2(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/test/workspace",
            "tool_input": {
                "command": "rm -rf /"
            }
        }
        res = self.run_hook_stdin(payload)
        self.assertEqual(res.returncode, 2)
        self.assertIn("[SECURITY HOOK BLOCKED]", res.stderr)
        self.assertIn("rm -rf", res.stderr)

        stdout_data = json.loads(res.stdout)
        self.assertEqual(stdout_data["hookSpecificOutput"]["permissionDecision"], "deny")

        # Verify audit log was created
        self.assertTrue(self.log_file.exists())
        log_content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("rm -rf /", log_content)

    def test_safe_bash_command_exits_0(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/test/workspace",
            "tool_input": {
                "command": "git status"
            }
        }
        res = self.run_hook_stdin(payload)
        self.assertEqual(res.returncode, 0)
        stdout_data = json.loads(res.stdout)
        self.assertEqual(stdout_data["hookSpecificOutput"]["permissionDecision"], "allow")
        self.assertFalse(self.log_file.exists())

    def test_non_bash_tool_ignored(self):
        payload = {
            "tool_name": "EditFile",
            "tool_input": {
                "path": "rm -rf /"
            }
        }
        res = self.run_hook_stdin(payload)
        self.assertEqual(res.returncode, 0)
        stdout_data = json.loads(res.stdout)
        self.assertEqual(stdout_data["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_cli_check_flag(self):
        env = os.environ.copy()
        env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

        # Destructive -> Exit 2
        res_block = subprocess.run(
            [sys.executable, self.hook_script, "--check", "DROP TABLE users;"],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertEqual(res_block.returncode, 2)
        self.assertIn("DROP TABLE", res_block.stderr)

        # Safe -> Exit 0
        res_allow = subprocess.run(
            [sys.executable, self.hook_script, "--check", "DELETE FROM users WHERE id = 1;"],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertEqual(res_allow.returncode, 0)
        self.assertIn("ALLOWED", res_allow.stdout)


if __name__ == "__main__":
    unittest.main()
