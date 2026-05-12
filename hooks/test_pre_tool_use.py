#!/usr/bin/env python3
"""Tests for the Claude Code destructive-command safety hook."""

import json
import os
import subprocess
import sys
import tempfile


HOOK_PATH = os.path.join(os.path.dirname(__file__), "pre_tool_use.py")


def run_hook(command: str, tool_name: str = "Bash") -> dict | None:
    """Run the hook with a simulated Claude Code tool invocation and return parsed JSON output, or None if allowed."""
    hook_input = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
    })
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=hook_input,
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    if result.returncode == 0 and stdout:
        return json.loads(stdout)
    return None


def test_safe_commands_are_allowed():
    """Normal, non-destructive commands must pass through."""
    safe_commands = [
        "ls -la",
        "echo hello world",
        "python3 script.py",
        "git status",
        "npm install",
        "cargo build",
        "mkdir new-folder",
        "cp file.txt backup.txt",
        "mv old new",
        "cat README.md",
        "grep pattern file.txt",
        "",
    ]
    for cmd in safe_commands:
        result = run_hook(cmd)
        assert result is None, f"Safe command was blocked: {cmd}"


def test_non_bash_tools_ignored():
    """Only Bash tool invocations are checked."""
    result = run_hook("rm -rf /", tool_name="Read")
    assert result is None, "Non-Bash tools should pass through"

    result = run_hook("rm -rf /", tool_name="Write")
    assert result is None, "Non-Bash tools should pass through"

    result = run_hook("rm -rf /", tool_name="Grep")
    assert result is None, "Non-Bash tools should pass through"


def test_rm_rf_blocked():
    """rm -rf variants must be blocked."""
    blocked = [
        "rm -rf /tmp/test",
        "rm -r -f /tmp/test",
        "rm -fr /tmp/test",
        "rm --no-preserve-root /",
        "sudo rm -rf /var/log",
        "rm -rf *",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"rm -rf should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_drop_table_blocked():
    """DROP TABLE must be blocked."""
    blocked = [
        "DROP TABLE users;",
        "echo 'DROP TABLE users' | psql",
        "mysql -e 'DROP TABLE orders'",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"DROP TABLE should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_drop_database_blocked():
    """DROP DATABASE must be blocked."""
    blocked = [
        "DROP DATABASE production;",
        "mysql -e 'DROP DATABASE testdb'",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"DROP DATABASE should be blocked: {cmd}"


def test_truncate_blocked():
    """TRUNCATE must be blocked."""
    blocked = [
        "TRUNCATE TABLE users;",
        "TRUNCATE users;",
        "echo 'TRUNCATE TABLE logs' | psql",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"TRUNCATE should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_delete_without_where_blocked():
    """DELETE FROM without WHERE must be blocked."""
    blocked = [
        "DELETE FROM users;",
        "DELETE FROM orders",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"DELETE FROM without WHERE should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_delete_with_where_allowed():
    """DELETE FROM with WHERE must be allowed."""
    allowed = [
        "DELETE FROM users WHERE id = 5;",
        "DELETE FROM orders WHERE status = 'cancelled'",
    ]
    for cmd in allowed:
        result = run_hook(cmd)
        assert result is None, f"DELETE FROM with WHERE should be allowed: {cmd}"


def test_git_push_force_blocked():
    """git push --force and -f must be blocked."""
    blocked = [
        "git push --force origin main",
        "git push -f origin main",
        "git push origin main --force",
        "git push --force-with-lease origin main",  # WARN but not BLOCK
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        # --force-with-lease is only warned, not blocked
        if "--force-with-lease" in cmd:
            assert result is None, f"force-with-lease should be allowed (warned only): {cmd}"
        else:
            assert result is not None, f"git push --force should be blocked: {cmd}"
            assert result["decision"] == "block"


def test_fork_bomb_blocked():
    """Fork bomb patterns must be blocked."""
    blocked = [
        ":(){ :|:& };:",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"Fork bomb should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_chmod_system_blocked():
    """chmod 777 on root-level paths must be blocked."""
    blocked = [
        "chmod 777 /",
        "chmod -R 777 /var/www",
        "chmod 777 /etc/passwd",
    ]
    for cmd in blocked:
        result = run_hook(cmd)
        assert result is not None, f"chmod 777 / should be blocked: {cmd}"
        assert result["decision"] == "block"


def test_chmod_safe_allowed():
    """chmod on non-root paths must be allowed."""
    allowed = [
        "chmod 755 script.sh",
        "chmod +x ./run.sh",
        "chmod 600 ~/.ssh/id_rsa",
    ]
    for cmd in allowed:
        result = run_hook(cmd)
        assert result is None, f"Safe chmod should be allowed: {cmd}"


def test_blocked_message_contains_command():
    """The blocked reason message should reference the original command."""
    result = run_hook("rm -rf /tmp/test")
    assert result is not None
    reason = result.get("reason", "")
    assert "/tmp/test" in reason or "rm" in reason.lower()


def test_empty_input_handled():
    """Hook must not crash on empty stdin."""
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input="",
        capture_output=True,
        text=True,
    )
    # Empty input should exit 0 (allow) without error
    assert result.returncode == 0


def test_invalid_json_handled():
    """Malformed JSON must not crash the hook."""
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input="not valid json {{{",
        capture_output=True,
        text=True,
    )
    # Invalid input should exit 0 (fail-safe: allow)
    assert result.returncode == 0


def test_blocked_command_logged():
    """Blocked commands must be written to blocked.log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override HOOKS_DIR for test — we can't easily mock it here,
        # so instead verify the log file was created in ~/.claude/hooks/
        log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
        # Remove stale log if it exists
        if os.path.exists(log_path):
            os.remove(log_path)

        run_hook("rm -rf /tmp/test")

        assert os.path.exists(log_path), "blocked.log should be created"
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["level"] == "BLOCK"
        assert "rm" in entry["command"].lower()


if __name__ == "__main__":
    # Run all tests
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
