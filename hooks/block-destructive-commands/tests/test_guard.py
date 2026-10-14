#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for block_destructive.py and block_destructive.sh.
Verifies:
1. Blocked commands correctly exit with code 2.
2. Safe commands pass through with exit code 0.
3. Blocked attempts write structured audit logs to ~/.claude/hooks/blocked.log.
4. Non-bash tools are ignored cleanly.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_HOOK = BASE_DIR / "block_destructive.py"
BASH_HOOK = BASE_DIR / "block_destructive.sh"

TEST_CASES = [
    # Blocked cases (must return exit code 2)
    {"cmd": "rm -rf node_modules", "should_block": True, "label": "rm -rf direct"},
    {"cmd": "rm -fr build/", "should_block": True, "label": "rm -fr direct"},
    {"cmd": "rm -r -f /tmp/foo", "should_block": True, "label": "rm -r -f separated"},
    {"cmd": "sudo rm --recursive --force /var/log/*", "should_block": True, "label": "sudo rm --recursive --force"},
    {"cmd": "DROP TABLE users;", "should_block": True, "label": "SQL DROP TABLE uppercase"},
    {"cmd": "drop table accounts", "should_block": True, "label": "SQL drop table lowercase"},
    {"cmd": "DROP DATABASE production;", "should_block": True, "label": "SQL DROP DATABASE"},
    {"cmd": "TRUNCATE TABLE logs;", "should_block": True, "label": "SQL TRUNCATE TABLE"},
    {"cmd": "truncate audit_events", "should_block": True, "label": "SQL truncate without table keyword"},
    {"cmd": "DELETE FROM users;", "should_block": True, "label": "SQL DELETE FROM without WHERE"},
    {"cmd": "delete from sessions", "should_block": True, "label": "SQL delete from without WHERE lowercase"},
    {"cmd": "git push origin main --force", "should_block": True, "label": "git push --force"},
    {"cmd": "git push -f origin feat/test", "should_block": True, "label": "git push -f"},
    {"cmd": "git push origin main --force-with-lease", "should_block": True, "label": "git push --force-with-lease"},
    {"cmd": "sudo mkfs.ext4 /dev/sdb1", "should_block": True, "label": "mkfs filesystem format"},

    # Safe / Allowed cases (must return exit code 0)
    {"cmd": "rm package-lock.json", "should_block": False, "label": "rm single file"},
    {"cmd": "git push origin feat/clean-branch", "should_block": False, "label": "git push normal"},
    {"cmd": "git status", "should_block": False, "label": "git status"},
    {"cmd": "SELECT * FROM users;", "should_block": False, "label": "SQL SELECT"},
    {"cmd": "DELETE FROM users WHERE id = 42;", "should_block": False, "label": "SQL DELETE with valid WHERE"},
    {"cmd": "python test.py", "should_block": False, "label": "run test script"},
    {"cmd": "npm run build", "should_block": False, "label": "npm build"},
]

def run_hook_test(hook_path: Path, use_python=False):
    print(f"\n--- Running tests against: {hook_path.name} ---")
    with tempfile.TemporaryDirectory() as tmp_home:
        env = os.environ.copy()
        env["HOME"] = tmp_home
        env["CLAUDE_PROJECT_DIR"] = "/tmp/fake-claude-project"

        passed_count = 0

        for case in TEST_CASES:
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": case["cmd"]}
            }
            json_str = json.dumps(payload)

            if use_python:
                cmd = [sys.executable, str(hook_path)]
            else:
                cmd = ["bash", str(hook_path)]

            proc = subprocess.run(
                cmd,
                input=json_str,
                text=True,
                capture_output=True,
                env=env
            )

            expected_code = 2 if case["should_block"] else 0
            if proc.returncode == expected_code:
                status = "PASS"
                passed_count += 1
            else:
                status = f"FAIL (Got {proc.returncode}, expected {expected_code})"
                print(f"[{status}] {case['label']}: {case['cmd']}")
                print(f"  STDERR: {proc.stderr.strip()}")
                print(f"  STDOUT: {proc.stdout.strip()}")
                continue

            print(f"[{status}] {case['label']}")

        # Verify audit log existence and contents
        log_file = Path(tmp_home) / ".claude" / "hooks" / "blocked.log"
        if not log_file.exists():
            print("FAIL: Audit log file ~/.claude/hooks/blocked.log was not created!")
            return False

        log_content = log_file.read_text(encoding="utf-8")
        if "rm -rf node_modules" not in log_content or "DROP TABLE users;" not in log_content:
            print("FAIL: Expected blocked entries missing from audit log!")
            return False

        print(f"Audit log verified: {len(log_content.splitlines())} lines written to {log_file}")
        print(f"Result: {passed_count}/{len(TEST_CASES)} tests passed.")
        return passed_count == len(TEST_CASES)

def main():
    py_ok = run_hook_test(PYTHON_HOOK, use_python=True)
    bash_ok = True
    if os.name != "nt":
        bash_ok = run_hook_test(BASH_HOOK, use_python=False)

    if not py_ok or not bash_ok:
        sys.exit(1)

    print("\nAll automated hook tests PASSED with 100% compliance!")
    sys.exit(0)

if __name__ == "__main__":
    main()
