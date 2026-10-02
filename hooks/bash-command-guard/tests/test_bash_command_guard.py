#!/usr/bin/env python3
"""
Comprehensive automated test suite for bash-command-guard hook.

Verifies:
  1. Blocks rm -rf and combinations (rm -rf, rm -fr, rm -r -f, rm --recursive --force)
  2. Blocks DROP TABLE, DROP DATABASE, DROP SCHEMA, DROP VIEW, DROP INDEX
  3. Blocks git push --force, git push -f, git push --force-with-lease, git push +ref
  4. Blocks TRUNCATE, TRUNCATE TABLE
  5. Blocks DELETE FROM without WHERE clause
  6. Allows safe operations: ls, git status, rm file.txt, rm -r dir, rm -f file, safe queries with WHERE
  7. Logging verification: checks JSON format, timestamp, project_path, and command in blocked.log
  8. End-to-end execution testing with Claude Code hook stdin JSON payloads and exit codes (2 = blocked, 0 = allowed)
"""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path

# Add hook module directory to sys.path
HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))

import importlib
hook = importlib.import_module("bash-command-guard")

def run_unit_tests():
    test_cases = [
        # --- BLOCKED: rm -rf variants ---
        ("rm -rf /", True, "rm-rf"),
        ("rm -rf /var/log/*", True, "rm-rf"),
        ("rm -fr dist/", True, "rm-rf"),
        ("rm -r -f build/", True, "rm-rf"),
        ("rm -f -r node_modules", True, "rm-rf"),
        ("rm -rfi critical_data", True, "rm-rf"),
        ("rm --recursive --force cache/", True, "rm-rf"),
        ("/bin/rm -rf /tmp/data", True, "rm-rf"),
        ("cd /tmp && rm -rf repo", True, "rm-rf"),

        # --- BLOCKED: DROP TABLE / DDL ---
        ("DROP TABLE users;", True, "sql-drop"),
        ("psql -U postgres -d app -c 'DROP TABLE accounts;'", True, "sql-drop"),
        ("mysql -e 'DROP DATABASE production'", True, "sql-drop"),
        ("sqlite3 app.db 'DROP TABLE sessions'", True, "sql-drop"),
        ("DROP SCHEMA public CASCADE", True, "sql-drop"),
        ("DROP VIEW customer_overview", True, "sql-drop"),
        ("DROP INDEX idx_user_email", True, "sql-drop"),

        # --- BLOCKED: git push --force ---
        ("git push origin main --force", True, "git-force-push"),
        ("git push -f origin main", True, "git-force-push"),
        ("git push origin --force-with-lease", True, "git-force-push"),
        ("git push --force origin feat/branch", True, "git-force-push"),
        ("git push origin +feat/branch:main", True, "git-force-push"),
        ("git -C /repo push -f", True, "git-force-push"),

        # --- BLOCKED: TRUNCATE ---
        ("TRUNCATE TABLE audit_logs;", True, "sql-truncate"),
        ("TRUNCATE payments", True, "sql-truncate"),
        ("psql -c 'TRUNCATE TABLE users RESTART IDENTITY'", True, "sql-truncate"),

        # --- BLOCKED: DELETE FROM without WHERE ---
        ("DELETE FROM users;", True, "sql-delete-no-where"),
        ("DELETE FROM sessions", True, "sql-delete-no-where"),
        ("psql -c 'DELETE FROM orders'", True, "sql-delete-no-where"),
        ("SELECT 1; DELETE FROM cache;", True, "sql-delete-no-where"),
        ("echo test && mysql -e 'DELETE FROM audit_events;'", True, "sql-delete-no-where"),

        # --- ALLOWED: Normal / Safe Commands ---
        ("ls -la", False, ""),
        ("pwd", False, ""),
        ("git status", False, ""),
        ("git diff HEAD~1", False, ""),
        ("git push origin main", False, ""),
        ("git push", False, ""),
        ("rm file.txt", False, ""),
        ("rm -r safe_dir/", False, ""),
        ("rm -f temporary.log", False, ""),
        ("rm -i prompt.txt", False, ""),
        ("SELECT * FROM users;", False, ""),
        ("SELECT * FROM users WHERE status = 'active';", False, ""),
        ("DELETE FROM users WHERE id = 12345;", False, ""),
        ("DELETE FROM users WHERE email = 'test@example.com' AND active = false;", False, ""),
        ("DELETE FROM sessions WHERE expires_at < NOW();", False, ""),
        ("npm test", False, ""),
        ("pytest -v", False, ""),
        ("cargo check", False, ""),
        ("cat << 'EOF' > test.sql\nSELECT * FROM users;\nEOF", False, ""),
        ("echo 'DROP TABLE users is an anti-pattern in production'", False, ""),
    ]

    print(f"Running {len(test_cases)} rule matching tests...")
    failures = 0
    for cmd, expected_blocked, expected_rule in test_cases:
        blocked, rule, _ = hook.check_destructive_command(cmd)
        if blocked != expected_blocked:
            print(f"❌ FAIL: '{cmd}' | Expected blocked={expected_blocked}, got {blocked}")
            failures += 1
        elif expected_blocked and rule != expected_rule:
            print(f"❌ FAIL: '{cmd}' | Expected rule={expected_rule}, got {rule}")
            failures += 1

    if failures == 0:
        print(f"✅ All {len(test_cases)} rule matching tests passed!\n")
    else:
        print(f"❌ {failures} tests failed!\n")
        return False
    return True

