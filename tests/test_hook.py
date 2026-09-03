#!/usr/bin/env python3
"""
Comprehensive test suite for Claude Code Destructive Bash Command Interceptor Hook.

Runs both standalone and via test discovery:
  python -m unittest discover -s tests -p "test_*.py" -v
  python -m unittest tests.test_hook -v
"""

import sys
import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "block_destructive.py"

if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from block_destructive import check_command


class TestDestructiveCommandBlocking(unittest.TestCase):
    """Negative test gate: verifies all dangerous patterns return exit code 2 and write to blocked.log."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"
        self.env = dict(os.environ)
        self.env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, command: str) -> subprocess.CompletedProcess:
        payload = json.dumps({
            "tool_name": "Bash",
            "cwd": str(REPO_ROOT),
            "tool_input": {"command": command}
        })
        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            env=self.env
        )

    def assert_blocked(self, command: str, expected_rule: str):
        proc = self.run_hook(command)
        self.assertEqual(proc.returncode, 2, f"Expected exit code 2 for '{command}', got {proc.returncode}")
        self.assertIn("SECURITY HOOK BLOCKED", proc.stderr)
        self.assertIn(expected_rule, proc.stderr)

        # Check stdout JSON
        data = json.loads(proc.stdout)
        self.assertEqual(data.get("hookSpecificOutput", {}).get("permissionDecision"), "deny")

        # Check log file
        self.assertTrue(self.log_file.exists())
        log_content = self.log_file.read_text(encoding="utf-8")
        self.assertIn(expected_rule, log_content)

    def test_block_rm_rf_root(self):
        self.assert_blocked("rm -rf /", "rm_rf")

    def test_block_rm_rf_home(self):
        self.assert_blocked("rm -rf ~", "rm_rf")

    def test_block_rm_rf_wildcard(self):
        self.assert_blocked("rm -rf *", "rm_rf")

    def test_block_rm_fr_variant(self):
        self.assert_blocked("rm -fr target/", "rm_rf")

    def test_block_rm_split_flags(self):
        self.assert_blocked("rm -r -f node_modules", "rm_rf")

    def test_block_rm_long_flags(self):
        self.assert_blocked("rm --recursive --force dist", "rm_rf")

    def test_block_rm_sudo(self):
        self.assert_blocked("sudo rm -rf /var", "rm_rf")

    def test_block_drop_table(self):
        self.assert_blocked("DROP TABLE users;", "drop_table")

    def test_block_drop_database(self):
        self.assert_blocked("DROP DATABASE production;", "drop_table")

    def test_block_git_force_push(self):
        self.assert_blocked("git push --force origin main", "git_force")

    def test_block_git_f_push(self):
        self.assert_blocked("git push -f origin main", "git_force")

    def test_block_git_force_lease(self):
        self.assert_blocked("git push --force-with-lease", "git_force")

    def test_block_git_refspec_force(self):
        self.assert_blocked("git push origin +main", "git_force")

    def test_block_truncate(self):
        self.assert_blocked("TRUNCATE TABLE audit_log;", "truncate")

    def test_block_delete_without_where(self):
        self.assert_blocked("DELETE FROM users;", "delete_without_where")

    def test_block_raw_disk_mkfs(self):
        self.assert_blocked("mkfs.ext4 /dev/sda1", "raw_disk")

    def test_block_raw_disk_dd(self):
        self.assert_blocked("dd if=/dev/zero of=/dev/sda bs=1M", "raw_disk")

    def test_block_fork_bomb(self):
        self.assert_blocked(":(){ :|:& };:", "fork_bomb")

    def test_block_shutdown(self):
        self.assert_blocked("shutdown -h now", "system_state")

    def test_block_chmod_777_root(self):
        self.assert_blocked("chmod -R 777 /", "perm_wipe")


class TestSafeCommandPassing(unittest.TestCase):
    """Positive test gate: verifies normal developer workflows exit 0 with empty stderr."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"
        self.env = dict(os.environ)
        self.env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, command: str) -> subprocess.CompletedProcess:
        payload = json.dumps({
            "tool_name": "Bash",
            "cwd": str(REPO_ROOT),
            "tool_input": {"command": command}
        })
        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            env=self.env
        )

    def assert_allowed(self, command: str):
        proc = self.run_hook(command)
        self.assertEqual(proc.returncode, 0, f"Expected exit code 0 for '{command}', got {proc.returncode}: {proc.stderr}")
        self.assertEqual(proc.stderr, "")
        self.assertFalse(self.log_file.exists(), "Safe command should not create audit log")

    def test_safe_git_status(self):
        self.assert_allowed("git status")

    def test_safe_git_diff(self):
        self.assert_allowed("git diff HEAD~1")

    def test_safe_git_commit(self):
        self.assert_allowed("git commit -m 'feat: add hook'")

    def test_safe_git_push(self):
        self.assert_allowed("git push origin feature-branch")

    def test_safe_npm_test(self):
        self.assert_allowed("npm test")

    def test_safe_python_unittest(self):
        self.assert_allowed("python -m unittest discover")

    def test_safe_pytest(self):
        self.assert_allowed("pytest tests/")

    def test_safe_cargo_test(self):
        self.assert_allowed("cargo test")

    def test_safe_file_removal(self):
        self.assert_allowed("rm README.txt")

    def test_safe_single_force_removal(self):
        self.assert_allowed("rm -f temp.log")

    def test_safe_sql_select(self):
        self.assert_allowed("SELECT * FROM users WHERE active = 1;")

    def test_safe_sql_delete_with_where(self):
        self.assert_allowed("DELETE FROM users WHERE id = 42;")

    def test_safe_sql_update(self):
        self.assert_allowed("UPDATE accounts SET balance = 100 WHERE id = 1;")


class TestCompoundAndEvasionCommands(unittest.TestCase):
    """Tests that chained operators, subshells, and wrappers are intercepted."""

    def test_compound_and_operator(self):
        res = check_command("git status && rm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_compound_semicolon(self):
        res = check_command("ls -la ; git push -f")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "git_force")

    def test_compound_pipe(self):
        res = check_command("cat data.txt | rm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_compound_newline(self):
        res = check_command("git status\nrm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_subshell_expansion(self):
        res = check_command("echo $(rm -rf /)")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_backtick_expansion(self):
        res = check_command("echo `rm -rf /`")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_bash_c_wrapper(self):
        res = check_command('bash -c "rm -rf /"')
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")


if __name__ == "__main__":
    unittest.main()
