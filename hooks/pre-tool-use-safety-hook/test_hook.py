#!/usr/bin/env python3
"""
Comprehensive test suite for pre_tool_use_hook.py

Run with:
    pytest test_hook.py -v
    # or
    python -m pytest test_hook.py -v --tb=short
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the hook module
from pre_tool_use_hook import (
    DEFAULT_RULES,
    check_command,
    load_config,
    log_blocked,
    make_deny_response,
    process_hook,
    _is_whitelisted,
    _parse_flags,
)


# =========================================================================
# Helpers
# =========================================================================

def make_tool_input(command: str, tool_name: str = "Bash", project_path: str = "/tmp/test") -> dict:
    """Build a Claude Code hook input dict."""
    return {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": project_path,
    }


# =========================================================================
# Rule matching — dangerous commands MUST be caught
# =========================================================================

class TestDangerousCommands:
    """Verify that every required dangerous pattern is detected."""

    @pytest.mark.parametrize(
        "command,expected_rule_id",
        [
            # rm -rf variants
            ("rm -rf /", "rm-rf"),
            ("rm -rf /home/user", "rm-rf"),
            ("rm -rf .", "rm-rf"),
            ("rm -r -f /tmp/build", "rm-rf"),
            ("sudo rm -rf /var/data", "rm-rf"),
            ("rm -rf --no-preserve-root /", "rm-rf"),
            # combined flags
            ("rm -rfi /tmp", "rm-rf"),
            ("rm -frd /tmp", "rm-rf"),
            # DROP TABLE
            ("mysql -e 'DROP TABLE users;'", "drop-table"),
            ("echo \"DROP TABLE orders\" | psql", "drop-table"),
            ("drop table config;", "drop-table"),
            # git push --force
            ("git push --force", "git-push-force"),
            ("git push origin main --force", "git-push-force"),
            ("git push -f origin main", "git-push-force"),
            # TRUNCATE
            ("mysql -e 'TRUNCATE users;'", "truncate"),
            ("TRUNCATE TABLE sessions;", "truncate"),
            ("truncate orders;", "truncate"),
            # DELETE FROM without WHERE
            ("mysql -e 'DELETE FROM users;'", "delete-no-where"),
            ("DELETE FROM orders;", "delete-no-where"),
            # DELETE FROM at end of line (no semicolon)
            ("DELETE FROM users", "delete-no-where-eol"),
            # chmod 777
            ("chmod 777 /var/www", "chmod-777"),
            # mkfs
            ("mkfs.ext4 /dev/sda1", "mkfs"),
            # dd to device
            ("dd if=/dev/zero of=/dev/sda bs=1M", "dd-of-dev"),
        ],
    )
    def test_dangerous_command_detected(self, command: str, expected_rule_id: str):
        result = check_command(command, DEFAULT_RULES)
        assert result is not None, f"Expected rule {expected_rule_id!r} to match: {command!r}"
        assert result["id"] == expected_rule_id


class TestSafeCommands:
    """Verify that normal commands are NOT blocked."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls -la",
            "cd /tmp",
            "cat file.txt",
            "git push origin main",
            "git push",
            "rm file.txt",
            "rm -r /tmp/build",  # -r without -f is not blocked by default
            "npm install",
            "pip install flask",
            "python manage.py migrate",
            "docker build .",
            "echo hello world",
            "grep -r 'pattern' .",
            "find . -name '*.py'",
            "curl https://example.com",
            "DELETE FROM users WHERE id = 5;",  # has WHERE clause
            "mysql -e 'DELETE FROM users WHERE active = 0;'",
            "SELECT * FROM users;",
            "INSERT INTO users VALUES (1, 'test');",
            "UPDATE users SET name = 'test' WHERE id = 1;",
        ],
    )
    def test_safe_command_allowed(self, command: str):
        result = check_command(command, DEFAULT_RULES)
        assert result is None, f"Command should NOT be blocked: {command!r}, matched: {result}"


# =========================================================================
# Non-Bash tools should pass through
# =========================================================================

