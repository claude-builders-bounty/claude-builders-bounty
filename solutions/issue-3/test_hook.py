#!/usr/bin/env python3
"""
Test script for Claude Code Security Hook

This script tests the security hook by simulating various commands.
Run this to verify the hook is working correctly.
"""

import json
import sys
from pathlib import Path

# Add the hook directory to path
hook_dir = Path(__file__).parent
sys.path.insert(0, str(hook_dir))

from pre_tool_use import check_command, log_blocked_attempt

def test_safe_commands():
    """Test commands that should be allowed."""
    safe_commands = [
        "ls -la",
        "git status",
        "npm install",
        "python script.py",
        "cat file.txt",
        "echo 'Hello World'",
        "mkdir new-directory",
        "git commit -m 'Update'",
        "git push origin main",
    ]
    
    print("✅ Testing SAFE commands (should pass):\n")
    all_passed = True
    
    for cmd in safe_commands:
        is_safe, violations = check_command(cmd)
        status = "✓ PASS" if is_safe else "✗ FAIL"
        if not is_safe:
            all_passed = False
        print(f"  {status}: {cmd}")
        if not is_safe:
            for v in violations:
                print(f"         ❌ Blocked by: {v['name']}")
    
    return all_passed

def test_dangerous_commands():
    """Test commands that should be blocked."""
    dangerous_commands = [
        ("rm -rf /home/user", "rm -rf"),
        ("DROP TABLE users;", "DROP TABLE"),
        ("TRUNCATE TABLE logs;", "TRUNCATE"),
        ("DELETE FROM users;", "DELETE FROM"),
        ("git push --force origin main", "git push --force"),
        ("DROP DATABASE production;", "DROP DATABASE"),
    ]
    
    print("\n❌ Testing DANGEROUS commands (should be blocked):\n")
    all_blocked = True
    
    for cmd, expected_pattern in dangerous_commands:
        is_safe, violations = check_command(cmd)
        status = "✓ BLOCKED" if not is_safe else "✗ NOT BLOCKED"
        if is_safe:
            all_blocked = False
        print(f"  {status}: {cmd}")
        if not is_safe:
            for v in violations:
                print(f"         ❌ Reason: {v['reason']}")
        else:
            print(f"         ⚠️  Expected to be blocked by: {expected_pattern}")
    
    return all_blocked

def test_log_functionality():
    """Test logging functionality."""
    print("\n📝 Testing logging:\n")
    
    test_command = "rm -rf /test/path"
    is_safe, violations = check_command(test_command)
    
    if not is_safe:
        log_blocked_attempt(test_command, violations, "/test/project")
        print(f"  ✓ Log entry created for: {test_command}")
        print(f"  ✓ Log file: ~/.claude/hooks/blocked.log")
        return True
    else:
        print(f"  ✗ Failed to block test command")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("Claude Code Security Hook - Test Suite")
    print("=" * 70)
    print()
    
    results = []
    
    # Run tests
    results.append(("Safe Commands", test_safe_commands()))
    results.append(("Dangerous Commands", test_dangerous_commands()))
    results.append(("Logging", test_log_functionality()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
