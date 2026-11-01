"""
Unit and Integration Test Suite for Claude Code Pre-Tool-Use Destructive Command Blocker.
Validates all acceptance criteria:
- Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
- Allows: safe commands (rm file.txt, git push, SELECT *, DELETE FROM with WHERE)
- Audit logging to ~/.claude/hooks/blocked.log
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add hooks directory to python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

from block_destructive import (
    inspect_command,
    check_delete_without_where,
    log_blocked_attempt,
    get_log_file_path,
)


class TestDestructiveCommandPatterns:
    """Tests the detection engine against destructive and benign commands."""

    # 1. rm -rf variations (Blocked)
    @pytest.mark.parametrize(
        "cmd",
        [
            "rm -rf /",
            "rm -rf /var/data",
            "rm -fr ./build",
            "rm -r -f node_modules",
            "rm --recursive --force .git",
            "rm -f -r cache",
            "sudo rm -rf /etc",
            "rm -rf *",
            "echo 'cleaning' && rm -rf temp",
            "cd /tmp; rm -rf build/",
        ],
    )
    def test_block_rm_rf(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is True
        assert "Recursive force removal" in reason

    # Safe rm commands (Allowed)
    @pytest.mark.parametrize(
        "cmd",
        [
            "rm output.txt",
            "rm -f single_file.log",
            "rm -r empty_dir",  # recursive without force is prompt-safe
            "rm ./test.py",
        ],
    )
    def test_allow_safe_rm(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is False
        assert reason is None

    # 2. DROP TABLE / DATABASE / SCHEMA (Blocked)
    @pytest.mark.parametrize(
        "cmd",
        [
            "DROP TABLE users;",
            "drop table `accounts`",
            "DROP DATABASE production;",
            "DROP SCHEMA public CASCADE",
            "psql -c 'DROP TABLE customers;'",
            "sqlite3 app.db \"drop table sessions\"",
        ],
    )
    def test_block_drop(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is True
        assert "Database drop commands" in reason

    # Safe DB commands (Allowed)
    @pytest.mark.parametrize(
        "cmd",
        [
            "SELECT * FROM users;",
            "CREATE TABLE IF NOT EXISTS logs (id INT);",
            "ALTER TABLE users ADD COLUMN age INT;",
            "echo 'Dropping by the store'",
        ],
    )
    def test_allow_safe_db(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is False

    # 3. git push --force variations (Blocked)
    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force",
            "git push origin main --force",
            "git push -f",
            "git push origin master -f",
            "git push --force-with-lease",
            "git push origin dev --force-with-lease",
            "git -C repo push --force",
        ],
    )
    def test_block_git_force_push(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is True
        assert "Git force pushing" in reason

    # Safe git push commands (Allowed)
    @pytest.mark.parametrize(
        "cmd",
        [
            "git push",
            "git push origin main",
            "git push -u origin feature-branch",
            "git status",
            "git log -n 5",
        ],
    )
    def test_allow_safe_git(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is False

    # 4. TRUNCATE variations (Blocked)
    @pytest.mark.parametrize(
        "cmd",
        [
            "TRUNCATE TABLE users;",
            "truncate table `orders`",
            "TRUNCATE sessions;",
            "psql -c 'TRUNCATE TABLE payments;'",
        ],
    )
    def test_block_truncate(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is True
        assert "Database truncation" in reason

    # 5. DELETE FROM without WHERE (Blocked)
    @pytest.mark.parametrize(
        "cmd",
        [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `sessions`;",
            "sqlite3 test.db 'DELETE FROM logs'",
        ],
    )
    def test_block_delete_without_where(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is True
        assert "without a WHERE clause" in reason

    # DELETE FROM with WHERE (Allowed)
    @pytest.mark.parametrize(
        "cmd",
        [
            "DELETE FROM users WHERE id = 42;",
            "delete from sessions where expired_at < NOW()",
            "DELETE FROM `logs` WHERE created_at < '2026-01-01';",
        ],
    )
    def test_allow_delete_with_where(self, cmd):
        is_blocked, reason = inspect_command(cmd)
        assert is_blocked is False


class TestAuditLogging:
    """Verifies that blocked commands are accurately written to blocked.log."""

    def test_log_blocked_attempt(self, tmp_path, monkeypatch):
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setenv("HOME", str(mock_home))
        monkeypatch.setenv("USERPROFILE", str(mock_home))

        log_blocked_attempt(
            command="rm -rf /critical/data",
            reason="Recursive force removal",
            project_path="/workspace/app",
        )

        expected_log = mock_home / ".claude" / "hooks" / "blocked.log"
        assert expected_log.exists()
        content = expected_log.read_text(encoding="utf-8")
        assert "BLOCKED" in content
        assert "rm -rf /critical/data" in content
        assert "Recursive force removal" in content
        assert "/workspace/app" in content
