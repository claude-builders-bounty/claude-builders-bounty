#!/usr/bin/env python3
"""Tests for hooks/block-destructive-commands.py.

Run:  python3 -m pytest tests/ -v
  or: python3 -m unittest discover -s tests -v
  or: python3 tests/test_block_destructive_commands.py

No third-party dependencies. Stdlib unittest only.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "hooks" / "block-destructive-commands.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("block_hook", HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hook = load_hook()


class TestRm(unittest.TestCase):
    def test_rm_rf_blocked(self):
        self.assertIsNotNone(hook.check_command("rm -rf /tmp/foo"))

    def test_rm_fr_blocked(self):
        self.assertIsNotNone(hook.check_command("rm -fr /tmp/foo"))

    def test_rm_r_f_separate_flags_blocked(self):
        self.assertIsNotNone(hook.check_command("rm -r -f /tmp/foo"))
        self.assertIsNotNone(hook.check_command("rm -f -r /tmp/foo"))

    def test_rm_long_flags_blocked(self):
        self.assertIsNotNone(hook.check_command("rm --recursive --force /tmp/foo"))

    def test_rm_rf_root_blocked(self):
        self.assertIsNotNone(hook.check_command("rm -rf /"))

    def test_rm_rf_home_blocked(self):
        self.assertIsNotNone(hook.check_command("rm -rf ~"))

    def test_sudo_rm_rf_blocked(self):
        self.assertIsNotNone(hook.check_command("sudo rm -rf /tmp/foo"))

    def test_rm_rf_chained_blocked(self):
        self.assertIsNotNone(hook.check_command("ls -la && rm -rf /tmp/x"))
        self.assertIsNotNone(hook.check_command("rm -rf /tmp/x; echo done"))

    def test_rm_plain_file_allowed(self):
        self.assertIsNone(hook.check_command("rm file.txt"))

    def test_rm_recursive_without_force_allowed(self):
        # Per the bounty spec only rm -rf is listed; -r alone is allowed.
        self.assertIsNone(hook.check_command("rm -r /tmp/foo"))

    def test_rm_force_without_recursive_allowed(self):
        self.assertIsNone(hook.check_command("rm -f file.txt"))

    def test_echo_rm_rf_quoted_allowed(self):
        # Quoted text is not a command being run.
        self.assertIsNone(hook.check_command('echo "rm -rf /"'))


class TestGitPush(unittest.TestCase):
    def test_git_push_force_blocked(self):
        self.assertIsNotNone(hook.check_command("git push --force origin main"))

    def test_git_push_f_blocked(self):
        self.assertIsNotNone(hook.check_command("git push -f origin main"))

    def test_git_push_force_after_remote_blocked(self):
        self.assertIsNotNone(hook.check_command("git push origin main --force"))

    def test_sudo_git_push_force_blocked(self):
        self.assertIsNotNone(hook.check_command("sudo git push --force"))

    def test_git_push_plain_allowed(self):
        self.assertIsNone(hook.check_command("git push origin main"))

    def test_git_push_force_with_lease_allowed(self):
        # Safe alternative — explicitly allowed, not blocked.
        self.assertIsNone(hook.check_command("git push --force-with-lease origin main"))
        self.assertIsNone(hook.check_command("git push --force-with-lease"))

    def test_git_push_force_plus_lease_blocked(self):
        # --force present alongside --force-with-lease still blocks.
        self.assertIsNotNone(
            hook.check_command("git push --force --force-with-lease origin main")
        )


class TestSql(unittest.TestCase):
    def test_drop_table_blocked(self):
        self.assertIsNotNone(hook.check_command("DROP TABLE users"))

    def test_drop_table_lowercase_blocked(self):
        self.assertIsNotNone(hook.check_command("drop table users"))

    def test_drop_table_if_exists_blocked(self):
        self.assertIsNotNone(hook.check_command("DROP TABLE IF EXISTS users;"))

    def test_drop_table_via_psql_blocked(self):
        self.assertIsNotNone(hook.check_command('psql -c "DROP TABLE users"'))

    def test_truncate_table_blocked(self):
        self.assertIsNotNone(hook.check_command("TRUNCATE TABLE users"))

    def test_truncate_bare_blocked(self):
        self.assertIsNotNone(hook.check_command("truncate users"))

    def test_delete_without_where_blocked(self):
        self.assertIsNotNone(hook.check_command("DELETE FROM users"))
        self.assertIsNotNone(hook.check_command("DELETE FROM users;"))
        self.assertIsNotNone(hook.check_command("delete from users"))

    def test_delete_with_where_allowed(self):
        self.assertIsNone(hook.check_command("DELETE FROM users WHERE id = 1"))
        self.assertIsNone(
            hook.check_command("DELETE FROM users WHERE name = 'Alice'")
        )

    def test_delete_mixed_statements(self):
        # One safe statement + one unsafe statement => blocked.
        self.assertIsNotNone(
            hook.check_command(
                "SELECT * FROM users; DELETE FROM users"
            )
        )
        self.assertIsNone(
            hook.check_command(
                "SELECT * FROM users; DELETE FROM users WHERE id = 1"
            )
        )

    def test_select_allowed(self):
        self.assertIsNone(hook.check_command("SELECT * FROM users"))
        self.assertIsNone(hook.check_command("CREATE TABLE users (id INT)"))


class TestNormalCommands(unittest.TestCase):
    def test_everyday_commands_allowed(self):
        for cmd in [
            "ls -la",
            "echo hello",
            "git status",
            "git pull origin main",
            "npm test",
            "python3 -m pytest tests/ -v",
            "cat README.md",
            "mkdir -p build",
        ]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(hook.check_command(cmd))

    def test_empty_allowed(self):
        self.assertIsNone(hook.check_command(""))
        self.assertIsNone(hook.check_command("   "))


class TestHookProtocol(unittest.TestCase):
    def _run_hook(self, payload, env_extra=None):
        env = dict(os.environ)
        env.update(env_extra or {})
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )
        return proc

    def test_deny_json_and_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "blocked.log"
            proc = self._run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /tmp/x"},
                    "cwd": "/tmp/myproject",
                },
                {"HOOK_BLOCKED_LOG": str(log)},
            )
            self.assertEqual(proc.returncode, 0)
            out = json.loads(proc.stdout)
            decision = out["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")
            self.assertIn("rm", out["hookSpecificOutput"]["permissionDecisionReason"])
            # Log line has timestamp, command and project path.
            logged = log.read_text()
            self.assertIn("rm -rf /tmp/x", logged)
            self.assertIn("/tmp/myproject", logged)
            self.assertIn("reason=", logged)

    def test_allow_json(self):
        proc = self._run_hook(
            {"tool_name": "Bash", "tool_input": {"command": "ls -la"}, "cwd": "/tmp"}
        )
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(
            out["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_non_bash_tool_allowed(self):
        proc = self._run_hook(
            {"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}, "cwd": "/tmp"}
        )
        out = json.loads(proc.stdout)
        self.assertEqual(
            out["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_malformed_input_fails_open(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not json at all",
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(
            out["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_check_flag(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH), "--check", "DELETE FROM users"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("BLOCKED", proc.stdout)
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH), "--check", "ls -la"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ALLOWED", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
