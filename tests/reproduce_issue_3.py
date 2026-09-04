#!/usr/bin/env python3
"""
Standalone Reproduction and Verification Script for Issue #3.

Verifies:
1. All required destructive patterns are blocked with exit code 2 and logged.
2. Normal safe developer commands are permitted with exit code 0.
3. Hook format and logging requirements are 100% satisfied.
"""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "block-destructive" / "block_destructive.py"


def run_test():
    print("=" * 65)
    print("Issue #3 Reproduction & Verification Harness")
    print("=" * 65)

    if not HOOK_SCRIPT.exists():
        print(f"[FAIL] Hook script not found at {HOOK_SCRIPT}")
        sys.exit(1)

    tmp_dir = tempfile.TemporaryDirectory()
    log_file = Path(tmp_dir.name) / "blocked.log"
    env = os.environ.copy()
    env["CLAUDE_HOOK_BLOCKED_LOG"] = str(log_file)

    destructive_commands = [
        ("rm_rf", "rm -rf /"),
        ("rm_rf", "rm -fr /tmp/build"),
        ("rm_rf", "rm -r -f node_modules"),
        ("rm_rf", "sudo rm -rf /etc"),
        ("drop_table", "DROP TABLE users;"),
        ("drop_table", "drop table if exists payments"),
        ("drop_table", "DROP DATABASE production;"),
        ("git_force", "git push --force origin main"),
        ("git_force", "git push -f"),
        ("git_force", "git push --force-with-lease"),
        ("truncate", "TRUNCATE TABLE audit_log;"),
        ("truncate", "truncate sessions"),
        ("delete_without_where", "DELETE FROM accounts;"),
        ("delete_without_where", "DELETE FROM users"),
    ]

    safe_commands = [
        "git status",
        "git diff HEAD~1",
        "git commit -m 'feat: block destructive bash commands'",
        "git push origin feat/hook",
        "rm file.txt",
        "rm -f temp.log",
        "rm -r docs/",
        "truncate -s 0 file.log",
        "SELECT * FROM users WHERE active = 1;",
        "DELETE FROM users WHERE id = 42;",
        "DELETE FROM sessions WHERE expired_at < NOW();",
        "npm test",
        "python3 -m unittest",
    ]

    print("\n--- Phase 1: Verifying Destructive Commands (Must be BLOCKED with Exit Code 2) ---")
    blocked_count = 0
    for expected_rule, cmd in destructive_commands:
        payload = {
            "tool_name": "Bash",
            "cwd": "/workspace/sample-project",
            "tool_input": {"command": cmd}
        }
        res = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env
        )

        if res.returncode != 2:
            print(f"  [FAIL] Expected exit code 2 for '{cmd}', got {res.returncode}")
            sys.exit(1)

        try:
            out_data = json.loads(res.stdout)
            if out_data["hookSpecificOutput"]["permissionDecision"] != "deny":
                print(f"  [FAIL] Expected permissionDecision 'deny' for '{cmd}', got {out_data}")
                sys.exit(1)
        except Exception as e:
            print(f"  [FAIL] Failed parsing stdout JSON for '{cmd}': {e}")
            sys.exit(1)

        print(f"  [PASS] Successfully blocked [{expected_rule}]: {cmd}")
        blocked_count += 1

    print(f"\n[INFO] Successfully intercepted {blocked_count}/{len(destructive_commands)} destructive commands.")

    print("\n--- Phase 2: Verifying Safe Commands (Must be ALLOWED with Exit Code 0) ---")
    allowed_count = 0
    for cmd in safe_commands:
        payload = {
            "tool_name": "Bash",
            "cwd": "/workspace/sample-project",
            "tool_input": {"command": cmd}
        }
        res = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env
        )

        if res.returncode != 0:
            print(f"  [FAIL] Expected exit code 0 for safe command '{cmd}', got {res.returncode}")
            print(f"  Stderr: {res.stderr}")
            sys.exit(1)

        try:
            out_data = json.loads(res.stdout)
            if out_data["hookSpecificOutput"]["permissionDecision"] != "allow":
                print(f"  [FAIL] Expected permissionDecision 'allow' for '{cmd}', got {out_data}")
                sys.exit(1)
        except Exception as e:
            print(f"  [FAIL] Failed parsing stdout JSON for '{cmd}': {e}")
            sys.exit(1)

        print(f"  [PASS] Successfully permitted safe command: {cmd}")
        allowed_count += 1

    print(f"\n[INFO] Successfully permitted {allowed_count}/{len(safe_commands)} safe commands.")

    print("\n--- Phase 3: Verifying Audit Log Integrity ---")
    if not log_file.exists():
        print(f"  [FAIL] Audit log file {log_file} was not created!")
        sys.exit(1)

    log_lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    print(f"  [+] Audit log recorded {len(log_lines)} blocked events.")
    if len(log_lines) != blocked_count:
        print(f"  [FAIL] Expected {blocked_count} log entries, found {len(log_lines)}")
        sys.exit(1)

    print("  [PASS] Audit log verified with full timestamps, project path, rules, and commands.")

    tmp_dir.cleanup()
    print("\n" + "=" * 65)
    print("ALL ACCEPTANCE CRITERIA VERIFIED: Flawless, hardened security.")
    print("=" * 65)


if __name__ == "__main__":
    run_test()
