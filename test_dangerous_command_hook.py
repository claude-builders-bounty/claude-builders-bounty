#!/usr/bin/env python3
"""
Test script for the Claude Code PreToolUse hook
"""

import json
import subprocess
import sys

def test_dangerous_patterns():
    """Test that dangerous patterns are blocked."""
    dangerous_commands = [
        "rm -rf /tmp/test",
        "DROP TABLE users",
        "git push --force origin main",
        "TRUNCATE TABLE sessions",
        "DELETE FROM users",
    ]
    
    safe_commands = [
        "ls -la",
        "echo 'hello'",
        "git status",
        "SELECT * FROM users",
        "DELETE FROM users WHERE id = 1",
    ]
    
    print("Testing dangerous commands (should be blocked):")
    for cmd in dangerous_commands:
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        
        process = subprocess.Popen(
            ["python3", "claude-pre-tool-use-hook.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(json.dumps(input_data))
        result = json.loads(stdout)
        
        decision = result["hookSpecificOutput"]["permissionDecision"]
        status = "✓ BLOCKED" if decision == "deny" else "✗ NOT BLOCKED"
        print(f"  {status}: {cmd}")
    
    print("\nTesting safe commands (should be allowed):")
    for cmd in safe_commands:
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        
        process = subprocess.Popen(
            ["python3", "claude-pre-tool-use-hook.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(json.dumps(input_data))
        result = json.loads(stdout)
        
        decision = result["hookSpecificOutput"]["permissionDecision"]
        status = "✓ ALLOWED" if decision == "allow" else "✗ NOT ALLOWED"
        print(f"  {status}: {cmd}")

if __name__ == "__main__":
    test_dangerous_patterns()