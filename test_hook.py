#!/usr/bin/env python3
"""Test suite for block_destructive.py hook. 31 test cases total."""
import json
import subprocess
import sys
import os

HOOK = os.path.expanduser("~/Projects/CYBER_BOUNTY/sandbox/algora_hook/block_destructive.py")

# (command, should_block)
TEST_CASES = [
    # === BLOCKED (should deny) ===
    ("rm -rf /tmp/build", True),
    ("rm -fr node_modules", True),
    ("rm -rf --no-preserve-root /", True),
    ("git push --force origin main", True),
    ("git push -f origin main", True),  # -f is short for --force
    ("DROP TABLE users", True),
    ("drop table accounts", True),
    ("TRUNCATE TABLE logs", True),
    ("TRUNCATE logs", True),
    ("DELETE FROM sessions", True),
    ("delete from users", True),
    ("mkfs.ext4 /dev/sdb1", True),
    ("dd if=image.img of=/dev/sdb", True),

    # === ALLOWED (should permit) ===
    ("ls -la", False),
    ("cat README.md", False),
    ("git status", False),
    ("git push origin main", False),
    ("git push --force-with-lease origin main", False),
    ("rm README.md", False),
    ("rm -i old_file.txt", False),
    ("DELETE FROM users WHERE id = 1", False),
    ("echo 'DROP TABLE users' > backup.sql", False),  # in string, not SQL
    ("python3 manage.py migrate", False),

    # === EDGE CASES ===
    ("sudo rm -rf /tmp/build", True),
    ("echo y | rm -rf /tmp/build", True),
    ("git push --force origin main && echo done", True),
    ("DELETE FROM users WHERE 1=1", False),  # has WHERE, allowed by spec
    ("echo \"DROP TABLE users\"", False),  # echo, not SQL
    ("rm file.txt", False),
    ("git push --force --tags origin main", True),
    ("find . -name \"*.py\" | wc -l", False),
]


def run_hook(command: str) -> dict:
    """Run the hook with a given command and return its output."""
    payload = json.dumps({"tool_input": {"command": command}})
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = "/tmp/test-project"
    result = subprocess.run(
        [sys.executable, HOOK],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = {}
    if result.stdout.strip():
        try:
            stdout = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return {
        "stdout": stdout,
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def main():
    passed = 0
    failed = 0

    for command, should_block in TEST_CASES:
        result = run_hook(command)
        stdout = result["stdout"]
        stderr = result["stderr"]
        returncode = result["returncode"]

        # Check both formats: hookSpecificOutput (new) and top-level (legacy)
        is_blocked = (
            stdout.get("permissionDecision") == "deny"
            or stdout.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        )

        status = "PASS" if is_blocked == should_block else "FAIL"
        marker = "BLOCKED" if is_blocked else "ALLOWED"

        # Triple-signal checks for blocked commands
        signals_ok = True
        signal_detail = ""
        if should_block:
            # Signal A: stdout has hookSpecificOutput.permissionDecision=deny
            hook_decision = stdout.get("hookSpecificOutput", {}).get("permissionDecision")
            if hook_decision != "deny":
                signals_ok = False
                signal_detail = "missing hookSpecificOutput.permissionDecision"
            # Signal B: stderr has reason text
            if not stderr:
                signals_ok = False
                signal_detail = "missing stderr reason"
            # Signal C: exit code 2
            if returncode != 2:
                signals_ok = False
                signal_detail = f"exit code {returncode}, expected 2"

        if status == "PASS" and signals_ok:
            passed += 1
            print(f"  {status}: {marker:7s} | {command}")
        else:
            failed += 1
            expected = "BLOCKED" if should_block else "ALLOWED"
            extra = f" [signals: {signal_detail}]" if signal_detail else ""
            print(f"  {status}: got {marker}, expected {expected:7s}{extra} | {command}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{passed+failed} passed, {failed} failed")
    if failed == 0:
        print("STATUS: ALL TESTS PASS")
    else:
        print(f"STATUS: {failed} TESTS FAILED")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
