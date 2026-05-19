#!/usr/bin/env python3
"""Regression tests for the destructive command guard hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive-command-guard" / "pre-tool-use-block-destructive.py"
INSTALLER = ROOT / "hooks" / "destructive-command-guard" / "install.py"


def run_hook(command: str, home: Path, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    event = {
        "tool_name": tool_name,
        "hook_event_name": "PreToolUse",
        "cwd": "/workspace/example",
        "tool_input": {"command": command},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )


def assert_blocked(command: str, expected_pattern: str, home: Path) -> None:
    completed = run_hook(command, home)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    output = payload["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert expected_pattern in output["permissionDecisionReason"]

    log_path = home / ".claude" / "hooks" / "blocked.log"
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["attempted_command"] == command
    assert records[-1]["blocked_pattern"] == expected_pattern
    assert records[-1]["project_path"] == "/workspace/example"
    assert "timestamp" in records[-1]


def assert_allowed(command: str, home: Path, tool_name: str = "Bash") -> None:
    completed = run_hook(command, home, tool_name=tool_name)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""


def test_required_destructive_patterns_are_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        cases = [
            ("rm -rf build", "rm -rf"),
            ("rm -fr build", "rm -rf"),
            ("rm --recursive --force build", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push origin main --force", "git push --force"),
            ("git push -f origin main", "git push --force"),
            ("sqlite3 app.db 'TRUNCATE TABLE sessions'", "TRUNCATE"),
            ("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM without WHERE"),
        ]
        for command, pattern in cases:
            assert_blocked(command, pattern, home)


def test_normal_commands_are_allowed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        for command in [
            "ls -la",
            "rm file.txt",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'",
            "python3 -m pytest",
        ]:
            assert_allowed(command, home)
        assert_allowed("rm -rf build", home, tool_name="Read")


def test_installer_copies_hook_and_merges_settings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        completed = subprocess.run(
            [sys.executable, str(INSTALLER)],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "HOME": str(home)},
        )
        assert completed.returncode == 0, completed.stderr

        installed_hook = home / ".claude" / "hooks" / "pre-tool-use-block-destructive.py"
        assert installed_hook.exists()
        assert os.access(installed_hook, os.X_OK)

        settings = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pre_tool_use = settings["hooks"]["PreToolUse"]
        assert pre_tool_use[0]["matcher"] == "Bash"
        assert pre_tool_use[0]["hooks"][0]["command"] == "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"


if __name__ == "__main__":
    test_required_destructive_patterns_are_blocked()
    test_normal_commands_are_allowed()
    test_installer_copies_hook_and_merges_settings()
    print("destructive command guard tests passed")
