import subprocess
import json
import os
import shutil

HOOK_PATH = "hooks/destructive-command-blocker/pre-tool-use.py"
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")

def run_hook(command):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": "test-session"
    }
    process = subprocess.Popen(
        ["python3", HOOK_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=json.dumps(payload))
    return process.returncode, stdout, stderr

def test_destructive():
    tests = [
        ("rm -rf /", 2, "system or root directories"),
        ("git push --force", 2, "Forced git push"),
        ("DELETE FROM users", 2, "without a WHERE clause"),
        ("DROP TABLE accounts", 2, "Direct table or database deletion"),
        ("docker rm -f $(docker ps -aq)", 2, "Mass deletion of Docker"),
        ("echo hello", 0, ""),
        ("ls -la", 0, ""),
        ("git push origin main", 0, ""),
        ("DELETE FROM users WHERE id=1", 0, ""), # This might fail if my regex is too simple
    ]

    passed = 0
    for cmd, expected_code, expected_msg in tests:
        code, out, err = run_hook(cmd)
        if code == expected_code and (not expected_msg or expected_msg in err):
            print(f"✅ PASS: {cmd}")
            passed += 1
        else:
            print(f"❌ FAIL: {cmd} (Expected {expected_code}, got {code})")
            print(f"Stderr: {err}")

    print(f"\nPassed {passed}/{len(tests)} tests.")

if __name__ == "__main__":
    test_destructive()
