#!/usr/bin/env python3
"""Tests for pre-tool-use-block-destructive hook."""
import json
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "pre-tool-use-block-destructive.py")


def run_hook(command: str, tool_name: str = "Bash") -> tuple[int, str]:
    """Run the hook with given command, return (exit_code, stdout)."""
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command}
    })
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.returncode, result.stdout


class TestBlockedCommands:
    """Commands that MUST be blocked."""

    def test_rm_rf(self):
        code, _ = run_hook("rm -rf /")
        assert code == 2, "rm -rf / should be blocked"

    def test_rm_rf_home(self):
        code, _ = run_hook("rm -rf ~")
        assert code == 2, "rm -rf ~ should be blocked"

    def test_rm_force_recursive(self):
        code, _ = run_hook("rm -fr /var/log")
        assert code == 2, "rm -fr should be blocked"

    def test_drop_table(self):
        code, _ = run_hook("echo 'DROP TABLE users' | mysql")
        assert code == 2, "DROP TABLE should be blocked"

    def test_truncate(self):
        code, _ = run_hook("echo 'TRUNCATE users' | mysql")
        assert code == 2, "TRUNCATE should be blocked"

    def test_delete_no_where(self):
        code, _ = run_hook("echo 'DELETE FROM users' | mysql")
        assert code == 2, "DELETE FROM without WHERE should be blocked"

    def test_git_push_force(self):
        code, _ = run_hook("git push --force origin main")
        assert code == 2, "git push --force should be blocked"

    def test_git_push_f(self):
        code, _ = run_hook("git push -f origin main")
        assert code == 2, "git push -f should be blocked"

    def test_git_reset_hard(self):
        code, _ = run_hook("git reset --hard HEAD~1")
        assert code == 2, "git reset --hard should be blocked"

    def test_git_clean_force(self):
        code, _ = run_hook("git clean -fdx")
        assert code == 2, "git clean -f should be blocked"

    def test_chmod_777(self):
        code, _ = run_hook("chmod 777 /etc/passwd")
        assert code == 2, "chmod 777 should be blocked"

    def test_mkfs(self):
        code, _ = run_hook("mkfs.ext4 /dev/sda1")
        assert code == 2, "mkfs should be blocked"

    def test_dd_device(self):
        code, _ = run_hook("dd if=/dev/zero of=/dev/sda")
        assert code == 2, "dd to device should be blocked"

    def test_shutdown(self):
        code, _ = run_hook("shutdown -h now")
        assert code == 2, "shutdown should be blocked"

    def test_killall(self):
        code, _ = run_hook("killall python")
        assert code == 2, "killall should be blocked"

    def test_iptables_flush(self):
        code, _ = run_hook("iptables -F")
        assert code == 2, "iptables flush should be blocked"

    def test_overwrite_etc_passwd(self):
        code, _ = run_hook("echo '' > /etc/passwd")
        assert code == 2, "overwriting /etc/passwd should be blocked"

    def test_fork_bomb(self):
        code, _ = run_hook(":(){ :|:& };:")
        assert code == 2, "fork bomb should be blocked"

    def test_shred(self):
        code, _ = run_hook("shred /etc/shadow")
        assert code == 2, "shred should be blocked"

    def test_git_checkout_dot(self):
        code, _ = run_hook("git checkout -- .")
        assert code == 2, "git checkout -- . should be blocked"


class TestAllowedCommands:
    """Commands that should NOT be blocked."""

    def test_ls(self):
        code, _ = run_hook("ls -la")
        assert code == 0, "ls should be allowed"

    def test_git_status(self):
        code, _ = run_hook("git status")
        assert code == 0, "git status should be allowed"

    def test_git_push_normal(self):
        code, _ = run_hook("git push origin main")
        assert code == 0, "git push should be allowed"

    def test_pip_install(self):
        code, _ = run_hook("pip install requests")
        assert code == 0, "pip install should be allowed"

    def test_rm_single_file(self):
        code, _ = run_hook("rm test.log")
        assert code == 0, "rm single file should be allowed"

    def test_rm_temp_files(self):
        code, _ = run_hook("rm -rf *.log")
        assert code == 0, "rm *.log should be allowed"

    def test_rm_node_modules(self):
        code, _ = run_hook("rm -rf node_modules")
        assert code == 0, "rm -rf node_modules should be allowed"

    def test_rm_tmp(self):
        code, _ = run_hook("rm -rf /tmp/build")
        assert code == 0, "rm -rf /tmp should be allowed"

    def test_git_push_force_with_lease(self):
        code, _ = run_hook("git push --force-with-lease origin main")
        assert code == 0, "git push --force-with-lease should be allowed"

    def test_delete_with_where(self):
        code, _ = run_hook("echo 'DELETE FROM users WHERE id=1' | mysql")
        assert code == 0, "DELETE FROM with WHERE should be allowed"

    def test_echo(self):
        code, _ = run_hook("echo hello world")
        assert code == 0, "echo should be allowed"

    def test_python(self):
        code, _ = run_hook("python --version")
        assert code == 0, "python should be allowed"

    def test_non_bash_tool(self):
        code, _ = run_hook("rm -rf /", tool_name="Read")
        assert code == 0, "non-Bash tools should be allowed"


class TestBypassAttempts:
    """Known bypass vectors that should still be blocked."""

    def test_rm_dash_dash(self):
        code, _ = run_hook("rm -rf -- /")
        assert code == 2, "rm -rf -- / bypass should be blocked"

    def test_drop_comment(self):
        code, _ = run_hook("DROP/*comment*/TABLE users")
        assert code == 2, "DROP with comment bypass should be blocked"

    def test_mixed_case(self):
        code, _ = run_hook("RM -RF /")
        assert code == 2, "mixed case rm should be blocked"

    def test_extra_flags(self):
        code, _ = run_hook("rm -rfv /")
        assert code == 2, "rm with extra flags should be blocked"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
