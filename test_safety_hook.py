#!/usr/bin/env python3
"""Test suite for safety_hook.py"""
import sys
import os
import json
import tempfile

# Add current file's directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import safety_hook


def test_blocked_commands():
    """Commands that should be blocked."""
    blocked = [
        ("rm -rf /", "recursive force delete"),
        ("rm -fr /home", "recursive force delete"),
        ("DROP TABLE users;", "SQL DROP TABLE"),
        ("drop table if exists foo", "SQL DROP TABLE"),
        ("git push origin --force", "force push to git"),
        ("git push --force-with-lease", "force push to git"),
        ("TRUNCATE TABLE logs;", "SQL TRUNCATE"),
        ("truncate users;", "SQL TRUNCATE"),
        ("DELETE FROM users;", "SQL DELETE without WHERE clause"),
        ("delete from sessions;", "SQL DELETE without WHERE clause"),
    ]
    passed = 0
    for cmd, expected_reason in blocked:
        is_blocked, reason = safety_hook.check_command(cmd)
        assert is_blocked, f"Should block: {cmd}"
        assert reason == expected_reason, f"Wrong reason for '{cmd}': got {reason}"
        passed += 1
    return passed


def test_allowed_commands():
    """Commands that should pass through."""
    allowed = [
        "ls -la",
        "pip install requests",
        "git push origin main",
        "git commit -m 'update'",
        "DELETE FROM users WHERE id = 1;",
        "delete from logs where created_at < '2024-01-01';",
        "rm -rf /tmp/test_output",
        "rm -rf node_modules",
        "rm single_file.txt",
        "echo hello world",
    ]
    passed = 0
    for cmd in allowed:
        is_blocked, reason = safety_hook.check_command(cmd)
        assert not is_blocked, f"Should allow: {cmd} (was blocked for: {reason})"
        passed += 1
    return passed


def test_logging():
    """Test that blocked commands get logged."""
    old_log = safety_hook.LOG_FILE
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as tmp:
            tmp_path = tmp.name
        safety_hook.LOG_FILE = tmp_path

        safety_hook.log_blocked("rm -rf /", "test")
        safety_hook.log_blocked("DROP TABLE x", "test2")

        with open(tmp_path) as f:
            lines = f.readlines()

        assert len(lines) == 2
        entry = json.loads(lines[0])
        assert entry["command"] == "rm -rf /"
        assert entry["reason"] == "test"
        assert "timestamp" in entry
        return 1
    finally:
        safety_hook.LOG_FILE = old_log
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_truncation():
    """Test that command truncation only adds ellipsis when needed."""
    short_cmd = "rm -rf /"
    long_cmd = "rm -rf " + "/very_long_path/" * 20

    # Short command should not have ellipsis
    is_blocked, reason = safety_hook.check_command(short_cmd)
    if is_blocked:
        assert "..." not in reason or len(short_cmd) > 80, \
            f"Short command should not have ellipsis in: {reason}"

    # Long command (when blocked) should have ellipsis in display
    is_blocked, reason = safety_hook.check_command(long_cmd)
    assert is_blocked, f"Should block long rm -rf command"
    return 1


if __name__ == "__main__":
    print("Running safety_hook tests...\n")

    total = 0

    passed = test_blocked_commands()
    total += passed
    print(f"  blocked commands: {passed}/{passed} PASS")

    passed = test_allowed_commands()
    total += passed
    print(f"  allowed commands: {passed}/{passed} PASS")

    passed = test_logging()
    total += passed
    print(f"  logging: {passed}/1 PASS")

    passed = test_truncation()
    total += passed
    print(f"  truncation: {passed}/1 PASS")

    print(f"\n{total} tests passed!")
