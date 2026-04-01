#!/usr/bin/env python3
"""Tests for safety-hook.py"""
import subprocess
import json
import sys
import os

HOOK = os.path.join(os.path.dirname(__file__), "safety-hook.py")

def run_hook(tool_name: str, command: str) -> tuple[int, str]:
    """Run the hook with given input, return (exit_code, stdout)."""
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    result = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()

# Tests for BLOCKED commands
BLOCKED_TESTS = [
    ("rm -rf /", "rm -rf"),
    ("rm -rf /home/user", "rm -rf"),
    ("rm -f -r /tmp", "rm -rf"),
    ("sudo rm -rf /", "sudo rm"),
    ("DROP TABLE users;", "DROP TABLE"),
    ("DROP DATABASE production;", "DROP TABLE"),
    ("git push origin main --force", "git push --force"),
    ("git push -f origin main", "git push --force"),
    ("TRUNCATE TABLE users;", "TRUNCATE"),
    ("TRUNCATE users;", "TRUNCATE"),
    ("DELETE FROM users;", "DELETE FROM"),
    ("DELETE FROM users", "DELETE FROM"),
    ("mkfs.ext4 /dev/sda1", "mkfs"),
    ("dd if=/dev/zero of=/dev/sda", "dd writing"),
    ("chmod -R 777 /", "chmod 777"),
    ("shutdown -h now", "shutdown"),
    ("reboot", "reboot"),
]

# Tests for ALLOWED commands
ALLOWED_TESTS = [
    "ls -la",
    "git push origin main",
    "git commit -m 'fix: resolve issue'",
    "rm temp.txt",
    "rm -f temp.txt",
    "DELETE FROM users WHERE id = 5;",
    "SELECT * FROM users;",
    "chmod 755 script.sh",
    "chmod 644 file.txt",
    "dd if=input.img of=output.img",
    "echo 'DROP TABLE' > notes.txt",
    "python3 script.py",
    "npm install",
]

passed = 0
failed = 0

print("=== Testing BLOCKED commands ===\n")
for cmd, expected_reason in BLOCKED_TESTS:
    code, output = run_hook("bash", cmd)
    if code != 0:
        passed += 1
        print(f"  ✅ BLOCKED: {cmd}")
    else:
        failed += 1
        print(f"  ❌ NOT BLOCKED: {cmd} (expected: {expected_reason})")

print(f"\n=== Testing ALLOWED commands ===\n")
for cmd in ALLOWED_TESTS:
    code, output = run_hook("bash", cmd)
    if code == 0:
        passed += 1
        print(f"  ✅ ALLOWED: {cmd}")
    else:
        failed += 1
        print(f"  ❌ WRONGLY BLOCKED: {cmd}")

print(f"\n=== Testing non-bash tools (should always allow) ===\n")
for tool in ["read_file", "write_file", "search"]:
    code, _ = run_hook(tool, "rm -rf /")
    if code == 0:
        passed += 1
        print(f"  ✅ ALLOWED (non-bash tool: {tool})")
    else:
        failed += 1
        print(f"  ❌ WRONGLY BLOCKED: {tool}")

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("🎉 All tests passed!")
else:
    print(f"⚠️  {failed} tests failed!")
