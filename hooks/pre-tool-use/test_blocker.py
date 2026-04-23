#!/usr/bin/env python3
"""
Test suite for destructive command blocker
"""
import json
import subprocess
import sys

def test_command(command, should_block=True):
    """Test if a command is correctly blocked or allowed"""
    request = {
        "tool": {
            "name": "Bash",
            "input": {
                "command": command
            }
        },
        "context": {
            "cwd": "/tmp/test"
        }
    }

    try:
        result = subprocess.run(
            ['python3', 'pre-tool-use.py'],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5
        )

        blocked = result.returncode == 1

        status = "✓" if blocked == should_block else "✗"
        expected = "BLOCKED" if should_block else "ALLOWED"
        actual = "BLOCKED" if blocked else "ALLOWED"

        print(f"{status} {command[:60]:<60} | Expected: {expected:<8} | Actual: {actual}")

        if blocked != should_block:
            print(f"  ERROR: Expected {expected} but got {actual}")
            if result.stderr:
                print(f"  STDERR: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"✗ {command[:60]:<60} | ERROR: {e}")
        return False

def main():
    print("\nTesting Destructive Command Blocker")
    print("=" * 100)

    tests_passed = 0
    tests_failed = 0

    print("\n🚫 Commands that SHOULD be blocked:\n")

    dangerous_commands = [
        ("rm -rf /tmp/test", True),
        ("rm -rf node_modules", True),
        ("rm -rf *", True),
        ("DROP TABLE users", True),
        ("TRUNCATE TABLE logs", True),
        ("DELETE FROM users;", True),
        ("DELETE FROM users", True),
        ("git push --force origin main", True),
        ("git push -f origin main", True),
        ("mkfs.ext4 /dev/sda1", True),
        ("dd if=/dev/zero of=/dev/sda", True),
    ]

    for cmd, should_block in dangerous_commands:
        if test_command(cmd, should_block):
            tests_passed += 1
        else:
            tests_failed += 1

    print("\n✅ Commands that SHOULD be allowed:\n")

    safe_commands = [
        ("rm file.txt", False),
        ("rm -r old-folder", False),
        ("git push origin main", False),
        ("DELETE FROM users WHERE id=5", False),
        ("DROP INDEX idx_name", False),
        ("ls -la", False),
        ("echo 'test'", False),
        ("npm install", False),
    ]

    for cmd, should_block in safe_commands:
        if test_command(cmd, should_block):
            tests_passed += 1
        else:
            tests_failed += 1

    print("\n" + "=" * 100)
    print(f"\nResults: {tests_passed} passed, {tests_failed} failed")

    if tests_failed > 0:
        print("\n❌ Some tests failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
