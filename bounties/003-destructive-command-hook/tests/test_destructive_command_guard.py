#!/usr/bin/env python3
"""Regression tests for the destructive command guard hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "destructive_command_guard.py"


def run_hook(command: str | None, *, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload: dict[str, object] = {
        "tool_name": tool_name,
        "tool_input": {},
        "cwd": "/tmp/example-project",
    }
    if command is not None:
        payload["tool_input"] = {"command": command}

    env = os.environ.copy()
    env["CLAUDE_HOOK_BLOCK_LOG"] = str(LOG_PATH)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_allowed(command: str, *, tool_name: str = "Bash") -> None:
    result = run_hook(command, tool_name=tool_name)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def assert_blocked(command: str, expected_reason: str) -> None:
    result = run_hook(command)
    assert result.returncode == 0
    assert result.stderr == ""
    body = json.loads(result.stdout)
    output = body["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert expected_reason in output["permissionDecisionReason"]


def read_log_entries() -> list[dict[str, object]]:
    if not LOG_PATH.exists():
        return []
    return [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines()]


with tempfile.TemporaryDirectory() as temp_dir:
    LOG_PATH = Path(temp_dir) / "blocked.log"

    assert_allowed("npm test && git status --short")
    assert_allowed("echo rm -rf is only text")
    assert_allowed("echo git push -f is only text")
    assert_allowed("psql -c 'DELETE FROM users WHERE id = 42'")
    assert_allowed("rm -r ./build")
    assert_allowed("rm -f ./artifact")
    assert_allowed("rm -rf ./artifact", tool_name="Read")

    assert_blocked("rm -rf /tmp/danger", "rm with recursive and force flags")
    assert_blocked("TARGET=/tmp/danger rm --recursive --force \"$TARGET\"", "rm with recursive and force flags")
    assert_blocked("sudo -u root rm -fr /tmp/danger", "rm with recursive and force flags")
    assert_blocked("bash -c 'rm -rf /tmp/danger'", "rm with recursive and force flags")
    assert_blocked("git push --force origin main", "git push with force option")
    assert_blocked("git -C ../repo push --force origin main", "git push with force option")
    assert_blocked("git push -f origin main", "git push with force option")
    assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE statement")
    assert_blocked("mysql -e 'TRUNCATE TABLE sessions'", "TRUNCATE statement")
    assert_blocked("sqlite3 app.db 'DELETE FROM users;'", "DELETE FROM statement without WHERE")

    entries = read_log_entries()
    assert len(entries) == 10, entries
    assert entries[-1]["project_path"] == "/tmp/example-project"
    assert entries[-1]["command"] == "sqlite3 app.db 'DELETE FROM users;'"

print("destructive command guard tests passed")
