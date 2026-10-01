#!/usr/bin/env python3
"""Tests for the pre-tool-use destructive command hook."""

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "hook.py")


def run_hook(command_str, cwd=None):
    """Run hook.py with a command and return the parsed result."""
    input_data = json.dumps({"input": {"command": command_str, "cwd": cwd or "/tmp/test"}})
    result = subprocess.run(
        [sys.executable, HOOK],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_allows_safe_commands():
    r = run_hook("ls -la")
    assert r["allowed"] is True, f"ls should be allowed: {r}"

    r = run_hook("git status")
    assert r["allowed"] is True, f"git status should be allowed: {r}"

    r = run_hook("echo hello")
    assert r["allowed"] is True, f"echo should be allowed: {r}"

    r = run_hook("python script.py")
    assert r["allowed"] is True, f"python should be allowed: {r}"
    print("PASS: safe commands allowed")


def test_blocks_rm_rf():
    for cmd in ["rm -rf /", "rm -rf /tmp/foo", "rm --recursive --force /"]:
        r = run_hook(cmd)
        assert r["allowed"] is False, f"rm -rf should be blocked: {cmd} -> {r}"
        assert "rm" in r.get("message", "").lower()
    print("PASS: rm -rf blocked")


def test_blocks_drop_table():
    r = run_hook("DROP TABLE users")
    assert r["allowed"] is False
    assert "drop table" in r["message"].lower()
    print("PASS: DROP TABLE blocked")


def test_blocks_git_push_force():
    for cmd in ["git push --force", "git push -f", "git push origin main --force"]:
        r = run_hook(cmd)
        assert r["allowed"] is False, f"git push --force should be blocked: {cmd}"
    print("PASS: git push --force blocked")


def test_blocks_truncate():
    r = run_hook("TRUNCATE TABLE users")
    assert r["allowed"] is False
    print("PASS: TRUNCATE blocked")


def test_allows_delete_with_where():
    r = run_hook("DELETE FROM users WHERE id = 1")
    assert r["allowed"] is True, f"DELETE with WHERE should be allowed: {r}"
    print("PASS: DELETE FROM with WHERE allowed")


def test_blocks_delete_without_where():
    r = run_hook("DELETE FROM users")
    assert r["allowed"] is False, f"DELETE without WHERE should be blocked: {r}"
    print("PASS: DELETE FROM without WHERE blocked")


def test_logs_blocked_attempts():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_path = f.name

    # Temporarily override the log path by patching via env or monkeypatching
    # Instead, run the hook and check the default log file exists afterward
    original_log = os.path.expanduser("~/.claude/hooks/blocked.log")

    # Clean up first
    if os.path.exists(original_log):
        os.remove(original_log)

    run_hook("rm -rf /")

    assert os.path.exists(original_log), "blocked.log should be created"
    with open(original_log) as f:
        content = f.read()
    assert "rm -rf" in content, f"Log should contain blocked command: {content}"
    assert "timestamp" in content.lower() or "T" in content  # ISO timestamp

    # Clean up
    os.remove(original_log)
    print("PASS: blocked attempts logged")


def test_message_explains_why():
    r = run_hook("rm -rf /")
    assert "message" in r, "Blocked response should include message"
    assert len(r["message"]) > 10, "Message should explain why blocked"
    print("PASS: block message explains reason")


if __name__ == "__main__":
    test_allows_safe_commands()
    test_blocks_rm_rf()
    test_blocks_drop_table()
    test_blocks_git_push_force()
    test_blocks_truncate()
    test_allows_delete_with_where()
    test_blocks_delete_without_where()
    test_logs_blocked_attempts()
    test_message_explains_why()
    print("\nAll tests passed!")
