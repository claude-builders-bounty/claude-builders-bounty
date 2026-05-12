#!/usr/bin/env python3
"""Tests for the block-destructive-commands hook."""

import json
import os
import sys
import tempfile

# Add parent dir to path for import
sys.path.insert(0, os.path.dirname(__file__))
from block_destructive import check_command


def test_blocked_commands():
    """Test that known destructive commands are blocked."""
    blocked_cases = [
        ("rm -rf /", "rm -rf"),
        ("rm -rf /home/user", "rm -rf"),
        ("rm -fr /tmp/data", "rm -rf"),
        ("sudo rm -rf --no-preserve-root /", "rm -rf"),
        ("DROP TABLE users", "DROP TABLE"),
        ("drop table orders;", "DROP TABLE"),
        ("DROP DATABASE production", "DROP"),
        ("DROP SCHEMA public", "DROP"),
        ("git push --force origin main", "git push --force"),
        ("git push -f origin main", "git push --force"),
        ("git push origin main --force", "git push --force"),
        ("TRUNCATE users", "TRUNCATE"),
        ("TRUNCATE TABLE orders", "TRUNCATE"),
        ("truncate table logs", "TRUNCATE"),
        ("DELETE FROM users;", "DELETE FROM without WHERE"),
        ("DELETE FROM orders", "DELETE FROM without WHERE"),
        ("mkfs.ext4 /dev/sda1", "mkfs"),
        ("dd if=/dev/zero of=/dev/sda", "dd writing to device"),
    ]

    passed = 0
    failed = 0

    for command, expected_desc_fragment in blocked_cases:
        is_blocked, description, severity = check_command(command)
        if is_blocked:
            passed += 1
            print(f"  ✅ BLOCKED: {command!r} → {description}")
        else:
            failed += 1
            print(f"  ❌ MISSED:  {command!r} (expected to match '{expected_desc_fragment}')")

    return passed, failed


def test_allowed_commands():
    """Test that safe commands are NOT blocked."""
    allowed_cases = [
        "ls -la",
        "cat file.txt",
        "echo hello",
        "git push origin main",
        "git commit -m 'fix bug'",
        "rm file.txt",
        "rm -f single_file.txt",
        "python3 manage.py migrate",
        "npm install",
        "SELECT * FROM users WHERE id = 1",
        "DELETE FROM users WHERE id = 42;",
        "INSERT INTO users VALUES (1, 'test')",
        "UPDATE users SET name = 'new' WHERE id = 1",
        "docker compose up -d",
        "pip install requests",
    ]

    passed = 0
    failed = 0

    for command in allowed_cases:
        is_blocked, description, severity = check_command(command)
        if not is_blocked:
            passed += 1
            print(f"  ✅ ALLOWED: {command!r}")
        else:
            failed += 1
            print(f"  ❌ FALSE POSITIVE: {command!r} → blocked as {description}")

    return passed, failed


def test_stdin_integration():
    """Test the full stdin/stdout flow of the hook."""
    import subprocess

    hook_script = os.path.join(os.path.dirname(__file__), "block_destructive.py")

    # Test a blocked command
    input_data = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"},
    })
    result = subprocess.run(
        [sys.executable, hook_script],
        input=input_data,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    if output:
        response = json.loads(output)
        assert response["decision"] == "block", f"Expected block, got {response}"
        print("  ✅ stdin/stdout: blocked rm -rf correctly")
    else:
        print("  ❌ stdin/stdout: expected block output for rm -rf")

    # Test an allowed command
    input_data = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
    })
    result = subprocess.run(
        [sys.executable, hook_script],
        input=input_data,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    if not output:
        print("  ✅ stdin/stdout: allowed ls -la correctly (no output)")
    else:
        print(f"  ❌ stdin/stdout: expected no output for ls -la, got: {output}")

    # Test non-bash tool (should be allowed)
    input_data = json.dumps({
        "tool_name": "FileWrite",
        "tool_input": {"path": "/tmp/test.txt", "content": "hello"},
    })
    result = subprocess.run(
        [sys.executable, hook_script],
        input=input_data,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    if not output:
        print("  ✅ stdin/stdout: ignored non-bash tool correctly")
    else:
        print(f"  ❌ stdin/stdout: expected no output for non-bash tool, got: {output}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing block-destructive-commands hook")
    print("=" * 60)

    print("\n📋 Test 1: Destructive commands should be BLOCKED")
    print("-" * 50)
    blocked_pass, blocked_fail = test_blocked_commands()

    print(f"\n📋 Test 2: Safe commands should be ALLOWED")
    print("-" * 50)
    allowed_pass, allowed_fail = test_allowed_commands()

    print(f"\n📋 Test 3: stdin/stdout integration")
    print("-" * 50)
    test_stdin_integration()

    total_pass = blocked_pass + allowed_pass
    total_fail = blocked_fail + allowed_fail

    print("\n" + "=" * 60)
    print(f"Results: {total_pass} passed, {total_fail} failed")
    print("=" * 60)

    if total_fail > 0:
        sys.exit(1)
