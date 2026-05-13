#!/usr/bin/env python3
"""Tests for the destructive Bash hook."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).with_name("pre_tool_use.py")
spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def test_blocks_required_patterns():
    dangerous = {
        "rm -rf dist": "rm -rf",
        "rm -fr ./tmp": "rm -rf",
        "psql -c 'DROP TABLE users'": "DROP TABLE",
        "git push origin main --force": "force",
        "sqlite3 app.db 'TRUNCATE users'": "TRUNCATE",
        "sqlite3 app.db 'DELETE FROM users'": "DELETE FROM",
    }
    for command in dangerous:
        assert hook.block_reason(command), command


def test_allows_normal_commands_and_scoped_delete():
    safe_commands = [
        "ls -la",
        "git push origin main",
        "rm -r dist",
        "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        "python3 -m pytest",
    ]
    for command in safe_commands:
        assert hook.block_reason(command) is None, command


def test_hook_exits_two_and_logs_blocked_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/example-project")
    payload = json.dumps({"tool_input": {"command": "rm -rf dist"}})

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Blocked destructive Bash command" in result.stderr
    log_path = tmp_path / ".claude" / "hooks" / "blocked.log"
    log_entry = json.loads(log_path.read_text().strip())
    assert log_entry["command"] == "rm -rf dist"
    assert log_entry["project_path"] == "/tmp/example-project"


def test_hook_exits_zero_for_safe_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    payload = json.dumps({"tool_input": {"command": "python3 -m pytest"}})

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert not (tmp_path / ".claude" / "hooks" / "blocked.log").exists()
