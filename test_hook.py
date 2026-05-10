#!/usr/bin/env python3
"""Smoke tests for the Claude Code destructive Bash blocker hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / ".claude" / "hooks" / "block-destructive-bash.py"


def run_hook(command: str) -> dict | None:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def assert_blocked(command: str, expected_reason: str) -> None:
    output = run_hook(command)
    assert output is not None, f"Expected block for: {command}"
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert expected_reason.lower() in decision["permissionDecisionReason"].lower()


def assert_allowed(command: str) -> None:
    assert run_hook(command) is None, f"Expected allow for: {command}"


def main() -> int:
    assert_blocked("rm -rf build", "rm -rf")
    assert_blocked("psql -c 'DROP TABLE users'", "drop table")
    assert_blocked("git push --force origin main", "git push")
    assert_blocked("sqlite3 db.sqlite 'TRUNCATE audit_log;'", "truncate")
    assert_blocked("mysql -e 'DELETE FROM users;'", "delete")
    assert_allowed("rm build/output.txt")
    assert_allowed("git push origin main")
    assert_allowed("python -m pytest")
    assert_allowed("psql -c 'DELETE FROM jobs WHERE id = 1;' ")
    print("All hook smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
