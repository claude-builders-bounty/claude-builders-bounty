"""
Unit tests for Claude Code PreToolUse Destructive Command Blocker.
Verifies:
1. All dangerous commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE) are blocked.
2. Safe commands (ls, git status, targeted rm, DELETE FROM with WHERE, git push origin branch) pass through with zero interference.
3. Blocked attempts are recorded to the log file with timestamp, command, and project path.
4. Correct Claude Code PreToolUse JSON deny schema is output.
"""

import json
import os
import subprocess
import tempfile
import sys
from pathlib import Path
import pytest

from block_destructive_commands import inspect_command, check_unbounded_delete


@pytest.mark.parametrize(
    "command,expected_blocked",
    [
        # --- BLOCKED: rm -rf variants ---
        ("rm -rf /tmp/test", True),
        ("rm -fr ./build", True),
        ("rm -r -f node_modules", True),
        ("rm -f -r dist", True),
        ("rm -Rf .cache", True),
        ("rm --recursive --force vendor", True),
        ("rm --force --recursive temp", True),
        ("cd src && rm -rf build", True),
        ("rm -rf *", True),
        
        # --- BLOCKED: DROP TABLE / DATABASE ---
        ("DROP TABLE users;", True),
        ("drop table if exists accounts", True),
        ("DROP TEMPORARY TABLE session_tokens", True),
        ("DROP DATABASE production_db", True),
        ("DROP SCHEMA public CASCADE", True),
        ("psql -c 'DROP TABLE customers;'", True),

        # --- BLOCKED: git push --force variants ---
        ("git push --force origin main", True),
        ("git push -f origin master", True),
        ("git push origin feature-branch --force", True),
        ("git push --force-with-lease origin main", True),
        ("git push -f", True),

        # --- BLOCKED: TRUNCATE ---
        ("TRUNCATE TABLE audit_logs;", True),
        ("truncate orders", True),
        ("TRUNCATE events", True),

        # --- BLOCKED: DELETE FROM without WHERE ---
        ("DELETE FROM users;", True),
        ("delete from orders", True),
        ("DELETE FROM `sessions`;", True),
        ("DELETE FROM \"user_accounts\"", True),
        ("sqlite3 prod.db 'DELETE FROM transactions'", True),
        ("SELECT * FROM items; DELETE FROM inventory; SELECT 1;", True),

        # --- ALLOWED / SAFE COMMANDS ---
        ("ls -la", False),
        ("git status", False),
        ("git add .", False),
        ("git commit -m 'feat: add hook'", False),
        ("git push origin feature-branch", False),
        ("git push", False),
        ("rm safe_file.txt", False),
        ("rm -f single_file.log", False),
        ("rmdir empty_dir", False),
        ("cat package.json", False),
        ("npm run build", False),
        ("python script.py", False),
        ("pytest tests/", False),
        ("DELETE FROM users WHERE id = 42;", False),
        ("DELETE FROM orders WHERE status = 'cancelled' AND created_at < NOW();", False),
        ("SELECT * FROM users WHERE active = 1;", False),
    ],
)
def test_inspect_command(command, expected_blocked):
    reason = inspect_command(command)
    if expected_blocked:
        assert reason is not None, f"Expected '{command}' to be blocked, but it was allowed."
    else:
        assert reason is None, f"Expected '{command}' to be allowed, but it was blocked: {reason}"


def test_end_to_end_blocked_execution(tmp_path, monkeypatch):
    """
    Test running the hook script via stdin JSON payload when command should be blocked.
    """
    hook_script = Path(__file__).parent / "block_destructive_commands.py"
    
    # Mock HOME to tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    
    payload = {
        "hookEventName": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /critical/data"},
        "cwd": "/home/user/project",
    }
    
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=os.environ,
    )
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "rm -rf" in output["hookSpecificOutput"]["permissionDecisionReason"]

    # Verify log entry was created
    log_file = tmp_path / ".claude" / "hooks" / "blocked.log"
    assert log_file.exists()
    
    log_lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    log_data = json.loads(log_lines[0])
    assert log_data["command"] == "rm -rf /critical/data"
    assert log_data["project_path"] == "/home/user/project"
    assert "timestamp" in log_data


def test_end_to_end_allowed_execution(tmp_path, monkeypatch):
    """
    Test running the hook script via stdin JSON payload when command is safe.
    """
    hook_script = Path(__file__).parent / "block_destructive_commands.py"
    monkeypatch.setenv("HOME", str(tmp_path))
    
    payload = {
        "hookEventName": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git status"},
        "cwd": "/home/user/project",
    }
    
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=os.environ,
    )
    
    assert result.returncode == 0
    # Output should be empty for allowed commands
    assert result.stdout.strip() == ""

    # Verify log file was NOT created
    log_file = tmp_path / ".claude" / "hooks" / "blocked.log"
    assert not log_file.exists()
