import sys
import os
import tempfile
from pathlib import Path
import pytest

# Add hooks directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "pre-tool-use"))
from block_destructive import check_command, log_blocked_attempt

def test_rm_rf_variants_blocked():
    blocked_commands = [
        "rm -rf /",
        "rm -rf ./node_modules",
        "rm -r -f /var/data",
        "rm -fr .git",
        "sudo rm -rf /etc"
    ]
    for cmd in blocked_commands:
        is_blocked, reason = check_command(cmd)
        assert is_blocked is True, f"Failed to block: {cmd}"
        assert "rm -rf" in reason

def test_git_force_push_blocked():
    blocked_commands = [
        "git push --force origin main",
        "git push -f",
        "git push --force",
        "git push origin +main"
    ]
    for cmd in blocked_commands:
        is_blocked, reason = check_command(cmd)
        assert is_blocked is True, f"Failed to block: {cmd}"
        assert "force" in reason.lower()

def test_database_destructive_blocked():
    blocked_commands = [
        "DROP TABLE users;",
        "drop table if exists accounts;",
        "DROP DATABASE production;",
        "TRUNCATE TABLE session_logs;",
        "TRUNCATE analytics;",
        "DELETE FROM customers;",
        "delete from orders"
    ]
    for cmd in blocked_commands:
        is_blocked, reason = check_command(cmd)
        assert is_blocked is True, f"Failed to block: {cmd}"

def test_benign_commands_allowed():
    safe_commands = [
        "ls -la",
        "git status",
        "git push origin feat/my-branch",
        "npm run build",
        "pytest tests/",
        "rm file.txt",
        "rm -r empty_directory",
        "DELETE FROM users WHERE id = 42;",
        "delete from sessions where expired_at < NOW();",
        "SELECT * FROM users WHERE active = true;"
    ]
    for cmd in safe_commands:
        is_blocked, reason = check_command(cmd)
        assert is_blocked is False, f"Erroneously blocked safe command: {cmd} with reason: {reason}"

def test_logging_format(tmp_path):
    log_file = tmp_path / "blocked.log"
    log_blocked_attempt(
        command="rm -rf /test",
        reason="Test blocked reason",
        project_path="/home/user/project",
        log_file=log_file
    )

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "PATH: /home/user/project" in content
    assert "REASON: Test blocked reason" in content
    assert "COMMAND: rm -rf /test" in content
