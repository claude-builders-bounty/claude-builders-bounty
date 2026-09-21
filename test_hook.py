#!/usr/bin/env python3
"""Test script for the destructive command blocker hook."""

import json
import subprocess
import sys
import os

HOOK_PATH = os.path.join(os.path.dirname(__file__), 'block_destructive.py')

def run_hook(input_data):
    """Run the hook with given input and return (stdout, exit_code)."""
    proc = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )
    return proc.stdout.strip(), proc.returncode

def test_blocked(pattern, command, description):
    """Test that a command is blocked."""
    input_data = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/test/project"
    }
    output, code = run_hook(input_data)
    if code != 0:
        print(f"FAIL: {description} - non-zero exit code {code}")
        return False
    try:
        result = json.loads(output)
        if result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny":
            print(f"PASS: {description}")
            return True
        else:
            print(f"FAIL: {description} - not denied, got: {output}")
            return False
    except json.JSONDecodeError:
        print(f"FAIL: {description} - invalid JSON output: {output}")
        return False

def test_allowed(command, description):
    """Test that a command is allowed (exits silently with code 0)."""
    input_data = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/test/project"
    }
    output, code = run_hook(input_data)
    if code == 0 and output == "":
        print(f"PASS: {description}")
        return True
    else:
        print(f"FAIL: {description} - got output: {output}, code: {code}")
        return False

def test_non_bash_tool(command, description):
    """Test that non-Bash tools are ignored."""
    input_data = {
        "tool_name": "Edit",
        "tool_input": {"command": command},
        "cwd": "/test/project"
    }
    output, code = run_hook(input_data)
    if code == 0 and output == "":
        print(f"PASS: {description}")
        return True
    else:
        print(f"FAIL: {description} - got output: {output}, code: {code}")
        return False

def main():
    print("Testing destructive command blocker hook...\n")
    
    all_passed = True
    
    # Blocked patterns
    print("=== Blocked Patterns ===")
    all_passed &= test_blocked("rm -rf", "rm -rf /tmp/test", "rm -rf")
    all_passed &= test_blocked("rm -rf", "RM -RF /tmp/test", "RM -RF (uppercase)")
    all_passed &= test_blocked("rm -rf", "npm test && rm -rf /build", "rm -rf in subcommand")
    
    all_passed &= test_blocked("DROP TABLE", "DROP TABLE users", "DROP TABLE")
    all_passed &= test_blocked("DROP TABLE", "drop table users", "drop table (lowercase)")
    
    all_passed &= test_blocked("git push --force", "git push --force origin main", "git push --force")
    all_passed &= test_allowed("git push --force-with-lease origin main", "git push --force-with-lease")
    
    all_passed &= test_blocked("TRUNCATE", "TRUNCATE TABLE logs", "TRUNCATE TABLE")
    all_passed &= test_blocked("TRUNCATE", "TRUNCATE users", "TRUNCATE without TABLE")
    
    all_passed &= test_blocked("DELETE FROM without WHERE", "DELETE FROM users", "DELETE FROM no WHERE")
    all_passed &= test_blocked("DELETE FROM without WHERE", "delete from users", "delete from (lowercase)")
    all_passed &= test_blocked("DELETE FROM without WHERE", "DELETE FROM users;", "DELETE FROM with semicolon")
    
    # Allowed patterns
    print("\n=== Allowed Patterns ===")
    all_passed &= test_allowed("rm file.txt", "rm single file")
    all_passed &= test_allowed("rm -r dir", "rm -r (recursive but not force)")
    all_passed &= test_allowed("ls -la", "ls command")
    all_passed &= test_allowed("git push origin main", "git push (normal)")
    all_passed &= test_allowed("git push --force-with-lease origin main", "git push --force-with-lease")
    all_passed &= test_allowed("DELETE FROM users WHERE id = 1", "DELETE FROM with WHERE")
    all_passed &= test_allowed("DELETE FROM users WHERE name = 'test'", "DELETE FROM with WHERE clause")
    all_passed &= test_allowed("SELECT * FROM users", "SELECT query")
    all_passed &= test_allowed("INSERT INTO users VALUES (1)", "INSERT query")
    all_passed &= test_allowed("UPDATE users SET name = 'test'", "UPDATE query")
    
    # Non-Bash tools
    print("\n=== Non-Bash Tools ===")
    all_passed &= test_non_bash_tool("rm -rf /tmp", "Edit tool ignored")
    all_passed &= test_non_bash_tool("DROP TABLE users", "Read tool ignored")
    
    # Invalid input
    print("\n=== Invalid Input Handling ===")
    proc = subprocess.run(
        [sys.executable, HOOK_PATH],
        input="invalid json",
        capture_output=True,
        text=True
    )
    if proc.returncode == 0 and proc.stdout.strip() == "":
        print("PASS: Invalid JSON handled gracefully")
    else:
        print(f"FAIL: Invalid JSON - code: {proc.returncode}, output: {proc.stdout}")
        all_passed = False
    
    proc = subprocess.run(
        [sys.executable, HOOK_PATH],
        input="{}",
        capture_output=True,
        text=True
    )
    if proc.returncode == 0 and proc.stdout.strip() == "":
        print("PASS: Empty JSON handled gracefully")
    else:
        print(f"FAIL: Empty JSON - code: {proc.returncode}, output: {proc.stdout}")
        all_passed = False
    
    print(f"\n{'='*40}")
    if all_passed:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())