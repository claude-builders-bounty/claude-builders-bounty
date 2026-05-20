#!/usr/bin/env python3
"""
test-hook.py - Test the destructive command blocker hook

Run this script to verify the hook works correctly.
"""

import subprocess
import json
import sys

def test_hook(tool_name, command, expected_decision):
    """Test the hook with a specific command"""
    hook_path = "pre-tool-use-hook.py"
    
    input_data = {
        "tool_name": tool_name,
        "tool_input": {"command": command}
    }
    
    result = subprocess.run(
        ["python3", hook_path],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )
    
    try:
        output = json.loads(result.stdout)
        decision = output.get("decision")
        
        if decision == expected_decision:
            print(f"✅ PASS: '{command}' -> {decision}")
            return True
        else:
            print(f"❌ FAIL: '{command}' -> expected {expected_decision}, got {decision}")
            print(f"   Reason: {output.get('reason')}")
            return False
    except json.JSONDecodeError:
        print(f"❌ FAIL: Invalid JSON output for '{command}'")
        print(f"   stdout: {result.stdout}")
        print(f"   stderr: {result.stderr}")
        return False

def main():
    print("=" * 60)
    print("Testing Destructive Command Blocker Hook")
    print("=" * 60)
    print()
    
    tests = [
        # Should be BLOCKED
        ("bash", "rm -rf /", "reject"),
        ("bash", "rm -rf /home/user", "reject"),
        ("bash", "rm -fr /tmp", "reject"),
        ("bash", "rm --recursive --force .", "reject"),
        ("bash", "DROP TABLE users", "reject"),
        ("bash", "TRUNCATE TABLE logs", "reject"),
        ("bash", "DELETE FROM users", "reject"),
        ("bash", "git push --force origin main", "reject"),
        ("bash", "git push -f", "reject"),
        ("bash", "git push origin +force", "reject"),
        
        # Should be ALLOWED
        ("bash", "ls -la", "approve"),
        ("bash", "rm file.txt", "approve"),  # Single file, no -rf
        ("bash", "DELETE FROM users WHERE id = 1", "approve"),  # Has WHERE
        ("bash", "git push origin main", "approve"),  # No force
        ("bash", "cat /etc/passwd", "approve"),  # Reading, not destructive
        
        # Non-bash tools should always be approved
        ("read", {"file_path": "/etc/passwd"}, "approve"),
        ("edit", {"path": "test.py"}, "approve"),
    ]
    
    passed = 0
    failed = 0
    
    for tool_name, command, expected in tests:
        if test_hook(tool_name, command, expected):
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()