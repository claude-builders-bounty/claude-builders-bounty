#!/usr/bin/env python3
"""Test suite for safety_hook.py"""
import sys
import os
import json
import tempfile

# Add current directory to path
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
        assert expected_reason in reason, f"Expected '{expected_reason}' got '{reason}' for: {cmd}"
        passed += 1
    print(f"  test_blocked_commands: {passed}/{len(blocked)} passed")
    return passed


def test_allowed_commands():
    """Commands that should pass through."""
    allowed = [
        "rm -rf /tmp/scratch",
        "rm -rf node_modules/",
        "rm -rf /var/tmp/build_cache",
        "rm -rf test_output/",
        "DELETE FROM users WHERE id = 5;",
        "git push origin main",
        "ls -la",
        "pip install requests",
    ]
    passed = 0
    for cmd in allowed:
        is_blocked, reason = safety_hook.check_command(cmd)
        assert not is_blocked, f"Should allow: {cmd} (blocked as: {reason})"
        passed += 1
    print(f"  test_allowed_commands: {passed}/{len(allowed)} passed")
    return passed


def test_logging():
    """Test that blocked commands are logged."""
    tmp = os.path.join(tempfile.gettempdir(), "test_hook_log.jsonl")
    original_log = safety_hook.LOG_FILE
    safety_hook.LOG_FILE = tmp
    try:
        safety_hook.log_blocked("rm -rf /", "recursive force delete")
        assert os.path.exists(tmp), "Log file should be created"
        with open(tmp) as f:
            entry = json.loads(f.readline())
        assert entry["reason"] == "recursive force delete"
        assert "rm -rf /" in entry["cmd"]
        passed = 1
    finally:
        safety_hook.LOG_FILE = original_log
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"  test_logging: {passed}/1 passed")
    return passed


if __name__ == "__main__":
    print("Running safety_hook tests...")
    total = 0
    total += test_blocked_commands()
    total += test_allowed_commands()
    total += test_logging()
    print(f"\nAll tests passed: {total}/{total}")
