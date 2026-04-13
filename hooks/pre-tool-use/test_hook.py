#!/usr/bin/env python3
"""
Test suite for the pre-tool-use safety hook.

Run:  python3 test_hook.py
Requires Python 3.10+ (for type hints with |)
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "hook.py"


def run_hook(command: str, tool: str = "bash") -> dict:
    """Run the hook with a simulated command and return parsed JSON."""
    input_data = json.dumps({"tool": tool, "args": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def run_hook_raw(input_str: str) -> dict:
    """Run the hook with raw stdin input."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=input_str,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


# ─── Blocked command tests ──────────────────────────────────────────────────

def test_blocks_rm_rf_root():
    assert run_hook("rm -rf /")["allow"] is False
    assert run_hook("sudo rm -rf /")["allow"] is False


def test_blocks_rm_rf_home():
    assert run_hook("rm -rf ~")["allow"] is False
    assert run_hook("rm -rf ~/Documents")["allow"] is False


def test_blocks_rm_rf_wildcard():
    assert run_hook("rm -rf *")["allow"] is False
    assert run_hook("rm -rf .")["allow"] is False


def test_blocks_rm_rf_system_dirs():
    assert run_hook("rm -rf /etc")["allow"] is False
    assert run_hook("rm -rf /home")["allow"] is False
    assert run_hook("rm -rf /usr/local")["allow"] is False
    assert run_hook("rm -rf /var")["allow"] is False
    assert run_hook("rm -rf /boot")["allow"] is False


def test_blocks_sql_destructive():
    assert run_hook("DROP TABLE users")["allow"] is False
    assert run_hook("drop database prod")["allow"] is False
    assert run_hook("TRUNCATE TABLE logs")["allow"] is False
    assert run_hook("DELETE FROM users;")["allow"] is False
    assert run_hook("DELETE FROM users WHERE 1=1")["allow"] is False


def test_blocks_git_force():
    assert run_hook("git push --force origin main")["allow"] is False
    assert run_hook("git push -f origin main")["allow"] is False
    assert run_hook("git push origin -f")["allow"] is False
    assert run_hook("git reset --hard HEAD~5")["allow"] is False


def test_blocks_disk_ops():
    assert run_hook("dd if=/dev/zero of=/dev/sda")["allow"] is False
    assert run_hook("mkfs.ext4 /dev/sdb1")["allow"] is False
    assert run_hook("fdisk /dev/sda")["allow"] is False
    assert run_hook("shred -vfz -n 3 /dev/sda")["allow"] is False


def test_blocks_firewall():
    assert run_hook("iptables -F")["allow"] is False
    assert run_hook("ufw disable")["allow"] is False


def test_blocks_fork_bomb():
    assert run_hook(":(){ :|:& };:")["allow"] is False


def test_blocks_chmod_chown():
    assert run_hook("chmod 777 /etc/passwd")["allow"] is False
    assert run_hook("chown user:user -R /")["allow"] is False


def test_blocks_kill_init():
    assert run_hook("kill -9 1")["allow"] is False
    assert run_hook("killall -9 sshd")["allow"] is False


def test_case_insensitive():
    assert run_hook("DROP TABLE users")["allow"] is False
    assert run_hook("drop table users")["allow"] is False
    assert run_hook("Drop Table Users")["allow"] is False
    assert run_hook("RM -RF /")["allow"] is False


# ─── Allowed command tests ──────────────────────────────────────────────────

def test_allows_normal_commands():
    assert run_hook("ls -la")["allow"] is True
    assert run_hook("git status")["allow"] is True
    assert run_hook("npm install")["allow"] is True
    assert run_hook("python main.py")["allow"] is True
    assert run_hook("rm file.txt")["allow"] is True
    assert run_hook("cat /etc/hosts")["allow"] is True
    assert run_hook("echo hello")["allow"] is True
    assert run_hook("git push origin main")["allow"] is True


def test_allows_rm_rf_tmp():
    """rm -rf on /tmp is allowed — it's a common dev workflow."""
    assert run_hook("rm -rf /tmp/my-work-dir")["allow"] is True
    assert run_hook("rm -rf /tmp/build-output")["allow"] is True


def test_allows_delete_with_where():
    """DELETE with a specific WHERE clause is allowed."""
    assert run_hook("DELETE FROM users WHERE id = 5")["allow"] is True
    assert run_hook("delete from sessions where expired = true")["allow"] is True


def test_allows_non_bash_tool():
    result = run_hook_raw(json.dumps({"tool": "read_file", "args": {"path": "test.py"}}))
    assert result["allow"] is True


def test_allows_empty_input():
    result = run_hook_raw("")
    assert result["allow"] is True


def test_allows_invalid_json():
    result = run_hook_raw("not json at all")
    assert result["allow"] is True


def test_blocked_message_is_helpful():
    result = run_hook("rm -rf /")
    reason = result.get("reason", "")
    assert "BLOCKED" in reason
    assert "Command:" in reason
    assert "pre-tool-use" in reason.lower() or "blocked" in reason.lower()


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import inspect

    passed = failed = skipped = 0
    errors = []

    tests = sorted(
        (name, obj) for name, obj in globals().items()
        if name.startswith("test_") and inspect.isfunction(obj)
    )

    for name, func in tests:
        try:
            func()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
            errors.append((name, e))

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for name, e in errors:
            print(f"  {name}: {e}")
    sys.exit(1 if failed else 0)