class TestNonBashTools:
    """Non-Bash tool calls should never be blocked."""

    @pytest.mark.parametrize("tool_name", ["Read", "Write", "Edit", "Search", "FileEditor", ""])
    def test_non_bash_passes(self, tool_name: str):
        data = make_tool_input("rm -rf /", tool_name=tool_name)
        exit_code = process_hook(data, load_config())
        assert exit_code == 0


# =========================================================================
# Whitelist
# =========================================================================

class TestWhitelist:
    """Whitelisted paths and commands should bypass blocking."""

    def test_path_whitelist(self):
        config = load_config()
        config["whitelist"]["paths"] = ["/tmp/safe"]
        assert _is_whitelisted("rm -rf /tmp/safe/build", "/tmp/safe/project", config) is True
        assert _is_whitelisted("rm -rf /", "/home/user/project", config) is False

    def test_command_whitelist(self):
        config = load_config()
        config["whitelist"]["commands"] = ["rm -rf /tmp/build"]
        assert _is_whitelisted("rm -rf /tmp/build", "/any/path", config) is True
        assert _is_whitelisted("rm -rf /", "/any/path", config) is False

    def test_whitelisted_command_not_blocked(self):
        config = load_config()
        config["whitelist"]["commands"] = ["rm -rf /tmp/build"]
        data = make_tool_input("rm -rf /tmp/build")
        exit_code = process_hook(data, config)
        assert exit_code == 0


# =========================================================================
# Dry-run mode
# =========================================================================

class TestDryRun:
    """In dry-run mode, dangerous commands should be logged but not blocked."""

    def test_dry_run_allows_dangerous(self):
        config = load_config()
        config["dry_run"] = True
        config["logging"]["enabled"] = False  # don't write log in tests
        data = make_tool_input("rm -rf /")
        exit_code = process_hook(data, config)
        assert exit_code == 0  # not blocked


# =========================================================================
# Logging
# =========================================================================

class TestLogging:
    """Log file should be written correctly."""

    def test_log_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_blocked.log")
            config = load_config()
            config["logging"]["log_file"] = log_file
            config["logging"]["enabled"] = True

            rule = {"id": "rm-rf", "description": "Recursive force delete", "severity": "critical"}
            log_blocked("rm -rf /", rule, "/test/project", config)

            assert os.path.exists(log_file)
            with open(log_file) as f:
                entry = json.loads(f.readline())
            assert entry["command"] == "rm -rf /"
            assert entry["rule_id"] == "rm-rf"
            assert entry["project_path"] == "/test/project"
            assert "timestamp" in entry

    def test_log_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_blocked.log")
            config = load_config()
            config["logging"]["log_file"] = log_file
            config["logging"]["max_size_mb"] = 0  # force rotation

            # Write a large initial file
            with open(log_file, "w") as f:
                f.write("x" * 2048)

            rule = {"id": "test", "description": "test", "severity": "low"}
            log_blocked("test", rule, "/", config)

            rotated = log_file + ".1"
            assert os.path.exists(rotated)

    def test_log_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_blocked.log")
            config = load_config()
            config["logging"]["log_file"] = log_file
            config["logging"]["enabled"] = False

            rule = {"id": "test", "description": "test", "severity": "low"}
            log_blocked("test", rule, "/", config)

            assert not os.path.exists(log_file)


# =========================================================================
# process_hook integration
# =========================================================================

