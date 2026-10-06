#!/usr/bin/env python3
"""
Unit tests for Claude Code Pre-Tool-Use Security Hook
"""

import sys
import os
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib.machinery import SourceFileLoader

hook_module = SourceFileLoader("pre_tool_use", str(Path(__file__).resolve().parent / "pre-tool-use.py")).load_module()
check_command = hook_module.check_command

def test_blocked_commands():
    dangerous_cases = [
        # rm -rf variants
        "rm -rf /tmp/cache",
        "rm -rf node_modules",
        "rm -fr dist",
        "rm -r -f build",
        "rm -rf .git",
        # DROP TABLE
        "DROP TABLE accounts;",
        "drop table users",
        "sqlite3 app.db 'DROP TABLE sessions;'",
        # git push --force
        "git push --force origin main",
        "git push origin master -f",
        "git push --force-with-lease origin feat",
        # TRUNCATE
        "TRUNCATE TABLE audit_logs;",
        "truncate table sessions",
        "truncate users",
        # DELETE FROM without WHERE
        "DELETE FROM users;",
        "DELETE FROM sessions",
        "delete from temporary_data;",
        # A WHERE in a later SQL statement must not make the earlier DELETE safe.
        "DELETE FROM users; DELETE FROM sessions WHERE id = 42;"
    ]

    print("Running DANGEROUS command tests...")
    for cmd in dangerous_cases:
        blocked, reason = check_command(cmd)
        assert blocked, f"Expected '{cmd}' to be BLOCKED, but it was ALLOWED!"
        print(f"  ✓ Blocked: {cmd} -> ({reason.split('.')[0]})")

def test_allowed_commands():
    safe_cases = [
        "ls -la",
        "npm install",
        "git status",
        "git push origin main",
        "git pull --rebase",
        "rm test_file.txt",
        "rm -f single_file.log",
        "SELECT * FROM users WHERE active = 1;",
        "DELETE FROM users WHERE id = 42;",
        "DELETE FROM sessions WHERE expired_at < NOW();",
        "pytest -v",
        "python server.py"
    ]

    print("\nRunning SAFE command tests...")
    for cmd in safe_cases:
        blocked, reason = check_command(cmd)
        assert not blocked, f"Expected '{cmd}' to be ALLOWED, but it was BLOCKED! ({reason})"
        print(f"  ✓ Allowed: {cmd}")

if __name__ == "__main__":
    test_blocked_commands()
    test_allowed_commands()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