def run_e2e_cli_and_logging_tests():
    print("Running CLI execution and log verification tests...")
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_log = Path(temp_dir) / "test_blocked.log"
        hook_script = HOOK_DIR / "bash-command-guard.py"

        # Monkey-patch LOG_FILE for module test
        original_log = hook.LOG_FILE
        hook.LOG_FILE = fake_log

        # 1. Test CLI invocation with JSON payload via stdin (exit 2 for blocked)
        blocked_payload = json.dumps({
            "tool_input": {
                "command": "rm -rf /tmp/test"
            },
            "project_path": "/home/user/project"
        })

        proc = subprocess.run(
            [sys.executable, str(hook_script)],
            input=blocked_payload,
            text=True,
            capture_output=True,
            env={**os.environ, "HOME": temp_dir}
        )

        assert proc.returncode == 2, f"Expected returncode 2 for blocked command, got {proc.returncode}"
        assert "[BLOCKED BY SECURITY HOOK]" in proc.stderr, "Expected blocked banner in stderr"
        assert "rm-rf" in proc.stderr, "Expected rule name in stderr"

        # 2. Test CLI invocation for allowed command (exit 0)
        allowed_payload = json.dumps({
            "tool_input": {
                "command": "git status"
            },
            "project_path": "/home/user/project"
        })

        proc_allowed = subprocess.run(
            [sys.executable, str(hook_script)],
            input=allowed_payload,
            text=True,
            capture_output=True,
            env={**os.environ, "HOME": temp_dir}
        )

        assert proc_allowed.returncode == 0, f"Expected returncode 0 for allowed command, got {proc_allowed.returncode}"

        # 3. Check blocked.log content
        created_log = Path(temp_dir) / ".claude" / "hooks" / "blocked.log"
        assert created_log.exists(), f"Log file was not created at {created_log}"

        with open(created_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1, f"Expected 1 logged blocked command, found {len(lines)}"
            log_data = json.loads(lines[0])
            assert log_data["command"] == "rm -rf /tmp/test"
            assert log_data["project_path"] == "/home/user/project"
            assert "timestamp" in log_data
            assert log_data["reason"] == "rm-rf"

        hook.LOG_FILE = original_log
        print("✅ CLI execution and log verification passed!\n")
    return True

if __name__ == "__main__":
    t1 = run_unit_tests()
    t2 = run_e2e_cli_and_logging_tests()
    if t1 and t2:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        sys.exit(1)
