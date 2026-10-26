#!/usr/bin/env python3
"""
Unit tests for pre_tool_use.py hook.
Tests dangerous commands (must be blocked) and safe commands (must be allowed).
"""

import subprocess
import sys
import json
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "pre_tool_use.py"

TEST_CASES = [
    # Blocked cases (Expected exit code 1)
    ("rm -rf /", 1, "Root rm -rf"),
    ("rm -rf ~", 1, "Home rm -rf"),
    ("git push origin main --force", 1, "Git force push"),
    ("git push -f origin feat", 1, "Git short force push"),
    ("DROP TABLE users;", 1, "SQL DROP TABLE"),
    ("DROP DATABASE production;", 1, "SQL DROP DATABASE"),
    ("TRUNCATE TABLE logs;", 1, "SQL TRUNCATE"),
    ("DELETE FROM customers;", 1, "SQL DELETE without WHERE"),
    (":(){ :|:& };:", 1, "Bash fork bomb"),
    ("git reset --hard HEAD~1", 1, "Git hard reset"),

    # Allowed cases (Expected exit code 0)
    ("git status", 0, "Git status"),
    ("git push origin main", 0, "Safe git push"),
    ("rm ./tmp/test.txt", 0, "Single file rm"),
    ("DELETE FROM users WHERE id = 5;", 0, "SQL DELETE with safe WHERE clause"),
    ("npm run build", 0, "Standard build command"),
    ("ls -la", 0, "Directory listing")
]

def run_test():
    passed = 0
    failed = 0
    print("=" * 65)
    print("[TEST] RUNNING PRE-TOOL-USE HOOK TEST SUITE")
    print("=" * 65)

    for cmd, expected_code, desc in TEST_CASES:
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT), payload],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode == expected_code:
            status = "[PASS]"
            passed += 1
        else:
            status = f"[FAIL] (Got {result.returncode}, Expected {expected_code})"
            failed += 1

        print(f"{status.ljust(8)} | {desc.ljust(35)} : {cmd}")

    print("=" * 65)
    print(f"Results: {passed} PASSED, {failed} FAILED")
    print("=" * 65)
    return failed == 0

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
