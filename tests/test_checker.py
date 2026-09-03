#!/usr/bin/env python3
"""
Unit tests for the pattern detection and command checker engine.
"""

import sys
import unittest
from pathlib import Path

# Add .claude/hooks to sys.path
HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from block_destructive import check_command


class TestRmRfChecker(unittest.TestCase):
    """Tests for rm -rf permutations and safe rm commands."""

    def test_blocks_standard_rm_rf(self):
        res = check_command("rm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_permuted_rm_fr(self):
        res = check_command("rm -fr /tmp/test")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_split_flags(self):
        res = check_command("rm -r -f node_modules")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

        res2 = check_command("rm -f -r dist")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "rm_rf")

    def test_blocks_long_flags(self):
        res = check_command("rm --recursive --force build/")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

        res2 = check_command("rm --force --recursive target/")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "rm_rf")

    def test_blocks_verbose_combined_flags(self):
        res = check_command("rm -rfv /var/cache")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_flags_after_target(self):
        res = check_command("rm /tmp/data -rf")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_sudo_wrapped(self):
        res = check_command("sudo rm -rf /etc/test")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_allows_single_file_removal(self):
        self.assertIsNone(check_command("rm file.txt"))
        self.assertIsNone(check_command("rm /tmp/sample.log"))

    def test_allows_force_without_recursion(self):
        self.assertIsNone(check_command("rm -f temp.log"))
        self.assertIsNone(check_command("rm --force cache.db"))

    def test_allows_recursion_without_force(self):
        self.assertIsNone(check_command("rm -r build/"))
        self.assertIsNone(check_command("rm -R docs/"))


class TestSqlChecker(unittest.TestCase):
    """Tests for SQL destructive statements and safe queries."""

    def test_blocks_drop_table(self):
        res = check_command("DROP TABLE users;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "drop_table")

    def test_blocks_drop_table_case_insensitive(self):
        res = check_command("drop table if exists session_tokens;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "drop_table")

    def test_blocks_drop_database(self):
        res = check_command("DROP DATABASE production;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "drop_table")

    def test_blocks_drop_schema(self):
        res = check_command("DROP SCHEMA public CASCADE;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "drop_table")

    def test_blocks_truncate(self):
        res = check_command("TRUNCATE TABLE audit_log;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "truncate")

        res2 = check_command("truncate users")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "truncate")

    def test_blocks_delete_without_where(self):
        res = check_command("DELETE FROM users;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "delete_without_where")

        res2 = check_command("delete from accounts")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "delete_without_where")

    def test_allows_delete_with_where(self):
        self.assertIsNone(check_command("DELETE FROM users WHERE id = 10;"))
        self.assertIsNone(check_command("delete from sessions where expired_at < now();"))
        self.assertIsNone(check_command("DELETE FROM logs WHERE created_at < '2026-01-01';"))

    def test_allows_standard_queries(self):
        self.assertIsNone(check_command("SELECT * FROM users WHERE active = 1;"))
        self.assertIsNone(check_command("INSERT INTO accounts (name) VALUES ('alice');"))
        self.assertIsNone(check_command("UPDATE users SET email = 'a@b.com' WHERE id = 5;"))

    def test_allows_coreutils_truncate(self):
        self.assertIsNone(check_command("truncate -s 0 debug.log"))
        self.assertIsNone(check_command("truncate --size 10M file.bin"))


class TestGitChecker(unittest.TestCase):
    """Tests for git force pushes and safe git workflows."""

    def test_blocks_git_push_force(self):
        res = check_command("git push --force origin main")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "git_force")

    def test_blocks_git_push_short_f(self):
        res = check_command("git push -f origin main")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "git_force")

    def test_blocks_git_push_force_with_lease(self):
        res = check_command("git push --force-with-lease origin branch-1")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "git_force")

    def test_blocks_git_push_forced_refspec(self):
        res = check_command("git push origin +main")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "git_force")

    def test_allows_safe_git_push(self):
        self.assertIsNone(check_command("git push origin main"))
        self.assertIsNone(check_command("git push -u origin feat/new-api"))
        self.assertIsNone(check_command("git push"))

    def test_allows_safe_git_operations(self):
        self.assertIsNone(check_command("git status"))
        self.assertIsNone(check_command("git diff HEAD~1"))
        self.assertIsNone(check_command("git log -n 5"))
        self.assertIsNone(check_command("git commit -m 'fix: avoid rm -rf bug'"))
        self.assertIsNone(check_command("git checkout -b feature-test"))


class TestRawDiskAndSystemChecker(unittest.TestCase):
    """Tests for raw disk wipes, fork bombs, and system disruptions."""

    def test_blocks_mkfs(self):
        res = check_command("mkfs.ext4 /dev/sda1")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "raw_disk")

    def test_blocks_dd_to_raw_device(self):
        res = check_command("dd if=/dev/zero of=/dev/sda bs=1M")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "raw_disk")

        res2 = check_command("dd if=/dev/urandom of=/dev/nvme0n1")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "raw_disk")

    def test_allows_safe_dd_to_file(self):
        self.assertIsNone(check_command("dd if=/dev/zero of=output.bin bs=1M count=5"))

    def test_blocks_fork_bomb(self):
        res = check_command(":(){ :|:& };:")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "fork_bomb")

    def test_blocks_while_fork(self):
        res = check_command("while true; do bash & done")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "fork_bomb")

    def test_blocks_shutdown_and_reboot(self):
        res = check_command("shutdown -h now")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "system_state")

        res2 = check_command("reboot")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "system_state")

    def test_blocks_init_0(self):
        res = check_command("init 0")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "system_state")

    def test_blocks_chmod_root(self):
        res = check_command("chmod -R 777 /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "perm_wipe")


class TestCompoundAndEvasionChecker(unittest.TestCase):
    """Tests for compound commands, subshells, and wrapper evasions."""

    def test_blocks_chained_and(self):
        res = check_command("git status && rm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_chained_or(self):
        res = check_command("git pull || rm -rf /")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_chained_semicolon(self):
        res = check_command("echo hello ; DROP TABLE users;")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "drop_table")

    def test_blocks_chained_pipe(self):
        res = check_command("cat /dev/zero | dd if=/dev/zero of=/dev/sda")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "raw_disk")

    def test_blocks_subshell_dollar_paren(self):
        res = check_command("echo $(rm -rf /)")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_subshell_backtick(self):
        res = check_command("echo `rm -rf /`")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_blocks_bash_c_nested(self):
        res = check_command('bash -c "rm -rf /"')
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "rm_rf")

    def test_allows_text_echo(self):
        self.assertIsNone(check_command("echo 'rm -rf /' > notes.txt"))
        self.assertIsNone(check_command("echo 'DROP TABLE users;'"))

    def test_allows_grep_search(self):
        self.assertIsNone(check_command("grep -rn 'rm -rf' src/"))
        self.assertIsNone(check_command("grep 'DROP TABLE' schema.sql"))


if __name__ == "__main__":
    unittest.main()
