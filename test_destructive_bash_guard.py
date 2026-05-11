#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "hooks" / "destructive_bash_guard.py"


def run_hook(command: str, *, tool_name: str = "Bash", home: str | None = None) -> dict:
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    if home:
        env["HOME"] = home
    proc = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return json.loads(proc.stdout)


def decision(result: dict) -> str:
    return result["hookSpecificOutput"]["permissionDecision"]


def reason(result: dict) -> str:
    return result["hookSpecificOutput"].get("permissionDecisionReason", "")


def assert_denied(command: str) -> None:
    with tempfile.TemporaryDirectory() as home:
        result = run_hook(command, home=home)
        assert decision(result) == "deny", (command, result)
        log = Path(home) / ".claude" / "hooks" / "blocked.log"
        assert log.exists(), f"blocked.log missing for {command}"
        record = json.loads(log.read_text().strip().splitlines()[-1])
        assert record["command"] == command
        assert record["project_path"] == "/tmp/example-project"
        assert record["timestamp"]


def assert_allowed(command: str) -> None:
    with tempfile.TemporaryDirectory() as home:
        result = run_hook(command, home=home)
        assert decision(result) == "allow", (command, result)
        log = Path(home) / ".claude" / "hooks" / "blocked.log"
        assert not log.exists(), f"safe command should not be logged: {command}"


def test_required_blocks() -> None:
    assert_denied("rm -rf /tmp/build")
    assert_denied("rm -fr dist")
    assert_denied("rm -r -f node_modules")
    assert_denied("bash -c 'rm -rf dist'")
    assert_denied("git push --force origin main")
    assert_denied("git push -f")
    assert_denied("git push --force-with-lease origin main")
    assert_denied("psql -c 'DROP TABLE users'")
    assert_denied("sqlite3 app.db 'TRUNCATE sessions'")
    assert_denied("mysql -e 'DELETE FROM users'")
    assert_denied("psql -c 'delete from users\nwhere id = 1; drop table audit_log;'")


def test_safe_commands_pass() -> None:
    assert_allowed("ls -la")
    assert_allowed("rm -r dist")
    assert_allowed("git push origin main")
    assert_allowed("python3 -m pytest")
    assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")
    assert_allowed("psql -c 'DELETE FROM users\nWHERE id = 1'")
    assert_allowed("git commit -m 'Fix DELETE FROM bug in docs'")
    assert_allowed("grep 'DROP TABLE' schema.sql")
    assert_allowed("echo 'DROP TABLE users' > docs/example.sql")


def test_non_bash_tools_pass() -> None:
    result = run_hook("rm -rf /", tool_name="Read")
    assert decision(result) == "allow"


if __name__ == "__main__":
    test_required_blocks()
    test_safe_commands_pass()
    test_non_bash_tools_pass()
    print("test_destructive_bash_guard.py: ok")
