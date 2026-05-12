"""Tests for the pre_tool_use destructive-command safety hook."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from pre_tool_use import check, is_delete_without_where, main


# ---------------------------------------------------------------------------
# Unit tests: check()
# ---------------------------------------------------------------------------

class TestSafeCommands:
    def test_ls(self):
        blocks, warns = check("ls -la")
        assert blocks == []

    def test_echo(self):
        blocks, warns = check("echo hello world")
        assert blocks == []

    def test_git_status(self):
        blocks, warns = check("git status")
        assert blocks == []

    def test_git_commit(self):
        blocks, warns = check("git commit -m 'fix: update README'")
        assert blocks == []

    def test_git_push_normal(self):
        blocks, warns = check("git push origin main")
        assert blocks == []

    def test_delete_with_where(self):
        blocks, warns = check("DELETE FROM users WHERE id = 42;")
        assert blocks == []

    def test_delete_with_where_multiline(self):
        blocks, warns = check("DELETE FROM sessions\nWHERE created_at < NOW() - INTERVAL '30 days';")
        assert blocks == []

    def test_select_from(self):
        blocks, warns = check("SELECT * FROM users;")
        assert blocks == []

    def test_npm_install(self):
        blocks, warns = check("npm install")
        assert blocks == []

    def test_rm_single_file(self):
        blocks, warns = check("rm somefile.txt")
        assert blocks == []

    def test_rm_minus_r_no_f(self):
        blocks, warns = check("rm -r old_dir/")
        assert blocks == []


class TestBlockedCommands:
    def test_rm_rf(self):
        blocks, _ = check("rm -rf /tmp/foo")
        assert any("rm -rf" in b for b in blocks)

    def test_rm_fr(self):
        blocks, _ = check("rm -fr /tmp/foo")
        assert any("rm -rf" in b or "rm" in b for b in blocks)

    def test_rm_flags_reordered(self):
        # flags can appear as -r -f or combined in different order
        blocks, _ = check("rm -r -f /tmp/data")
        assert any("rm" in b for b in blocks)

    def test_rm_no_preserve_root(self):
        blocks, _ = check("rm --no-preserve-root /")
        assert any("no-preserve-root" in b for b in blocks)

    def test_dd_to_block_device(self):
        blocks, _ = check("dd if=/dev/zero of=/dev/sda")
        assert any("block device" in b for b in blocks)

    def test_redirect_to_sda(self):
        blocks, _ = check("cat /dev/zero > /dev/sda")
        assert any("block device" in b for b in blocks)

    def test_drop_table(self):
        blocks, _ = check("DROP TABLE users;")
        assert any("DROP" in b for b in blocks)

    def test_drop_database(self):
        blocks, _ = check("DROP DATABASE production;")
        assert any("DROP" in b for b in blocks)

    def test_drop_schema(self):
        blocks, _ = check("DROP SCHEMA public CASCADE;")
        assert any("DROP" in b for b in blocks)

    def test_truncate_table(self):
        blocks, _ = check("TRUNCATE TABLE sessions;")
        assert any("TRUNCATE" in b for b in blocks)

    def test_truncate_no_table_keyword(self):
        blocks, _ = check("TRUNCATE events;")
        assert any("TRUNCATE" in b for b in blocks)

    def test_delete_without_where(self):
        blocks, _ = check("DELETE FROM users;")
        assert any("WHERE" in b for b in blocks)

    def test_delete_without_where_multiline(self):
        blocks, _ = check("DELETE\nFROM\norders;")
        assert any("WHERE" in b for b in blocks)

    def test_git_push_force(self):
        blocks, _ = check("git push --force")
        assert any("force" in b for b in blocks)

    def test_git_push_f(self):
        blocks, _ = check("git push -f origin main")
        assert any("force" in b for b in blocks)

    def test_git_push_uppercase_F(self):
        blocks, _ = check("git push -F origin main")
        assert any("force" in b for b in blocks)

    def test_chmod_777_root(self):
        blocks, _ = check("chmod 777 /etc")
        assert any("chmod" in b for b in blocks)

    def test_chmod_recursive_777_root(self):
        blocks, _ = check("chmod -R 777 /usr")
        assert any("chmod" in b for b in blocks)


class TestWarnOnly:
    def test_force_with_lease_not_blocked(self):
        blocks, warns = check("git push --force-with-lease")
        assert blocks == []
        assert any("force-with-lease" in w for w in warns)


class TestDeleteWithoutWhere:
    def test_simple_delete_no_where(self):
        assert is_delete_without_where("DELETE FROM logs;") is True

    def test_delete_with_where(self):
        assert is_delete_without_where("DELETE FROM logs WHERE ts < '2020-01-01';") is False

    def test_multiline_delete_with_where(self):
        sql = "DELETE FROM sessions\n  WHERE user_id = $1\n  AND expired = true;"
        assert is_delete_without_where(sql) is False

    def test_multiline_delete_no_where(self):
        sql = "DELETE\nFROM\narchive_data;"
        assert is_delete_without_where(sql) is True


# ---------------------------------------------------------------------------
# Integration: main() via stdin/stdout
# ---------------------------------------------------------------------------

def run_hook(payload: dict) -> dict | None:
    """Run main() with the given payload and return parsed stdout JSON if any."""
    stdin = StringIO(json.dumps(payload))
    stdout = StringIO()
    with patch("sys.stdin", stdin), patch("sys.stdout", stdout):
        try:
            main()
        except SystemExit:
            pass
    output = stdout.getvalue().strip()
    return json.loads(output) if output else None


class TestMainIntegration:
    def test_safe_command_no_output(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert result is None

    def test_rm_rf_blocked(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}})
        assert result is not None
        assert result["decision"] == "block"
        assert "rm" in result["reason"].lower()

    def test_drop_table_blocked(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "psql -c 'DROP TABLE users'"}})
        assert result is not None
        assert result["decision"] == "block"

    def test_non_bash_tool_ignored(self):
        result = run_hook({"tool_name": "Read", "tool_input": {"path": "/etc/passwd"}})
        assert result is None

    def test_empty_stdin(self):
        stdin = StringIO("")
        with patch("sys.stdin", stdin):
            try:
                main()
            except SystemExit:
                pass

    def test_malformed_json(self):
        stdin = StringIO("{not valid json}")
        with patch("sys.stdin", stdin):
            try:
                main()
            except SystemExit:
                pass

    def test_delete_without_where_blocked(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "psql -c 'DELETE FROM events'"}})
        assert result is not None
        assert result["decision"] == "block"

    def test_git_push_force_blocked(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}})
        assert result is not None
        assert result["decision"] == "block"

    def test_git_push_force_with_lease_allowed(self):
        result = run_hook({"tool_name": "Bash", "tool_input": {"command": "git push --force-with-lease"}})
        assert result is None
