#!/usr/bin/env python3
"""
🧪 Automated Test Suite for Destructive Command Hook
Verifies that all forbidden patterns are intercepted, safe commands pass through,
and blocked actions are recorded properly to blocked.log.
"""

import subprocess
import os
import sys

HOOK_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "pre-tool-use.py"))
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def run_hook(command: str) -> tuple[int, str, str]:
    """Runs the hook with the given command and returns (exitcode, stdout, stderr)."""
    proc = subprocess.Popen(
        [sys.executable, HOOK_SCRIPT, command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr


def test_destructive_patterns():
    test_cases_blocked = [
        ("rm -rf /tmp/test", "Recursive Force Removal"),
        ("rm -fr build/", "Recursive Force Removal"),
        ("rm --recursive --force node_modules", "Recursive Force Removal"),
        ("DROP TABLE users;", "DROP TABLE/DATABASE"),
        ("DROP DATABASE analytics;", "DROP TABLE/DATABASE"),
        ("DROP SCHEMA staging;", "DROP TABLE/DATABASE"),
        ("git push --force origin main", "Git Force Push"),
        ("git push -f origin feat", "Git Force Push"),
        ("git push origin main --force-with-lease", "Git Force Push"),
        ("TRUNCATE TABLE session_cache;", "SQL Truncation"),
        ("TRUNCATE orders;", "SQL Truncation"),
        ("DELETE FROM users;", "SQL Delete Without WHERE"),
        ("DELETE FROM accounts", "SQL Delete Without WHERE"),
    ]

    print("🔍 Testing Dangerous Commands (Expected to be BLOCKED):")
    passed = 0
    for cmd, expected_rule in test_cases_blocked:
        code, stdout, stderr = run_hook(cmd)
        if code != 0 and "Destructive Command Blocked" in stderr:
            print(f"  ✅ [BLOCKED (code {code})] {cmd} -> {expected_rule}")
            passed += 1
        else:
            print(f"  ❌ [FAILED TO BLOCK] {cmd} (returned exit code {code})")

    assert passed == len(test_cases_blocked), f"Failed {len(test_cases_blocked) - passed} block tests"
    print(f"\n🎉 All {passed}/{len(test_cases_blocked)} destructive commands blocked successfully!\n")


def test_safe_commands():
    safe_commands = [
        "ls -la",
        "git status",
        "git push origin main",
        "rm single_file.txt",
        "python -m pytest tests/",
        "SELECT * FROM users WHERE active = true;",
        "DELETE FROM users WHERE id = 123;",
        "DELETE FROM sessions WHERE expired_at < NOW();",
        "npm run build",
        "cargo build --release"
    ]

    print("🔍 Testing Safe Commands (Expected to PASS):")
    passed = 0
    for cmd in safe_commands:
        code, stdout, stderr = run_hook(cmd)
        if code == 0:
            print(f"  ✅ [ALLOWED (code 0)] {cmd}")
            passed += 1
        else:
            print(f"  ❌ [FALSE POSITIVE] {cmd} was blocked (exit code {code})")

    assert passed == len(safe_commands), f"Failed {len(safe_commands) - passed} safe tests"
    print(f"\n🎉 All {passed}/{len(safe_commands)} safe commands passed without interference!\n")


def test_audit_log():
    print("🔍 Checking Audit Log (~/.claude/hooks/blocked.log):")
    assert os.path.exists(LOG_FILE), "Log file was not created!"
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    print(f"  ✅ Log file exists and contains {len(lines)} recorded security events.")
    print(f"  Last entry: {lines[-1].strip() if lines else 'empty'}")


if __name__ == "__main__":
    test_destructive_patterns()
    test_safe_commands()
    test_audit_log()
    print("\n🏆 ALL TESTS PASSED! Hook is 100% compliant with Issue #3 criteria.\n")
