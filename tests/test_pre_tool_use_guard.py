#!/usr/bin/env python3
"""Tests for the Claude Code destructive Bash command guard."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "pre_tool_use_guard.py"
INSTALLER = REPO_ROOT / "hooks" / "install.py"


def main() -> int:
    tests = [
        test_blocks_required_patterns,
        test_allows_normal_commands,
        test_logs_redacted_command,
        test_non_bash_tools_are_ignored,
        test_installer_registers_bash_hook,
    ]

    for test in tests:
        test()
        print(f"ok - {test.__name__}")

    return 0


def test_blocks_required_patterns() -> None:
    cases = [
        ("rm -rf /tmp/example", "rm"),
        ("rm -fr ./build", "rm"),
        ("psql -c 'DROP TABLE users'", "DROP TABLE"),
        ("git push --force origin main", "force push"),
        ("git push -f", "force push"),
        ("mysql -e 'TRUNCATE audit_log'", "TRUNCATE"),
        ("sqlite3 app.db 'DELETE FROM sessions;'", "DELETE FROM"),
    ]

    with tempfile.TemporaryDirectory() as home:
        for command, expected_reason_text in cases:
            result = run_hook(command, home=home)
            assert result.returncode == 0
            response = json.loads(result.stdout)
            hook_output = response["hookSpecificOutput"]
            assert hook_output["hookEventName"] == "PreToolUse"
            assert hook_output["permissionDecision"] == "deny"
            assert expected_reason_text.lower() in hook_output["permissionDecisionReason"].lower()

        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        log_lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(log_lines) == len(cases)
        first_entry = json.loads(log_lines[0])
        assert first_entry["command"] == cases[0][0]
        assert first_entry["project_path"] == "/tmp/project"
        assert "timestamp" in first_entry


def test_allows_normal_commands() -> None:
    allowed = [
        "ls -la",
        "git status --short",
        "echo 'DROP TABLE users'",
        "cat migration.sql | sed 's/DROP TABLE/DROP VIEW/'",
        "echo rm -rf /tmp/example",
        "echo 'DELETE FROM users WHERE id = 1'",
        "sqlite3 app.db 'DELETE FROM sessions WHERE id = 7;'",
        "rm -r ./build",
    ]

    with tempfile.TemporaryDirectory() as home:
        for command in allowed:
            result = run_hook(command, home=home)
            assert result.returncode == 0
            assert result.stdout == ""
            assert result.stderr == ""

        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        assert not log_path.exists()


def test_logs_redacted_command() -> None:
    with tempfile.TemporaryDirectory() as home:
        result = run_hook("PASSWORD=hunter2 rm -rf /tmp/example", home=home)
        assert result.returncode == 0

        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
        assert entry["command"] == "PASSWORD=<redacted> rm -rf /tmp/example"
        assert "hunter2" not in entry["command"]


def test_non_bash_tools_are_ignored() -> None:
    with tempfile.TemporaryDirectory() as home:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"command": "rm -rf /"},
            "cwd": "/tmp/project",
        }
        result = run_hook_payload(payload, home=home)
        assert result.returncode == 0
        assert result.stdout == ""


def test_installer_registers_bash_hook() -> None:
    with tempfile.TemporaryDirectory() as home:
        env = os.environ.copy()
        env["HOME"] = home
        result = subprocess.run(
            [sys.executable, str(INSTALLER)],
            input="",
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        installed_hook = Path(home) / ".claude" / "hooks" / "pre_tool_use_guard.py"
        assert installed_hook.exists()
        assert os.access(installed_hook, os.X_OK)

        settings_path = Path(home) / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        pre_tool_use = settings["hooks"]["PreToolUse"]
        bash_entries = [entry for entry in pre_tool_use if entry.get("matcher") == "Bash"]
        assert len(bash_entries) == 1
        commands = [hook["command"] for hook in bash_entries[0]["hooks"]]
        assert any("pre_tool_use_guard.py" in command for command in commands)


def run_hook(command: str, home: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp/project",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    return run_hook_payload(payload, home=home)


def run_hook_payload(payload: dict[str, object], home: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
