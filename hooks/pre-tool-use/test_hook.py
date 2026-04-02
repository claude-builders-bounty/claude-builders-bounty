#!/usr/bin/env python3
"""Test the pre-tool-use hook with various commands."""
import json
import subprocess
import sys
import os

HOOK = os.path.join(os.path.dirname(__file__), "pre-tool-use.py")

def test(command, should_block):
    with open(os.devnull, 'w') as devnull:
        proc = subprocess.run(
            ["python3", HOOK],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
            capture_output=True, text=True
        )
    result = json.loads(proc.stdout)
    blocked = not result.get("continue", True)
    status = "✓ BLOCKED" if (blocked and should_block) else "✓ ALLOWED" if (not blocked and not should_block) else "✗ UNEXPECTED"
    print(f"{status:15} | {command[:60]:<60} | should_block={should_block}")
    if blocked and should_block:
        print(f"  Reason snippet: {result.get('reason','')[:80]}...")

tests = [
    # Should be blocked
    ("rm -rf /tmp/test", True),
    ("rm -rf node_modules", True),
    ("DROP TABLE users", True),
    ("TRUNCATE TABLE sessions", True),
    ("git push --force origin main", True),
    ("git push -f", True),
    ("DELETE FROM users", True),
    ("DELETE FROM logs WHERE id = 1", False),  # Has WHERE, should be OK
    ("echo hello > /dev/sda", True),
    # Should be allowed
    ("echo 'hello world'", False),
    ("ls -la", False),
    ("git push origin main", False),
    ("npm install", False),
    ("cat package.json", False),
    ("DELETE FROM users WHERE id = 1", False),
    ("rm somefile.txt", False),  # Single file rm is not blocked
]

print("\n=== Hook Test Results ===\n")
for cmd, should_block in tests:
    test(cmd, should_block)
print()
