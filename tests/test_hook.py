#!/usr/bin/env python3
import subprocess
import os
import sys
import tempfile
import json

HOOK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks", "pre-tool-use"))
LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

def test_hook():
    print("=== Testing Claude Code Pre-Tool-Use Security Hook ===")
    assert os.path.exists(HOOK_PATH), f"Hook not found at {HOOK_PATH}"
    
    # Clean previous log if exists
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            prev_lines = len(f.readlines())
    else:
        prev_lines = 0

    destructive_commands = [
        "rm -rf /tmp/test_dir",
        "rm -f -r some_dir",
        "DROP TABLE users;",
        "sqlite3 db.sqlite 'DROP TABLE accounts;'",
        "git push --force origin main",
        "git push origin master -f",
        "TRUNCATE TABLE logs;",
        "DELETE FROM users;",
        "DELETE FROM sessions"
    ]

    safe_commands = [
        "ls -la",
        "git status",
        "git push origin feat/cool-feature",
        "rm file.txt",
        "DELETE FROM users WHERE id = 1;",
        "SELECT * FROM users;"
    ]

    print("\n1. Testing destructive commands (must be blocked)...")
    for cmd in destructive_commands:
        # Test CLI args
        res = subprocess.run([sys.executable, HOOK_PATH, cmd], capture_output=True, text=True)
        assert res.returncode == 1, f"Expected {cmd} to be blocked, but got exit code {res.returncode}"
        assert "[BLOCKED BY SECURITY HOOK]" in res.stderr
        print(f"  [OK BLOCKED] {cmd}")

        # Test JSON stdin
        json_input = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        res_json = subprocess.run([sys.executable, HOOK_PATH], input=json_input, capture_output=True, text=True)
        assert res_json.returncode == 1, f"Expected JSON {cmd} to be blocked"

    print("\n2. Testing safe commands (must be allowed)...")
    for cmd in safe_commands:
        res = subprocess.run([sys.executable, HOOK_PATH, cmd], capture_output=True, text=True)
        assert res.returncode == 0, f"Expected {cmd} to be allowed, but got {res.returncode}. Stderr: {res.stderr}"
        print(f"  [OK ALLOWED] {cmd}")

    print("\n3. Testing blocked log persistence...")
    assert os.path.exists(LOG_PATH), "Log file was not created"
    with open(LOG_PATH, "r") as f:
        curr_lines = len(f.readlines())
    assert curr_lines > prev_lines, "Blocked entries were not logged"
    print(f"  [OK LOGGED] Log entries recorded in {LOG_PATH}")

    print("\n✅ All security hook tests passed successfully!")

if __name__ == "__main__":
    test_hook()
