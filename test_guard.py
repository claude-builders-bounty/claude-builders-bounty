#!/usr/bin/env python3
"""Tests for destructive-command-guard — 30 tests covering all patterns."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add guard to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks" / "pre-tool-use"))

# Import the module — need to handle the __name__ check
import importlib.util
spec = importlib.util.spec_from_file_location(
    "guard",
    Path(__file__).resolve().parent / "hooks" / "pre-tool-use" / "destructive-command-guard.py",
)
guard = importlib.util.module_from_spec(spec)
# Prevent __main__ from running on import
guard.__name__ = "guard"
spec.loader.exec_module(guard)


class TestDangerousPatterns:
    """Tests 1-13: Each dangerous pattern is detected."""

    def test_rm_rf_standard(self):
        is_dangerous, pattern, _ = guard.check_command("rm -rf /tmp/cache")
        assert is_dangerous, "Should detect rm -rf"
        assert pattern["id"] == "RM_RF"

    def test_rm_rf_separate_flags(self):
        is_dangerous, pattern, _ = guard.check_command("rm -r -f /var/log")
        assert is_dangerous
        assert pattern["id"] == "RM_RF"

    def test_git_push_force(self):
        is_dangerous, pattern, _ = guard.check_command("git push --force origin main")
        assert is_dangerous
        assert pattern["id"] == "GIT_PUSH_FORCE"

    def test_git_push_f(self):
        is_dangerous, pattern, _ = guard.check_command("git push -f upstream dev")
        assert is_dangerous
        assert pattern["id"] == "GIT_PUSH_FORCE"

    def test_drop_table(self):
        is_dangerous, pattern, _ = guard.check_command("DROP TABLE users;")
        assert is_dangerous
        assert pattern["id"] == "DROP_TABLE"

    def test_drop_table_lowercase(self):
        is_dangerous, pattern, _ = guard.check_command("drop table orders cascade;")
        assert is_dangerous
        assert pattern["id"] == "DROP_TABLE"

    def test_drop_database(self):
        is_dangerous, pattern, _ = guard.check_command("DROP DATABASE production;")
        assert is_dangerous
        assert pattern["id"] == "DROP_DATABASE"

    def test_truncate(self):
        is_dangerous, pattern, _ = guard.check_command("TRUNCATE users;")
        assert is_dangerous
        assert pattern["id"] == "TRUNCATE"

    def test_truncate_table(self):
        is_dangerous, pattern, _ = guard.check_command("truncate table logs;")
        assert is_dangerous
        assert pattern["id"] == "TRUNCATE"

    def test_delete_from_without_where(self):
        is_dangerous, pattern, _ = guard.check_command("DELETE FROM users;")
        assert is_dangerous
        assert pattern["id"] == "DELETE_WITHOUT_WHERE"

    def test_dd_to_block_device(self):
        is_dangerous, pattern, _ = guard.check_command("dd if=/dev/zero of=/dev/sda bs=1M")
        assert is_dangerous
        assert pattern["id"] == "DD_DANGEROUS"

    def test_chmod_777_recursive(self):
        is_dangerous, pattern, _ = guard.check_command("chmod -R 777 /var/www")
        assert is_dangerous
        assert pattern["id"] == "CHMOD_777_RECURSIVE"

    def test_chown_recursive(self):
        is_dangerous, pattern, _ = guard.check_command("chown -R www-data:www-data /var/www")
        assert is_dangerous
        assert pattern["id"] == "CHOWN_RECURSIVE"

    def test_mkfs(self):
        is_dangerous, pattern, _ = guard.check_command("mkfs.ext4 /dev/sdb1")
        assert is_dangerous
        assert pattern["id"] == "MKFS"

    def test_shred(self):
        is_dangerous, pattern, _ = guard.check_command("shred -n 3 sensitive.doc")
        assert is_dangerous
        assert pattern["id"] == "SHRED"


class TestSafeCommands:
    """Tests 16-21: Safe commands pass through."""

    def test_safe_rm(self):
        is_dangerous, _, _ = guard.check_command("rm /tmp/tempfile.txt")
        assert not is_dangerous

    def test_git_push_without_force(self):
        is_dangerous, _, _ = guard.check_command("git push origin main")
        assert not is_dangerous

    def test_git_push_force_with_lease(self):
        is_dangerous, _, _ = guard.check_command("git push --force-with-lease origin main")
        assert not is_dangerous

    def test_delete_from_with_where(self):
        is_dangerous, _, _ = guard.check_command("DELETE FROM users WHERE id = 42;")
        assert not is_dangerous

    def test_select_query(self):
        is_dangerous, _, _ = guard.check_command("SELECT * FROM users;")
        assert not is_dangerous

    def test_safe_ls(self):
        is_dangerous, _, _ = guard.check_command("ls -la /tmp")
        assert not is_dangerous


class TestEdgeCases:
    """Tests 22-26: Edge cases handled correctly."""

    def test_empty_string(self):
        is_dangerous, _, _ = guard.check_command("")
        assert not is_dangerous

    def test_whitespace_only(self):
        is_dangerous, _, _ = guard.check_command("   ")
        assert not is_dangerous

    def test_none_value(self):
        is_dangerous, _, _ = guard.check_command(None)
        assert not is_dangerous

    def test_comment_only(self):
        is_dangerous, _, _ = guard.check_command("# rm -rf /")
        assert not is_dangerous, "Comments should not execute"

    def test_echoed_dangerous_string(self):
        is_dangerous, _, _ = guard.check_command('echo "rm -rf / is dangerous"')
        assert not is_dangerous, "echo of dangerous text should not trigger"


class TestLogging:
    """Tests 27-30: Logging works correctly."""

    def test_log_file_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "guard.log"
            os.environ["DESTRUCTIVE_GUARD_LOG"] = str(log_path)
            guard.log_attempt("rm -rf /tmp", {"id": "RM_RF", "description": "test", "suggestion": "test"}, Path("/project"))
            assert log_path.exists()
            content = log_path.read_text()
            assert "RM_RF" in content
            assert "rm -rf /tmp" in content
        del os.environ["DESTRUCTIVE_GUARD_LOG"]

    def test_log_entry_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "guard.log"
            os.environ["DESTRUCTIVE_GUARD_LOG"] = str(log_path)
            guard.log_attempt("DROP TABLE test", {"id": "DROP_TABLE", "description": "test", "suggestion": "Backup first"}, Path("/project"))
            lines = log_path.read_text().strip().split("\n")
            entry = json.loads(lines[0])
            assert "timestamp" in entry
            assert entry["command"] == "DROP TABLE test"
            assert entry["matched_pattern"] == "DROP_TABLE"
            assert entry["suggestion"] == "Backup first"
        del os.environ["DESTRUCTIVE_GUARD_LOG"]

    def test_multiple_log_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "guard.log"
            os.environ["DESTRUCTIVE_GUARD_LOG"] = str(log_path)
            patterns = [
                {"id": "RM_RF", "description": "a", "suggestion": "x"},
                {"id": "DROP_TABLE", "description": "b", "suggestion": "y"},
            ]
            guard.log_attempt("cmd1", patterns[0], Path("/p1"))
            guard.log_attempt("cmd2", patterns[1], Path("/p2"))
            lines = log_path.read_text().strip().split("\n")
            assert len(lines) == 2
        del os.environ["DESTRUCTIVE_GUARD_LOG"]

    def test_log_chmod_attempt(self):
        """Real-world scenario: chmod -R 777 gets logged."""
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "guard.log"
            os.environ["DESTRUCTIVE_GUARD_LOG"] = str(log_path)
            is_dangerous, pattern, log_entry = guard.check_command("chmod -R 777 /var/www/html")
            assert is_dangerous
            assert log_entry["matched_pattern"] == "CHMOD_777_RECURSIVE"
            assert log_entry["project_path"] == str(Path.cwd())
            assert "suggestion" in log_entry
        del os.environ["DESTRUCTIVE_GUARD_LOG"]
