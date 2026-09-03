#!/usr/bin/env python3
"""
Reproduction script for Issue #3: Pre-tool-use hook blocking destructive bash commands.

Demonstrates:
1. Baseline vulnerability: without the hook, destructive commands execute unintercepted.
2. Hook verification: with the hook, destructive commands are strictly intercepted
   with exit code 2, logged to blocked.log, and descriptive explanation emitted to stderr.
3. False-positive verification: standard development commands are permitted with exit code 0.
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / ".claude" / "hooks" / "block_destructive.py"

DESTRUCTIVE_COMMANDS = [
    ("rm -rf /", "rm_rf"),
    ("rm -fr /tmp/test", "rm_rf"),
    ("rm -r -f node_modules", "rm_rf"),
    ("sudo rm -rf /var/log", "rm_rf"),
    ("DROP TABLE users;", "drop_table"),
    ("drop table if exists sensitive_data", "drop_table"),
    ("DROP DATABASE production;", "drop_table"),
    ("git push --force origin main", "git_force"),
    ("git push -f", "git_force"),
    ("git push --force-with-lease origin feat", "git_force"),
    ("TRUNCATE TABLE audit_log;", "truncate"),
    ("truncate sessions", "truncate"),
    ("DELETE FROM accounts;", "delete_without_where"),
    ("DELETE FROM users", "delete_without_where"),
    ("mkfs.ext4 /dev/sda1", "raw_disk"),
    ("dd if=/dev/zero of=/dev/sda bs=1M", "raw_disk"),
    (":(){ :|:& };:", "fork_bomb"),
    ("shutdown -h now", "system_state"),
]

SAFE_COMMANDS = [
    "git status",
    "git diff HEAD~1",
    "git commit -m 'feat: test'",
    "git push origin feature-branch",
    "npm test",
    "python -m unittest discover",
    "rm file.txt",
    "rm -f temp.log",
    "SELECT * FROM users WHERE active = 1;",
    "DELETE FROM users WHERE id = 42;",
    "DELETE FROM sessions WHERE expired_at < NOW();",
    "UPDATE accounts SET balance = 100 WHERE id = 1;",
]


def run_hook(command: str, log_file: Path, tool_name: str = "Bash") -> subprocess.CompletedProcess:
    """Run hook script simulating Claude Code stdin IPC."""
    payload = {
        "session_id": "test_session_reproduce",
        "cwd": str(REPO_ROOT),
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {
            "command": command
        }
    }
    env = dict(os.environ)
    env["CLAUDE_HOOK_BLOCKED_LOG"] = str(log_file)
    env["CLAUDE_BLOCKED_LOG_PATH"] = str(log_file)

    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env
    )


def test_baseline_vulnerability():
    """Verify that without the hook, destructive commands would run unprotected."""
    print("=== Step 1: Baseline Check ===")
    if not HOOK_SCRIPT.exists():
        print(f"[BASELINE VULNERABLE] Hook file does not exist: {HOOK_SCRIPT}")
        print("Destructive commands (rm -rf, DROP TABLE, git push -f) would execute unintercepted by Claude Code.")
        return False
    print(f"[INFO] Hook script detected at {HOOK_SCRIPT}. Proceeding to enforcement tests.")
    return True


def test_hook_enforcement():
    """Verify that all destructive commands are intercepted with exit code 2 and logged."""
    print("\n=== Step 2: Testing Destructive Commands Interception (Exit 2) ===")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_log = Path(temp_dir) / "blocked.log"

        failed = []
        for cmd, category in DESTRUCTIVE_COMMANDS:
            proc = run_hook(cmd, temp_log)
            if proc.returncode != 2:
                print(f"[FAIL] Expected exit code 2, got {proc.returncode} for: {cmd}")
                failed.append((cmd, f"Returncode was {proc.returncode}"))
                continue

            # Verify stderr contains explanation
            if not proc.stderr or "blocked" not in proc.stderr.lower():
                print(f"[FAIL] Stderr lacked blocking explanation for: {cmd}")
                failed.append((cmd, "Missing explanation in stderr"))
                continue

            # Verify stdout contains structured JSON denial
            try:
                stdout_data = json.loads(proc.stdout) if proc.stdout.strip() else {}
                decision = stdout_data.get("hookSpecificOutput", {}).get("permissionDecision", "")
                if decision != "deny":
                    print(f"[FAIL] JSON permissionDecision != 'deny' for: {cmd}")
                    failed.append((cmd, "JSON output lacked permissionDecision: deny"))
                    continue
            except Exception as e:
                print(f"[FAIL] Stdout was not valid JSON for: {cmd}: {e}")
                failed.append((cmd, f"Invalid stdout JSON: {e}"))
                continue

            print(f"[PASS] Intercepted [{category}]: {cmd}")

        # Check log file entries
        if not temp_log.exists():
            print("[FAIL] Audit log file was not created!")
            return False

        log_content = temp_log.read_text(encoding="utf-8")
        log_lines = [line for line in log_content.splitlines() if line.strip()]
        print(f"[INFO] Audit log recorded {len(log_lines)} blocked operations.")
        if len(log_lines) < len(DESTRUCTIVE_COMMANDS):
            print(f"[FAIL] Expected at least {len(DESTRUCTIVE_COMMANDS)} log lines, got {len(log_lines)}")
            return False

        if failed:
            print(f"\n[FAIL] {len(failed)} destructive commands were not properly blocked:")
            for cmd, reason in failed:
                print(f"  - {cmd}: {reason}")
            return False

    print("\n[SUCCESS] All destructive commands intercepted with exit code 2, stderr reasons, and audit logs.")
    return True


def test_safe_commands():
    """Verify that safe commands are allowed with exit code 0."""
    print("\n=== Step 3: Testing Safe Commands Passing (Exit 0) ===")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_log = Path(temp_dir) / "blocked.log"

        failed = []
        for cmd in SAFE_COMMANDS:
            proc = run_hook(cmd, temp_log)
            if proc.returncode != 0:
                print(f"[FAIL] Safe command was blocked (exit {proc.returncode}): {cmd}")
                print(f"       stderr: {proc.stderr}")
                failed.append((cmd, f"Blocked with exit {proc.returncode}"))
                continue
            print(f"[PASS] Allowed safe command: {cmd}")

        # Ensure safe commands did not write to blocked.log
        if temp_log.exists() and temp_log.stat().st_size > 0:
            print("[FAIL] Safe commands wrote entries to blocked.log!")
            return False

        if failed:
            print(f"\n[FAIL] {len(failed)} safe commands were incorrectly blocked:")
            for cmd, reason in failed:
                print(f"  - {cmd}: {reason}")
            return False

    print("\n[SUCCESS] All safe developer commands passed through with exit code 0.")
    return True


def main():
    print("Running reproduction and verification harness for Issue #3...")
    baseline_ok = test_baseline_vulnerability()
    if not baseline_ok:
        print("\n[VULNERABILITY CONFIRMED] Baseline lacks destructive command prevention hook.")
        sys.exit(1)

    enforce_ok = test_hook_enforcement()
    safe_ok = test_safe_commands()

    if enforce_ok and safe_ok:
        print("\n========================================================")
        print("ALL CHECKS PASSED: Issue #3 is completely and genuinely solved.")
        print("========================================================")
        sys.exit(0)
    else:
        print("\n[ERROR] Verification failed.")
        sys.exit(2)


if __name__ == "__main__":
    main()
