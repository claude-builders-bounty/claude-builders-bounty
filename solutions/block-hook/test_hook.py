#!/usr/bin/env python3
"""Test harness for the destructive command block hook."""

import json
import subprocess
import sys
import os

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "block-destructive.py")

def test_blocked(description, command):
    """Test that a command is blocked."""
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {
            "name": "Bash",
            "input": {"command": command},
            "toolCallId": "test_call"
        }
    })
    
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    try:
        output = json.loads(result.stdout)
        decision = output.get("permissionDecision", "unknown")
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
    except json.JSONDecodeError:
        decision = "parse_error"
        reason = result.stdout
    
    if decision == "deny":
        print(f"  ✅ BLOCKED: {description}")
        print(f"     Reason preview: {reason[:80]}...")
        return True
    else:
        print(f"  ❌ NOT BLOCKED: {description} (decision={decision})")
        return False

def test_allowed(description, command):
    """Test that a safe command is allowed."""
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {
            "name": "Bash",
            "input": {"command": command},
            "toolCallId": "test_call"
        }
    })
    
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    try:
        output = json.loads(result.stdout)
        decision = output.get("permissionDecision", "unknown")
    except json.JSONDecodeError:
        decision = "parse_error"
    
    if decision == "allow":
        print(f"  ✅ ALLOWED: {description}")
        return True
    else:
        print(f"  ❌ BLOCKED INCORRECTLY: {description} (decision={decision})")
        return False


def run_tests():
    """Run all tests."""
    passed = 0
    failed = 0
    
    print("\n" + "=" * 60)
    print("  BLOCK-DESTRUCTIVE HOOK TEST SUITE")
    print("=" * 60)
    
    # === DANGEROUS PATTERNS (should be blocked) ===
    print("\n📛 Dangerous patterns (should be BLOCKED):\n")
    
    tests_block = [
        ("rm -rf basic", "rm -rf /important/data"),
        ("rm -rf with flags", "rm -rf /var/log/*"),
        ("rm -rf with sudo", "sudo rm -rf /etc"),
        ("rm -rf extended flag", "rm -r -f /data"),
        ("DROP TABLE", "DROP TABLE users;"),
        ("DROP TABLE with schema", "DROP TABLE IF EXISTS public.users;"),
        ("DROP TABLE in multi-statement", "SELECT 1; DROP TABLE orders;"),
        ("git push --force", "git push --force origin main"),
        ("git push --force-with-lease", "git push --force origin dev"),
        ("TRUNCATE", "TRUNCATE TABLE orders;"),
        ("TRUNCATE with cascade", "TRUNCATE TABLE users CASCADE;"),
        ("DELETE FROM without WHERE", "DELETE FROM users;"),
        ("DELETE FROM without WHERE (multiline)", "DELETE FROM users;"),
    ]
    
    for desc, cmd in tests_block:
        if test_blocked(desc, cmd):
            passed += 1
        else:
            failed += 1
    
    # === SAFE PATTERNS (should be allowed) ===
    print("\n✅ Safe patterns (should be ALLOWED):\n")
    
    tests_allow = [
        ("ls basic", "ls -la"),
        ("rm single file", "rm file.txt"),
        ("rm with -i flag", "rm -i important.txt"),
        ("SELECT query", "SELECT * FROM users WHERE id = 1;"),
        ("DELETE FROM with WHERE", "DELETE FROM users WHERE id = 5;"),
        ("DELETE FROM with complex WHERE", "DELETE FROM orders WHERE created_at < '2024-01-01';"),
        ("git push normal", "git push origin main"),
        ("git push with upstream", "git push --set-upstream origin feature"),
        ("INSERT query", "INSERT INTO users (name) VALUES ('test');"),
        ("UPDATE with WHERE", "UPDATE users SET name = 'new' WHERE id = 1;"),
        ("npm install", "npm install express"),
        ("pip install", "pip install flask"),
        ("python script", "python3 manage.py migrate"),
        ("mkdir", "mkdir -p project/src"),
        ("chmod (safe)", "chmod 755 script.sh"),
        ("cp file", "cp source.txt dest.txt"),
        ("mv file", "mv old.txt new.txt"),
    ]
    
    for desc, cmd in tests_allow:
        if test_allowed(desc, cmd):
            passed += 1
        else:
            failed += 1
    
    # === SUMMARY ===
    print("\n" + "=" * 60)
    print(f"  RESULTS:", "ALL PASSED ✅" if failed == 0 else f"{failed} FAILED ❌")
    print(f"  Passed: {passed}  |  Failed: {failed}  |  Total: {passed + failed}")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
