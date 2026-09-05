#!/usr/bin/env python3
import subprocess
import json
import os
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "hooks" / "pre-tool-use.py"
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

TEST_CASES = [
    # Dangerous (Must block: return code 1)
    ("rm -rf /var/log", True, "rm -rf"),
    ("rm -r -f ./temp", True, "rm -r -f"),
    ("DROP TABLE users;", True, "DROP TABLE"),
    ("git push origin main --force", True, "git push --force"),
    ("git push -f origin feat", True, "git push -f"),
    ("TRUNCATE TABLE logs;", True, "TRUNCATE TABLE"),
    ("DELETE FROM sessions", True, "DELETE FROM without WHERE"),
    
    # Safe (Must allow: return code 0)
    ("ls -la", False, "Safe ls"),
    ("git push origin main", False, "Safe git push"),
    ("git commit -m 'rm -rf fix'", False, "Safe commit message with keyword"),
    ("DELETE FROM users WHERE id = 10", False, "DELETE with valid WHERE clause"),
    ("echo 'hello world'", False, "Safe echo"),
]

def run_test():
    passed = 0
    total = len(TEST_CASES)
    
    # Clear log before test
    if LOG_FILE.exists():
        LOG_FILE.unlink()
        
    for cmd, should_block, desc in TEST_CASES:
        payload = json.dumps({
            "tool": "Bash",
            "parameters": {"command": cmd},
            "cwd": str(Path.cwd())
        })
        
        proc = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True
        )
        
        is_blocked = (proc.returncode != 0)
        if is_blocked == should_block:
            passed += 1
            print(f"✅ PASS: [{desc}] -> blocked={is_blocked}")
        else:
            print(f"❌ FAIL: [{desc}] (cmd: '{cmd}') -> expected blocked={should_block}, got {is_blocked}")
            if proc.stderr:
                print(f"   stderr: {proc.stderr.strip()}")

    print(f"\nResults: {passed}/{total} tests passed.")
    assert passed == total, f"Some tests failed: {passed}/{total}"
    
    # Verify log output
    assert LOG_FILE.exists(), "Log file was not created!"
    lines = LOG_FILE.read_text().strip().split("\n")
    print(f"✅ Verified log entries: {len(lines)} blocked events logged in {LOG_FILE}")
    print("\n🎉 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    run_test()
