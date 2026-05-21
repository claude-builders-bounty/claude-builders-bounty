#!/usr/bin/env python3
"""
Unit tests for the Claude Code Bash Safety Hook.
"""

import json
import subprocess
import sys
import os

# Test cases
TEST_CASES = [
    # rm -rf test cases
    {"command": "rm -rf /", "tool_name": "Bash", "expected_code": 2, "description": "Block rm -rf root"},
    {"command": "rm -rf some_dir", "tool_name": "Bash", "expected_code": 2, "description": "Block rm -rf directory"},
    {"command": "rm file.txt", "tool_name": "Bash", "expected_code": 0, "description": "Allow simple rm file"},
    
    # git push force test cases
    {"command": "git push origin main --force", "tool_name": "Bash", "expected_code": 2, "description": "Block git push force long flag"},
    {"command": "git push origin main -f", "tool_name": "Bash", "expected_code": 2, "description": "Block git push force short flag"},
    {"command": "git push origin main --force-with-lease", "tool_name": "Bash", "expected_code": 2, "description": "Block git push force-with-lease"},
    {"command": "git push origin main", "tool_name": "Bash", "expected_code": 0, "description": "Allow regular git push"},
    
    # DROP TABLE test cases
    {"command": "DROP TABLE users;", "tool_name": "Bash", "expected_code": 2, "description": "Block DROP TABLE"},
    {"command": "drop table clients", "tool_name": "Bash", "expected_code": 2, "description": "Block case-insensitive drop table"},
    {"command": "SELECT * FROM users;", "tool_name": "Bash", "expected_code": 0, "description": "Allow SELECT statement"},
    
    # TRUNCATE test cases
    {"command": "TRUNCATE table_name", "tool_name": "Bash", "expected_code": 2, "description": "Block TRUNCATE"},
    {"command": "truncate users", "tool_name": "Bash", "expected_code": 2, "description": "Block case-insensitive truncate"},
    
    # DELETE FROM without WHERE test cases
    {"command": "DELETE FROM users", "tool_name": "Bash", "expected_code": 2, "description": "Block DELETE FROM without WHERE"},
    {"command": "DELETE FROM users WHERE id = 10", "tool_name": "Bash", "expected_code": 0, "description": "Allow DELETE FROM with WHERE"},
    {"command": "delete from users; select * from users", "tool_name": "Bash", "expected_code": 2, "description": "Block delete from without where in multi-statement query"},
    {"command": "select * from users; delete from users where id = 5", "tool_name": "Bash", "expected_code": 0, "description": "Allow delete with where in multi-statement query"},
    
    # Safe general commands
    {"command": "ls -la", "tool_name": "Bash", "expected_code": 0, "description": "Allow ls command"},
    {"command": "echo 'Hello World'", "tool_name": "Bash", "expected_code": 0, "description": "Allow echo command"},
    
    # Non-bash tools
    {"command": "rm -rf /", "tool_name": "Write", "expected_code": 0, "description": "Allow non-Bash tools (Write)"},
]

def run_test(case):
    hook_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre_tool_use_hook.py")
    
    input_payload = {
        "tool_name": case["tool_name"],
        "tool_input": {
            "command": case["command"]
        },
        "context": {
            "project_path": "/mock/project/path"
        }
    }
    
    # Run the hook in a subprocess
    process = subprocess.Popen(
        [sys.executable, hook_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(input=json.dumps(input_payload))
    return process.returncode, stdout, stderr

def main():
    failed = 0
    passed = 0
    
    print("Running Hook Unit Tests...")
    print("=" * 60)
    
    for i, case in enumerate(TEST_CASES, 1):
        code, stdout, stderr = run_test(case)
        
        status = "PASS"
        if code != case["expected_code"]:
            status = "FAIL"
            failed += 1
        else:
            passed += 1
            
        print(f"[{status}] Test #{i}: {case['description']}")
        print(f"  Command:   {case['command']}")
        print(f"  Expected:  Exit Code {case['expected_code']}")
        print(f"  Got:       Exit Code {code}")
        if code == 2:
            print(f"  Blocked Msg: {stderr.strip().splitlines()[1] if len(stderr.strip().splitlines()) > 1 else stderr.strip()}")
        print("-" * 60)
        
    print(f"\nTest Summary: {passed} passed, {failed} failed.")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed successfully! 🎉")
        sys.exit(0)

if __name__ == "__main__":
    main()