class TestProcessHook:
    """Full integration tests for process_hook."""

    def test_blocks_rm_rf(self, capsys):
        config = load_config()
        config["logging"]["enabled"] = False
        data = make_tool_input("rm -rf /home/user/important")
        exit_code = process_hook(data, config)
        assert exit_code == 2
        stdout = capsys.readouterr().out
        response = json.loads(stdout)
        assert response["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Blocked by safety hook" in response["hookSpecificOutput"]["permissionDecisionReason"]

    def test_blocks_drop_table(self, capsys):
        config = load_config()
        config["logging"]["enabled"] = False
        data = make_tool_input("mysql -e 'DROP TABLE users;'")
        exit_code = process_hook(data, config)
        assert exit_code == 2

    def test_blocks_git_push_force(self, capsys):
        config = load_config()
        config["logging"]["enabled"] = False
        data = make_tool_input("git push --force origin main")
        exit_code = process_hook(data, config)
        assert exit_code == 2

    def test_blocks_truncate(self, capsys):
        config = load_config()
        config["logging"]["enabled"] = False
        data = make_tool_input("TRUNCATE TABLE sessions;")
        exit_code = process_hook(data, config)
        assert exit_code == 2

    def test_blocks_delete_no_where(self, capsys):
        config = load_config()
        config["logging"]["enabled"] = False
        data = make_tool_input("DELETE FROM users;")
        exit_code = process_hook(data, config)
        assert exit_code == 2

    def test_allows_safe_commands(self):
        config = load_config()
        for cmd in ["ls -la", "git push origin main", "npm install", "cat README.md"]:
            data = make_tool_input(cmd)
            exit_code = process_hook(data, config)
            assert exit_code == 0, f"Should not block: {cmd!r}"

    def test_allows_delete_with_where(self):
        config = load_config()
        data = make_tool_input("DELETE FROM users WHERE id = 5;")
        exit_code = process_hook(data, config)
        assert exit_code == 0

    def test_empty_command(self):
        config = load_config()
        data = make_tool_input("")
        exit_code = process_hook(data, config)
        assert exit_code == 0


# =========================================================================
# make_deny_response
# =========================================================================

class TestDenyResponse:
    """Verify the deny response matches Claude Code's expected format."""

    def test_deny_structure(self):
        resp = make_deny_response("test reason")
        assert "hookSpecificOutput" in resp
        hso = resp["hookSpecificOutput"]
        assert hso["hookEventName"] == "PreToolUse"
        assert hso["permissionDecision"] == "deny"
        assert hso["permissionDecisionReason"] == "test reason"


# =========================================================================
# Config loading
# =========================================================================

class TestConfigLoading:
    """Config file loading and merging."""

    def test_default_config_valid(self):
        config = load_config()
        assert isinstance(config["rules"], list)
        assert len(config["rules"]) > 0
        assert config["dry_run"] is False

    def test_custom_config_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {
                "rules": [
                    {"id": "custom", "pattern": "dangerous_cmd", "severity": "low", "enabled": True}
                ],
                "dry_run": True,
            }
            cfg_path = os.path.join(tmpdir, "hook_config.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)

            with patch.dict(os.environ, {"HOOK_CONFIG_PATH": cfg_path}):
                config = load_config()
                assert len(config["rules"]) == 1
                assert config["rules"][0]["id"] == "custom"
                assert config["dry_run"] is True


# =========================================================================
# Flag parsing
# =========================================================================

class TestFlagParsing:
    def test_ignorecase(self):
        import re

        flags = _parse_flags("IGNORECASE")
        assert flags == re.IGNORECASE

    def test_multiple(self):
        import re

        flags = _parse_flags("IGNORECASE|MULTILINE")
        assert flags == re.IGNORECASE | re.MULTILINE

    def test_none(self):
        assert _parse_flags(None) == 0
        assert _parse_flags("") == 0


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:
    """Edge cases and robustness."""

    def test_multiline_command(self):
        cmd = "echo hello\nrm -rf /\necho done"
        result = check_command(cmd, DEFAULT_RULES)
        assert result is not None

    def test_command_in_pipe(self):
        cmd = "cat file | rm -rf /"
        result = check_command(cmd, DEFAULT_RULES)
        assert result is not None

    def test_command_with_env_vars(self):
        cmd = "FORCE=1 rm -rf $HOME"
        result = check_command(cmd, DEFAULT_RULES)
        assert result is not None

    def test_delete_from_with_where(self):
        cmd = "DELETE FROM users WHERE id = 5;"
        result = check_command(cmd, DEFAULT_RULES)
        assert result is None

    def test_delete_from_with_where_multiline(self):
        cmd = "DELETE FROM users\nWHERE active = 0;"
        # The first line matches delete-no-where-eol
        result = check_command(cmd, DEFAULT_RULES)
        # This is a known limitation — multiline DELETE with WHERE on next line
        # is caught. Document as expected behaviour.
        # For safety, this is acceptable (false positive > false negative).
        assert result is not None  # Intentionally catches this edge case

    def test_disabled_rule(self):
        rules = [
            {"id": "test", "pattern": "dangerous", "enabled": False}
        ]
        assert check_command("dangerous", rules) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
