#!/usr/bin/env python3
"""Test suite for pre-tool-use-blocker hook"""
import json, subprocess, sys, os

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "pre-tool-use-blocker.py")

def test_hook(command: str, should_block: bool):
    """Run a command through the hook and check if it gets blocked"""
    input_data = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command}
    })
    
    result = subprocess.run(
        ["python3", HOOK_SCRIPT],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    output = json.loads(result.stdout)
    blocked = not output.get("continue", True)
    
    status = "✅" if blocked == should_block else "❌"
    print(f"  {status} {'BLOCK' if should_block else 'ALLOW'}: {command[:60]}")
    
    if blocked:
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        if should_block:
            assert "BLOCKED" in reason, f"Expected BLOCKED message, got: {reason[:80]}"
        else:
            assert False, f"Expected ALLOW but got BLOCK: {reason[:80]}"
    
    return blocked == should_block


if __name__ == "__main__":
    print("Testing pre-tool-use-blocker hook...\n")
    
    tests = [
        ("rm -rf /tmp/test", True),
        ("rm -rf node_modules", True),
        ("DROP TABLE users", True),
        ("git push --force origin main", True),
        ("git push -f", True),
        ("TRUNCATE TABLE logs", True),
        ("DELETE FROM users", True),
        ("DELETE FROM users WHERE id = 1", False),
        ("DROP DATABASE production", True),
        ("chmod 777 script.sh", True),
        ("npm install", False),
        ("git status", False),
        ("ls -la", False),
        ("python3 script.py", False),
        ("echo hello world", False),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, should_block in tests:
        try:
            if test_hook(cmd, should_block):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {cmd[:60]} — {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed > 0:
        sys.exit(1)
