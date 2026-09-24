#!/usr/bin/env python3
"""
Comprehensive Test Suite for Pre-Tool-Use Guard Hook
Tests blocked commands, pipeline combinations, permitted commands, Claude Code JSON payloads, and audit logging.
"""
import subprocess
import sys
import os
import json
import tempfile

def run_guard(cmd_str: str) -> tuple[int, str, str]:
    script = os.path.abspath("pre_tool_use_guard.py")
    env = os.environ.copy()
    env["CLAUDE_HOOKS_DIR"] = os.path.abspath(".test_logs")
    res = subprocess.run([sys.executable, script, cmd_str], capture_output=True, text=True, env=env)
    return res.returncode, res.stdout, res.stderr

def run_guard_stdin(json_payload: dict) -> tuple[int, str, str]:
    script = os.path.abspath("pre_tool_use_guard.py")
    env = os.environ.copy()
    env["CLAUDE_HOOKS_DIR"] = os.path.abspath(".test_logs")
    raw_in = json.dumps(json_payload)
    res = subprocess.run([sys.executable, script], input=raw_in, capture_output=True, text=True, env=env)
    return res.returncode, res.stdout, res.stderr

def test_guard_rules():
    blocked_test_cases = [
        "rm -rf /tmp/data",
        "rm -fr ./cache",
        "rm -r -f /var/log",
        "rm --recursive --force ./dist",
        "mkdir /tmp/build && rm -rf /tmp/build",
        "cd /var/www; rm -fr cache/",
        "DROP TABLE users;",
        "drop database production;",
        "DROP VIEW user_summary",
        "git push origin main --force",
        "git push -f origin feat",
        "git push origin feat --force-with-lease",
        "TRUNCATE TABLE audit_logs;",
        "truncate users",
        "DELETE FROM users;",
        "delete from accounts"
    ]

    for cmd in blocked_test_cases:
        code, stdout, stderr = run_guard(cmd)
        assert code == 1, f"Failed to block dangerous command: {cmd} (exit code: {code})"
        assert "SECURITY HOOK BLOCKED COMMAND" in stderr, f"Expected error message missing for {cmd}"
        print(f"  [✓] Successfully blocked: {cmd}")

    allowed_test_cases = [
        "ls -la",
        "cat package.json",
        "git status",
        "git commit -m 'feat: add security hook to prevent DROP TABLE'",
        "git push origin main",
        "git pull --rebase",
        "pytest -v",
        "npm test",
        "rm file.txt",
        "DELETE FROM users WHERE id = 123;",
        "python3 script.py",
        "echo 'DROP TABLE users' is dangerous",
        "echo 'Do not run rm -rf on root'"
    ]

    for cmd in allowed_test_cases:
        code, stdout, stderr = run_guard(cmd)
        assert code == 0, f"Incorrectly blocked safe command: {cmd} (exit code: {code}, stderr: {stderr})"
        print(f"  [✓] Successfully allowed: {cmd}")

    # Test Claude Code JSON payload through stdin
    json_blocked = {"tool": "bash", "command": "rm -rf ~/.local/share"}
    code, stdout, stderr = run_guard_stdin(json_blocked)
    assert code == 1, "Failed to block dangerous command via stdin JSON payload"
    print("  [✓] Successfully blocked dangerous command via Claude Code JSON payload")

    json_allowed = {"tool": "bash", "command": "git log -n 5"}
    code, stdout, stderr = run_guard_stdin(json_allowed)
    assert code == 0, "Incorrectly blocked safe command via stdin JSON payload"
    print("  [✓] Successfully allowed safe command via Claude Code JSON payload")

    # Check log file
    log_file = os.path.abspath(".test_logs/blocked.log")
    assert os.path.exists(log_file), "Audit log file was not created"
    with open(log_file, "r") as f:
        log_content = f.read()
    assert "rm -rf" in log_content
    assert "DROP TABLE" in log_content

    print("\n[✓] ALL PRE-TOOL-USE GUARD ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_guard_rules()
