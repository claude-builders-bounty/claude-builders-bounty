#!/usr/bin/env python3
import subprocess
import json
import sys

HOOK_SCRIPT = "./pre_tool_use_guard.py"

BLOCKED_CASES = [
    "rm -rf /var/log",
    "rm -fr /home/user",
    "git push origin main --force",
    "git push -f",
    "DROP TABLE users;",
    "TRUNCATE TABLE transactions",
    "DELETE FROM accounts;",
]

ALLOWED_CASES = [
    "rm file.txt",
    "git push origin feature",
    "SELECT * FROM users WHERE active = 1;",
    "DELETE FROM sessions WHERE expires_at < NOW();",
    "python3 -m unittest",
    "npm run build",
]

def run_test(cmd: str, should_block: bool):
    # Test via stdin json
    payload = json.dumps({"tool_name": "bash", "tool_input": {"command": cmd}})
    p = subprocess.run([sys.executable, HOOK_SCRIPT], input=payload, text=True, capture_output=True)
    is_blocked = (p.returncode != 0)
    
    status = "PASS" if is_blocked == should_block else "FAIL"
    print(f"[{status}] Command: {cmd} -> Blocked: {is_blocked} (Expected: {should_block})")
    assert is_blocked == should_block, f"Test failed for: {cmd}"

def main():
    print("Running Security Hook Validation Suite...\n")
    for cmd in BLOCKED_CASES:
        run_test(cmd, should_block=True)
    for cmd in ALLOWED_CASES:
        run_test(cmd, should_block=False)
    print("\n✅ All 13 test cases passed flawlessly!")

if __name__ == "__main__":
    main()
