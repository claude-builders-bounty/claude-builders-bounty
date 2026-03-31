#!/usr/bin/env python3
"""
Test suite for the pre-tool-use security hook.
Run with: python3 test_hook.py
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent / "pre_tool_hook.py"

def run_hook(command_json):
    """Run hook with given JSON input."""
    result = subprocess.run(
        ["python3", str(HOOK_PATH)],
        input=json.dumps(command_json),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def test_blocked_commands():
    """Test that blocked commands are rejected."""
    blocked = [
        {"command": "rm -rf /", "desc": "rm -rf root"},
        {"command": "rm -rf /home", "desc": "rm -rf /home"},
        {"command": "rm -rf ~", "desc": "rm -rf home"},
        {"command": "rm -rf *", "desc": "rm -rf wildcard"},
        {"command": "DROP TABLE users", "desc": "DROP TABLE"},
        {"command": "TRUNCATE TABLE logs", "desc": "TRUNCATE TABLE"},
        {"command": "DELETE FROM users", "desc": "DELETE without WHERE"},
        {"command": "git push --force origin main", "desc": "git force push"},
        {"command": "git push -f", "desc": "git push -f"},
        {"command": "dd if=/dev/zero of=/dev/sda", "desc": "dd to disk"},
        {"command": "mkfs.ext4 /dev/sda1", "desc": "mkfs"},
        {"command": "chmod -R 000 /", "desc": "chmod 000 root"},
    ]
    
    passed = 0
    failed = 0
    
    for cmd in blocked:
        json_input = {"tool": "bash", "arguments": {"command": cmd["command"]}}
        code, stdout, stderr = run_hook(json_input)
        
        if code == 1 and "SECURITY BLOCK" in stderr:
            print(f"✅ PASS: Blocked '{cmd['desc']}'")
            passed += 1
        else:
            print(f"❌ FAIL: Should have blocked '{cmd['desc']}' (code={code})")
            if stderr:
                print(f"   stderr: {stderr[:100]}")
            failed += 1
    
    return passed, failed

def test_allowed_commands():
    """Test that safe commands are allowed."""
    allowed = [
        {"command": "ls -la", "desc": "ls"},
        {"command": "cat file.txt", "desc": "cat"},
        {"command": "git status", "desc": "git status"},
        {"command": "rm file.txt", "desc": "rm single file"},
        {"command": "rm -rf ./build", "desc": "rm -rf relative path"},
        {"command": "DELETE FROM logs WHERE id < 100", "desc": "DELETE with WHERE"},
        {"command": "echo 'hello world'", "desc": "echo"},
        {"command": "python script.py", "desc": "python"},
        {"command": "npm install", "desc": "npm"},
    ]
    
    passed = 0
    failed = 0
    
    for cmd in allowed:
        json_input = {"tool": "bash", "arguments": {"command": cmd["command"]}}
        code, stdout, stderr = run_hook(json_input)
        
        if code == 0:
            print(f"✅ PASS: Allowed '{cmd['desc']}'")
            passed += 1
        else:
            print(f"❌ FAIL: Should have allowed '{cmd['desc']}' (code={code})")
            if stderr:
                print(f"   stderr: {stderr[:100]}")
            failed += 1
    
    return passed, failed

def test_log_file():
    """Test that blocked commands are logged."""
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    
    if not log_path.exists():
        print("⚠️  SKIP: Log file not found (no blocked commands yet)")
        return 0, 0
    
    with open(log_path) as f:
        lines = f.readlines()
    
    if lines:
        last_entry = json.loads(lines[-1])
        print(f"✅ PASS: Log file exists with {len(lines)} entries")
        print(f"   Last entry: {last_entry.get('description', 'unknown')}")
        return 1, 0
    else:
        print("✅ PASS: Log file exists (empty)")
        return 1, 0

def main():
    """Run all tests."""
    print("=" * 60)
    print("Security Hook Test Suite")
    print("=" * 60)
    print()
    
    print("Testing BLOCKED commands:")
    print("-" * 40)
    bp, bf = test_blocked_commands()
    print()
    
    print("Testing ALLOWED commands:")
    print("-" * 40)
    ap, af = test_allowed_commands()
    print()
    
    print("Testing log file:")
    print("-" * 40)
    lp, lf = test_log_file()
    print()
    
    total_passed = bp + ap + lp
    total_failed = bf + af + lf
    
    print("=" * 60)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    if total_failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()