#!/usr/bin/env python3
"""
Test suite for Claude Code Pre-Tool-Use Security Hook
Verifies all forbidden patterns are blocked and safe commands are allowed.
"""

from block_destructive_commands import check_command

# Test cases that MUST be blocked
DANGEROUS_COMMANDS = [
    ("rm -rf /tmp/test", True),
    ("rm -r -f ./dist", True),
    ("rm -rf *", True),
    ("rm --recursive --force build/", True),
    ("DROP TABLE users;", True),
    ("drop table if exists orders;", True),
    ("git push --force origin main", True),
    ("git push -f", True),
    ("git push --force-with-lease origin feat", True),
    ("TRUNCATE TABLE accounts", True),
    ("truncate sessions;", True),
    ("DELETE FROM users;", True),
    ("delete from logs", True),
]

# Test cases that MUST be allowed (safe commands)
SAFE_COMMANDS = [
    ("ls -la", False),
    ("git status", False),
    ("git push origin main", False),
    ("rm file.txt", False),
    ("rm -r node_modules", False), # without -f
    ("SELECT * FROM users WHERE id = 1", False),
    ("DELETE FROM users WHERE id = 1;", False),
    ("delete from sessions where expires_at < now()", False),
    ("npm run build", False),
    ("pytest tests/", False),
]

def run_tests():
    passed = 0
    total = len(DANGEROUS_COMMANDS) + len(SAFE_COMMANDS)

    print("--- Testing Dangerous Commands (Expect BLOCKED) ---")
    for cmd, expected_blocked in DANGEROUS_COMMANDS:
        blocked, reason = check_command(cmd)
        if blocked == expected_blocked:
            print(f"[PASS] BLOCKED correctly: '{cmd}' -> {reason}")
            passed += 1
        else:
            print(f"[FAIL] FAILED to block: '{cmd}'")

    print("\n--- Testing Safe Commands (Expect ALLOWED) ---")
    for cmd, expected_blocked in SAFE_COMMANDS:
        blocked, reason = check_command(cmd)
        if blocked == expected_blocked:
            print(f"[PASS] ALLOWED correctly: '{cmd}'")
            passed += 1
        else:
            print(f"[FAIL] FALSE POSITIVE (blocked): '{cmd}'")

    print(f"\nResults: {passed}/{total} tests passed.")
    assert passed == total, "Some tests failed!"
    print("All security hook tests passed successfully!")

if __name__ == "__main__":
    run_tests()
