#!/usr/bin/env python3
"""
Comprehensive test suite for safety-hook.py

Run:
    python3 -m pytest test_safety_hook.py -v
    # or simply:
    python3 test_safety_hook.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "safety_hook", Path(__file__).resolve().parent / "safety-hook.py"
)
safety_hook = importlib.util.module_from_spec(_spec)
sys.modules["safety_hook"] = safety_hook
_spec.loader.exec_module(safety_hook)

SafetyHook = safety_hook.SafetyHook
normalise_command = safety_hook.normalise_command
extract_subcommands = safety_hook.extract_subcommands
EvalResult = safety_hook.EvalResult


@pytest.fixture(scope="module")
def hook() -> SafetyHook:
    """Return a SafetyHook loaded with the default config."""
    return SafetyHook()


# ============================================================================
#  BLOCKED - these commands MUST be blocked
# ============================================================================


class TestBlocked:
    """Commands that should be blocked (score >= threshold)."""

    # -- Filesystem destruction -----------------------------------------------

    def test_rm_rf_root(self, hook):
        r = hook.evaluate("rm -rf /")
        assert r.blocked, r.report()

    def test_rm_rf_root_sudo(self, hook):
        r = hook.evaluate("sudo rm -rf /")
        assert r.blocked, r.report()

    def test_rm_rf_root_no_preserve(self, hook):
        r = hook.evaluate("rm -rf --no-preserve-root /")
        assert r.blocked, r.report()

    def test_rm_rf_etc(self, hook):
        r = hook.evaluate("rm -rf /etc")
        assert r.blocked, r.report()

    def test_rm_rf_usr(self, hook):
        r = hook.evaluate("rm -rf /usr")
        assert r.blocked, r.report()

    def test_rm_rf_var(self, hook):
        r = hook.evaluate("rm -rf /var")
        assert r.blocked, r.report()

    def test_rm_fr_root(self, hook):
        """Flag order: -fr instead of -rf."""
        r = hook.evaluate("rm -fr /")
        assert r.blocked, r.report()

    # -- SQL destruction ------------------------------------------------------

    def test_drop_table(self, hook):
        r = hook.evaluate("mysql -e 'DROP TABLE users;'")
        assert r.blocked, r.report()

    def test_drop_database(self, hook):
        r = hook.evaluate("psql -c 'DROP DATABASE production;'")
        assert r.blocked, r.report()

    def test_truncate_table(self, hook):
        r = hook.evaluate("mysql -e 'TRUNCATE TABLE orders;'")
        assert r.blocked, r.report()

    def test_delete_no_where(self, hook):
        r = hook.evaluate("sqlite3 db.sqlite 'DELETE FROM users;'")
        assert r.blocked, r.report()

    # -- Git force-push -------------------------------------------------------

    def test_git_force_push_main(self, hook):
        r = hook.evaluate("git push --force origin main")
        assert r.blocked, r.report()

    def test_git_force_push_master(self, hook):
        r = hook.evaluate("git push --force origin master")
        assert r.blocked, r.report()

    def test_git_force_push_main_reversed(self, hook):
        r = hook.evaluate("git push origin main --force")
        assert r.blocked, r.report()

    # -- Permissions ----------------------------------------------------------

    def test_chmod_777_etc(self, hook):
        r = hook.evaluate("chmod 777 /etc")
        assert r.blocked, r.report()

    def test_chmod_777_root(self, hook):
        r = hook.evaluate("chmod 777 /")
        assert r.blocked, r.report()

    def test_chmod_recursive_777_usr(self, hook):
        r = hook.evaluate("chmod -R 777 /usr")
        assert r.blocked, r.report()

    # -- Disk destruction -----------------------------------------------------

    def test_mkfs(self, hook):
        r = hook.evaluate("mkfs.ext4 /dev/sda1")
        assert r.blocked, r.report()

    def test_mkfs_xfs(self, hook):
        r = hook.evaluate("mkfs.xfs /dev/nvme0n1p1")
        assert r.blocked, r.report()

    def test_dd_disk_write(self, hook):
        r = hook.evaluate("dd if=/dev/zero of=/dev/sda bs=1M")
        assert r.blocked, r.report()

    def test_dd_nvme(self, hook):
        r = hook.evaluate("dd if=/dev/urandom of=/dev/nvme0n1 bs=4k")
        assert r.blocked, r.report()

    # -- Shutdown / reboot ----------------------------------------------------

    def test_shutdown(self, hook):
        r = hook.evaluate("shutdown -h now")
        assert r.blocked, r.report()

    def test_reboot(self, hook):
        r = hook.evaluate("reboot")
        assert r.blocked, r.report()

    def test_poweroff(self, hook):
        r = hook.evaluate("poweroff")
        assert r.blocked, r.report()

    def test_halt(self, hook):
        r = hook.evaluate("halt")
        assert r.blocked, r.report()

    def test_init_0(self, hook):
        r = hook.evaluate("init 0")
        assert r.blocked, r.report()

    def test_systemctl_reboot(self, hook):
        r = hook.evaluate("systemctl reboot")
        assert r.blocked, r.report()

    # -- Process killing ------------------------------------------------------

    def test_kill_pid_1(self, hook):
        r = hook.evaluate("kill -9 1")
        assert r.blocked, r.report()

    def test_killall_sshd(self, hook):
        r = hook.evaluate("killall sshd")
        assert r.blocked, r.report()

    def test_pkill_systemd(self, hook):
        r = hook.evaluate("pkill systemd")
        assert r.blocked, r.report()

    def test_kill_all_processes(self, hook):
        r = hook.evaluate("kill -9 -1")
        assert r.blocked, r.report()

    # -- Fork bomb ------------------------------------------------------------

    def test_fork_bomb(self, hook):
        r = hook.evaluate(":(){ :|:& };")
        assert r.blocked, r.report()

    # -- Compound / chained ---------------------------------------------------

    def test_chained_rm(self, hook):
        r = hook.evaluate("echo hello && rm -rf /")
        assert r.blocked, r.report()

    def test_subshell_rm(self, hook):
        r = hook.evaluate("echo $(rm -rf /)")
        assert r.blocked, r.report()

    # -- Python destruction ---------------------------------------------------

    def test_python_rmtree_root(self, hook):
        r = hook.evaluate("""python3 -c "import shutil; shutil.rmtree('/');" """)
        assert r.blocked, r.report()

    def test_python_os_system_rm(self, hook):
        r = hook.evaluate("""python3 -c "import os; os.system('rm -rf /')" """)
        assert r.blocked, r.report()


# ============================================================================
#  ALLOWED - these commands MUST be allowed
# ============================================================================


class TestAllowed:
    """Commands that should be allowed (score < threshold)."""

    # -- Safe rm usage --------------------------------------------------------

    def test_rm_single_file(self, hook):
        r = hook.evaluate("rm myfile.txt")
        assert not r.blocked, r.report()

    def test_rm_rf_node_modules(self, hook):
        r = hook.evaluate("rm -rf node_modules")
        assert not r.blocked, r.report()

    def test_rm_rf_build_dir(self, hook):
        r = hook.evaluate("rm -rf ./build")
        assert not r.blocked, r.report()

    def test_rm_rf_dist(self, hook):
        r = hook.evaluate("rm -rf dist")
        assert not r.blocked, r.report()

    def test_rm_rf_pycache(self, hook):
        r = hook.evaluate("rm -rf __pycache__")
        assert not r.blocked, r.report()

    # -- Safe SQL -------------------------------------------------------------

    def test_drop_test_table(self, hook):
        r = hook.evaluate("psql -c 'DROP TABLE IF EXISTS test_users;'")
        assert not r.blocked, r.report()

    def test_drop_test_database(self, hook):
        r = hook.evaluate("psql -c 'DROP DATABASE test;'")
        assert not r.blocked, r.report()

    def test_select_query(self, hook):
        r = hook.evaluate("mysql -e 'SELECT * FROM users;'")
        assert not r.blocked, r.report()

    def test_delete_with_where(self, hook):
        r = hook.evaluate("""psql -c "DELETE FROM sessions WHERE expired = true;" """)
        assert not r.blocked, r.report()

    # -- Safe git -------------------------------------------------------------

    def test_git_push_normal(self, hook):
        r = hook.evaluate("git push origin main")
        assert not r.blocked, r.report()

    def test_git_force_push_feature(self, hook):
        r = hook.evaluate("git push --force origin feature/my-branch")
        assert not r.blocked, r.report()

    def test_git_commit(self, hook):
        r = hook.evaluate("git commit -m 'fix: update main module'")
        assert not r.blocked, r.report()

    # -- Safe permissions -----------------------------------------------------

    def test_chmod_755(self, hook):
        r = hook.evaluate("chmod 755 ./deploy.sh")
        assert not r.blocked, r.report()

    def test_chmod_644(self, hook):
        r = hook.evaluate("chmod 644 README.md")
        assert not r.blocked, r.report()

    # -- Safe disk commands ---------------------------------------------------

    def test_dd_file_copy(self, hook):
        r = hook.evaluate("dd if=input.img of=output.img bs=4M")
        assert not r.blocked, r.report()

    def test_mkfs_loopback(self, hook):
        r = hook.evaluate("mkfs.ext4 /dev/loop0")
        assert not r.blocked, r.report()

    # -- Everyday commands ----------------------------------------------------

    def test_ls(self, hook):
        r = hook.evaluate("ls -la")
        assert not r.blocked, r.report()

    def test_cat(self, hook):
        r = hook.evaluate("cat /etc/hostname")
        assert not r.blocked, r.report()

    def test_grep(self, hook):
        r = hook.evaluate("grep -r 'TODO' ./src")
        assert not r.blocked, r.report()

    def test_pip_install(self, hook):
        r = hook.evaluate("pip install requests")
        assert not r.blocked, r.report()

    def test_docker_run(self, hook):
        r = hook.evaluate("docker run -it ubuntu bash")
        assert not r.blocked, r.report()

    def test_make_build(self, hook):
        r = hook.evaluate("make && make install")
        assert not r.blocked, r.report()

    def test_npm_install(self, hook):
        r = hook.evaluate("npm install && npm run build")
        assert not r.blocked, r.report()

    def test_curl_download(self, hook):
        r = hook.evaluate("curl -o file.tar.gz https://example.com/release.tar.gz")
        assert not r.blocked, r.report()

    def test_kill_normal_process(self, hook):
        r = hook.evaluate("kill 12345")
        assert not r.blocked, r.report()

    def test_kill_9_normal_process(self, hook):
        r = hook.evaluate("kill -9 54321")
        assert not r.blocked, r.report()

    # -- Non-bash tool calls --------------------------------------------------

    def test_non_bash_tool_allowed(self, hook):
        r = hook.evaluate_tool_call({"tool": "read_file", "path": "/etc/passwd"})
        assert not r.blocked, r.report()


# ============================================================================
#  NORMALISATION
# ============================================================================


class TestNormalisation:
    """Verify command normalisation catches obfuscation."""

    def test_collapse_whitespace(self):
        assert normalise_command("rm   -rf   /") == "rm -rf /"

    def test_hex_decode(self):
        assert "rm" in normalise_command("\\x72\\x6d -rf /")

    def test_subcommand_extraction(self):
        parts = extract_subcommands("echo hi && rm -rf / || ls")
        assert any("rm" in p for p in parts)

    def test_subshell_extraction(self):
        parts = extract_subcommands("echo $(whoami)")
        assert any("whoami" in p for p in parts)


# ============================================================================
#  COMPOUND SCORING
# ============================================================================


class TestCompoundScoring:
    """Verify that compound modifiers increase the score."""

    def test_sudo_increases_score(self, hook):
        base = hook.evaluate("rm -rf /")
        elevated = hook.evaluate("sudo rm -rf /")
        assert elevated.total_score > base.total_score

    def test_no_preserve_root_increases_score(self, hook):
        base = hook.evaluate("rm -rf /etc")
        extra = hook.evaluate("rm -rf --no-preserve-root /etc")
        assert extra.total_score > base.total_score

    def test_output_suppression_increases_score(self, hook):
        base = hook.evaluate("rm -rf /etc")
        suppressed = hook.evaluate("rm -rf /etc 2>/dev/null")
        assert suppressed.total_score > base.total_score

    def test_modifiers_dont_fire_alone(self, hook):
        """Compound modifiers should NOT add score when no rule matches."""
        r = hook.evaluate("sudo ls")
        assert r.total_score == 0


# ============================================================================
#  RESULT API
# ============================================================================


class TestResultAPI:
    """Verify EvalResult helpers."""

    def test_verdict_blocked(self, hook):
        r = hook.evaluate("rm -rf /")
        assert r.verdict == "BLOCK"

    def test_verdict_allowed(self, hook):
        r = hook.evaluate("ls -la")
        assert r.verdict == "ALLOW"

    def test_to_dict(self, hook):
        r = hook.evaluate("rm -rf /")
        d = r.to_dict()
        assert d["blocked"] is True
        assert "rule_hits" in d

    def test_report_contains_command(self, hook):
        r = hook.evaluate("rm -rf /")
        assert "rm -rf /" in r.report()


# ============================================================================
#  CLI
# ============================================================================


class TestCLI:
    """Integration tests for the CLI entry-point."""

    _hook_path = str(Path(__file__).resolve().parent / "safety-hook.py")

    def test_cli_blocked(self):
        result = subprocess.run(
            [sys.executable, self._hook_path, "rm -rf /"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "BLOCK" in result.stdout

    def test_cli_allowed(self):
        result = subprocess.run(
            [sys.executable, self._hook_path, "ls -la"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "ALLOW" in result.stdout

    def test_cli_json_output(self):
        result = subprocess.run(
            [sys.executable, self._hook_path, "-j", "rm -rf /"],
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert data["blocked"] is True

    def test_cli_json_input(self):
        payload = json.dumps({"tool": "bash", "command": "rm -rf /"})
        result = subprocess.run(
            [sys.executable, self._hook_path, "--json", "-j"],
            input=payload, capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert data["blocked"] is True


# ============================================================================
#  EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Tricky inputs that probe boundary conditions."""

    def test_empty_string(self, hook):
        r = hook.evaluate("")
        assert not r.blocked

    def test_whitespace_only(self, hook):
        r = hook.evaluate("   \t\n  ")
        assert not r.blocked

    def test_comment_only(self, hook):
        r = hook.evaluate("# rm -rf /")
        # Comments still match patterns - the hook evaluates raw strings.
        # In tool-use payloads, comments are still executed by bash.
        assert isinstance(r, EvalResult)

    def test_multiline_command(self, hook):
        cmd = "echo start\nrm -rf /\necho end"
        r = hook.evaluate(cmd)
        assert r.blocked

    def test_very_long_command(self, hook):
        cmd = "echo " + "a" * 10_000 + " && rm -rf /"
        r = hook.evaluate(cmd)
        assert r.blocked

    def test_unicode_in_command(self, hook):
        r = hook.evaluate("echo '\U0001f389' && ls")
        assert not r.blocked


# -- Run with python3 directly -----------------------------------------------

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
