#!/usr/bin/env python3
"""
Comprehensive tests for block_destructive.py

Run: python3 -m pytest tests/test_block_destructive.py -v
"""

import json
import os
import sys
import tempfile

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks"))

import block_destructive as hook


def _make_input(command: str) -> dict:
    return {"tool_input": {"command": command}}


def _run_check(command: str) -> tuple[bool, str | None]:
    """Run check_command, return (was_blocked, reason_or_none)."""
    import io

    old_stdout = sys.stdout
    old_exit = sys.exit
    captured = io.StringIO()
    blocked = False
    reason = None

    def mock_exit(code=0):
        nonlocal blocked
        blocked = True
        raise SystemExit(code)

    sys.stdout = captured
    sys.exit = mock_exit

    try:
        hook.check_command(command)
    except SystemExit:
        pass
    finally:
        sys.stdout = old_stdout
        sys.exit = old_exit

    if blocked:
        output = captured.getvalue()
        try:
            data = json.loads(output.strip())
            reason = data["hookSpecificOutput"]["permissionDecisionReason"]
        except (json.JSONDecodeError, KeyError):
            pass

    return blocked, reason


# --- Should BLOCK ---

class TestBlocked:
    def test_rm_rf(self):
        blocked, _ = _run_check("rm -rf /tmp/test")
        assert blocked

    def test_rm_rf_variant(self):
        blocked, _ = _run_check("rm -fr /tmp/test")
        assert blocked

    def test_rm_rf_long_flags(self):
        blocked, _ = _run_check("rm --recursive --force /tmp/test")
        assert blocked

    def test_rm_rf_with_other_flags(self):
        blocked, _ = _run_check("rm -arfv /important")
        assert blocked

    def test_drop_table(self):
        blocked, _ = _run_check("DROP TABLE users;")
        assert blocked

    def test_drop_table_lowercase(self):
        blocked, _ = _run_check("drop table users;")
        assert blocked

    def test_drop_database(self):
        blocked, _ = _run_check("DROP DATABASE production;")
        assert blocked

    def test_drop_schema(self):
        blocked, _ = _run_check("DROP SCHEMA public;")
        assert blocked

    def test_git_push_force(self):
        blocked, _ = _run_check("git push --force origin main")
        assert blocked

    def test_git_push_f(self):
        blocked, _ = _run_check("git push -f origin main")
        assert blocked

    def test_truncate(self):
        blocked, _ = _run_check("TRUNCATE TABLE logs;")
        assert blocked

    def test_truncate_no_table_keyword(self):
        blocked, _ = _run_check("TRUNCATE logs;")
        assert blocked

    def test_delete_from_no_where(self):
        blocked, _ = _run_check("DELETE FROM users;")
        assert blocked

    def test_delete_from_lowercase_no_where(self):
        blocked, _ = _run_check("delete from users")
        assert blocked

    def test_delete_from_multiline_no_where(self):
        blocked, _ = _run_check("DELETE\nFROM\nusers;")
        assert blocked


# --- Should ALLOW ---

class TestAllowed:
    def test_normal_rm(self):
        blocked, _ = _run_check("rm /tmp/single_file.txt")
        assert not blocked

    def test_rm_i(self):
        blocked, _ = _run_check("rm -i /tmp/test")
        assert not blocked

    def test_rm_r_no_f(self):
        blocked, _ = _run_check("rm -r /tmp/test")
        assert not blocked

    def test_git_push_normal(self):
        blocked, _ = _run_check("git push origin main")
        assert not blocked

    def test_git_push_force_with_lease(self):
        """--force-with-lease is safe — it checks remote ref."""
        blocked, _ = _run_check("git push --force-with-lease origin main")
        assert not blocked

    def test_delete_from_with_where(self):
        blocked, _ = _run_check("DELETE FROM users WHERE id = 5;")
        assert not blocked

    def test_select(self):
        blocked, _ = _run_check("SELECT * FROM users;")
        assert not blocked

    def test_insert(self):
        blocked, _ = _run_check("INSERT INTO users (name) VALUES ('test');")
        assert not blocked

    def test_update_with_where(self):
        blocked, _ = _run_check("UPDATE users SET name='x' WHERE id=1;")
        assert not blocked

    def test_ls(self):
        blocked, _ = _run_check("ls -la /tmp")
        assert not blocked

    def test_cargo_build(self):
        blocked, _ = _run_check("cargo build --release")
        assert not blocked

    def test_pip_install(self):
        blocked, _ = _run_check("pip install -r requirements.txt")
        assert not blocked

    def test_empty_command(self):
        blocked, _ = _run_check("")
        assert not blocked

    def test_whitespace_only(self):
        blocked, _ = _run_check("   ")
        assert not blocked


# --- Log format ---

class TestLogging:
    def test_blocked_attempt_is_logged(self, tmp_path, monkeypatch):
        log_dir = str(tmp_path)
        log_file = os.path.join(log_dir, "blocked.log")
        monkeypatch.setattr(hook, "LOG_DIR", log_dir)
        monkeypatch.setattr(hook, "LOG_FILE", log_file)

        blocked, _ = _run_check("rm -rf /tmp/test")
        assert blocked
        assert os.path.exists(log_file)

        with open(log_file) as f:
            entry = json.loads(f.readline())
        assert entry["event"] == "BLOCKED"
        assert "rm -rf" in entry["command"]
        assert "timestamp" in entry
        assert "cwd" in entry

    def test_allowed_command_not_logged(self, tmp_path, monkeypatch):
        log_dir = str(tmp_path)
        log_file = os.path.join(log_dir, "blocked.log")
        monkeypatch.setattr(hook, "LOG_DIR", log_dir)
        monkeypatch.setattr(hook, "LOG_FILE", log_file)

        blocked, _ = _run_check("ls -la")
        assert not blocked
        assert not os.path.exists(log_file)


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
