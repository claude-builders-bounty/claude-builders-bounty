import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hooks.block_destructive_commands import (
    is_destructive_command,
    log_blocked_attempt,
    main,
)


@pytest.mark.parametrize(
    "command,expected_reason",
    [
        ("rm -rf /some/path", "rm -rf"),
        ("rm -fr build/", "rm -rf"),
        ("rm -r -f temp", "rm -rf"),
        ("rm -f -r temp", "rm -rf"),
        ("DROP TABLE users;", "DROP TABLE"),
        ("drop table if exists schema_migrations;", "DROP TABLE"),
        ("git push --force", "git push --force"),
        ("git push origin main --force", "git push --force"),
        ("git push origin main -f", "git push --force"),
        ("TRUNCATE users;", "TRUNCATE"),
        ("truncate table audit_logs;", "TRUNCATE"),
        ("DELETE FROM users;", "DELETE FROM"),
        ("delete from sessions;", "DELETE FROM"),
    ],
)
def test_destructive_commands_blocked(command, expected_reason):
    blocked, reason = is_destructive_command(command)
    assert blocked is True
    assert expected_reason in reason


@pytest.mark.parametrize(
    "command",
    [
        "ls -la",
        "rm file.txt",
        "git push origin main",
        "git status",
        "SELECT * FROM users;",
        "DELETE FROM users WHERE id = 123;",
        "delete from sessions where expired_at < NOW();",
        "git commit -m 'Fix TRUNCATE behavior'",
        "grep -r 'DROP TABLE' src/",
    ],
)
def test_safe_commands_allowed(command):
    blocked, reason = is_destructive_command(command)
    assert blocked is False
    assert reason == ""


def test_log_blocked_attempt(tmp_path):
    fake_hooks_dir = tmp_path / ".claude" / "hooks"
    fake_log_file = fake_hooks_dir / "blocked.log"

    with patch("pathlib.Path.home", return_value=tmp_path):
        log_blocked_attempt("rm -rf /tmp", "/home/user/project", "Destructive file removal")

    assert fake_log_file.exists()
    content = fake_log_file.read_text(encoding="utf-8")
    assert "PROJECT: /home/user/project" in content
    assert "COMMAND: rm -rf /tmp" in content
    assert "REASON: Destructive file removal" in content


def test_main_stdin_json_blocking(tmp_path, capsys):
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": "/path/to/myrepo",
        "tool_input": {"command": "DROP TABLE customers;"}
    })

    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("sys.stdin.isatty", return_value=False), \
         patch("sys.stdin.read", return_value=payload), \
         pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "BLOCKED BY CLAUDE CODE HOOK" in captured.err
    assert "DROP TABLE" in captured.err

    log_file = tmp_path / ".claude" / "hooks" / "blocked.log"
    assert log_file.exists()
    assert "DROP TABLE customers;" in log_file.read_text()


def test_main_stdin_json_allowed(capsys):
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": "/path/to/myrepo",
        "tool_input": {"command": "git status"}
    })

    with patch("sys.stdin.isatty", return_value=False), \
         patch("sys.stdin.read", return_value=payload), \
         pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
