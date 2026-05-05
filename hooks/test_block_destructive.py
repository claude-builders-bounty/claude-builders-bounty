"""Tests for the destructive command guard hook."""

import json
import os
import subprocess
import sys
import tempfile

import pytest

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "block_destructive.py")


def run_hook(tool_name: str, command: str = "") -> dict:
    """Run the hook script with given input and return parsed output."""
    hook_input = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
    })
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=hook_input,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Hook crashed: {result.stderr}"
    return json.loads(result.stdout)


class TestApprovedCommands:
    """Commands that should pass through without blocking."""

    def test_simple_ls(self):
        result = run_hook("Bash", "ls -la")
        assert result["decision"] == "approve"

    def test_git_push(self):
        result = run_hook("Bash", "git push origin main")
        assert result["decision"] == "approve"

    def test_git_push_with_set_upstream(self):
        result = run_hook("Bash", "git push -u origin feature-branch")
        assert result["decision"] == "approve"

    def test_rm_single_file(self):
        result = run_hook("Bash", "rm file.txt")
        assert result["decision"] == "approve"

    def test_rm_recursive_only(self):
        result = run_hook("Bash", "rm -r dir/")
        assert result["decision"] == "approve"

    def test_delete_with_where(self):
        result = run_hook("Bash", "echo 'DELETE FROM users WHERE id = 5'")
        assert result["decision"] == "approve"

    def test_non_bash_tool(self):
        result = run_hook("Read", "")
        assert result["decision"] == "approve"

    def test_empty_command(self):
        result = run_hook("Bash", "")
        assert result["decision"] == "approve"

    def test_npm_install(self):
        result = run_hook("Bash", "npm install express")
        assert result["decision"] == "approve"

    def test_grep_for_delete(self):
        result = run_hook("Bash", "grep -r 'DELETE FROM' src/")
        assert result["decision"] == "approve"


class TestBlockedCommands:
    """Commands that should be blocked."""

    def test_rm_rf(self):
        result = run_hook("Bash", "rm -rf /")
        assert result["decision"] == "block"
        assert "rm -rf" in result["reason"]

    def test_rm_rf_directory(self):
        result = run_hook("Bash", "rm -rf ./node_modules")
        assert result["decision"] == "block"

    def test_rm_fr(self):
        result = run_hook("Bash", "rm -fr /tmp/data")
        assert result["decision"] == "block"

    def test_drop_table(self):
        result = run_hook("Bash", "psql -c 'DROP TABLE users'")
        assert result["decision"] == "block"
        assert "DROP TABLE" in result["reason"]

    def test_drop_table_case_insensitive(self):
        result = run_hook("Bash", "echo 'drop table sessions' | psql")
        assert result["decision"] == "block"

    def test_git_push_force(self):
        result = run_hook("Bash", "git push --force origin main")
        assert result["decision"] == "block"
        assert "force push" in result["reason"]

    def test_git_push_f(self):
        result = run_hook("Bash", "git push -f origin main")
        assert result["decision"] == "block"

    def test_truncate(self):
        result = run_hook("Bash", "psql -c 'TRUNCATE users'")
        assert result["decision"] == "block"
        assert "TRUNCATE" in result["reason"]

    def test_truncate_case_insensitive(self):
        result = run_hook("Bash", "echo 'truncate table logs' | mysql")
        assert result["decision"] == "block"

    def test_delete_without_where(self):
        result = run_hook("Bash", "psql -c 'DELETE FROM users'")
        assert result["decision"] == "block"
        assert "DELETE FROM" in result["reason"]

    def test_delete_without_where_multiword_table(self):
        result = run_hook("Bash", "echo 'DELETE FROM audit_logs' | psql")
        assert result["decision"] == "block"


class TestLogging:
    """Test that blocked commands are logged correctly."""

    def test_blocked_command_is_logged(self, tmp_path, monkeypatch):
        log_file = str(tmp_path / "blocked.log")
        monkeypatch.setattr(
            "block_destructive.LOG_FILE", log_file
        )
        # Run in-process to use monkeypatch
        sys.path.insert(0, os.path.dirname(HOOK_SCRIPT))
        import importlib
        import block_destructive

        importlib.reload(block_destructive)
        block_destructive.LOG_FILE = log_file

        block_destructive.log_blocked("rm -rf /", "rm -rf (recursive force delete)")

        assert os.path.exists(log_file)
        content = open(log_file).read()
        assert "BLOCKED" in content
        assert "rm -rf /" in content
        assert "recursive force delete" in content

    def test_log_contains_timestamp(self, tmp_path):
        sys.path.insert(0, os.path.dirname(HOOK_SCRIPT))
        import importlib
        import block_destructive

        importlib.reload(block_destructive)
        log_file = str(tmp_path / "blocked.log")
        block_destructive.LOG_FILE = log_file

        block_destructive.log_blocked("DROP TABLE x", "DROP TABLE")

        content = open(log_file).read()
        # Check ISO timestamp format
        assert "202" in content
        assert "T" in content
        assert "Z" in content


class TestHookOutputFormat:
    """Verify the hook output is valid JSON matching Claude Code hook spec."""

    def test_approve_output_format(self):
        result = run_hook("Bash", "echo hello")
        assert "decision" in result
        assert result["decision"] == "approve"

    def test_block_output_format(self):
        result = run_hook("Bash", "rm -rf /")
        assert "decision" in result
        assert result["decision"] == "block"
        assert "reason" in result
        assert len(result["reason"]) > 0
