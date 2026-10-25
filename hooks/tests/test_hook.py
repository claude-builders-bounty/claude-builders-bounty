#!/usr/bin/env python3
"""
Unit and Integration Tests for Claude Code Pre-Tool-Use Security Hook
Validates all acceptance criteria for Bounty #3.
"""

import sys
import os
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

HOOK_PATH = Path(__file__).parent.parent / "pre-tool-use.py"

BLOCKED_TEST_CASES = [
    # rm -rf variants
    "rm -rf /var/data",
    "rm -fr ./temp",
    "rm -r -f build/",
    "rm -f -r cache/",
    "rm --recursive --force dist/",
    # git push force variants
    "git push origin main --force",
    "git push -f origin feat",
    "git push --force-with-lease",  # also caught or blocked safely
    # SQL Drop
    "DROP TABLE users;",
    "drop table if exists orders;",
    "DROP DATABASE production;",
    # SQL Truncate
    "TRUNCATE TABLE sessions;",
    "truncate logs;",
    # SQL Delete without WHERE
    "DELETE FROM users;",
    "delete from accounts",
    "DELETE FROM cache\n",
]

ALLOWED_TEST_CASES = [
    "ls -la",
    "git status",
    "git push origin main",
    "git commit -m 'chore: remove old files'",
    "rm -f single_file.txt",
    "rm myfile.log",
    "DELETE FROM users WHERE id = 42;",
    "DELETE FROM orders WHERE created_at < '2024-01-01';",
    "SELECT * FROM users;",
    "npm run build",
    "python3 main.py",
]


def run_hook_cli(cmd):
    return subprocess.run(
        [sys.executable, str(HOOK_PATH), cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def run_hook_stdin_json(cmd):
    json_payload = f'{{"tool": "Bash", "tool_input": {{"command": "{cmd}"}}}}'
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json_payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def test_all():
    print("Testing Blocked Cases (CLI & JSON Stdin)...")
    blocked_failures = 0
    for cmd in BLOCKED_TEST_CASES:
        res = run_hook_cli(cmd)
        if res.returncode == 0:
            print(f"❌ FAIL: Expected blocked, but allowed: {cmd}")
            blocked_failures += 1
        else:
            print(f"✅ BLOCKED: {cmd}")

    print("\nTesting Allowed Cases (CLI)...")
    allowed_failures = 0
    for cmd in ALLOWED_TEST_CASES:
        res = run_hook_cli(cmd)
        if res.returncode != 0:
            print(f"❌ FAIL: Expected allowed, but blocked: {cmd}\n   Stderr: {res.stderr}")
            allowed_failures += 1
        else:
            print(f"✅ ALLOWED: {cmd}")

    print("\nTesting Claude Code JSON Stdin Format...")
    res_json_block = run_hook_stdin_json("rm -rf /")
    assert res_json_block.returncode == 1, "JSON Stdin rm -rf should be blocked"

    res_json_allow = run_hook_stdin_json("git status")
    assert res_json_allow.returncode == 0, "JSON Stdin git status should be allowed"

    print("\nTesting Log File Generation...")
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    assert log_file.exists(), "Blocked log file should exist"
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "rm -rf" in log_content, "rm -rf must be present in audit log"
    assert "Project Path:" in log_content, "Project path must be logged"

    print(f"\nAll tests finished. Blocked failures: {blocked_failures}, Allowed failures: {allowed_failures}")
    if blocked_failures == 0 and allowed_failures == 0:
        print("🎉 ALL TESTS PASSED! Hook is 100% compliant with acceptance criteria.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(test_all())
