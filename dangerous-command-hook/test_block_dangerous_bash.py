#!/usr/bin/env python3
"""Regression tests for block_dangerous_bash.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / ".claude" / "hooks" / "block_dangerous_bash.py"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "session_id": "test",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp/example-project",
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def assert_blocked(command: str, expected_rule: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    decision = output["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert expected_rule in decision["permissionDecisionReason"]


def assert_allowed(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)

        assert_blocked("rm -rf build", "rm -rf", home)
        assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE", home)
        assert_blocked("git push origin main --force", "git push --force", home)
        assert_blocked("sqlite3 app.db 'TRUNCATE users'", "TRUNCATE", home)
        assert_blocked("sqlite3 app.db 'DELETE FROM users;'", "DELETE FROM without WHERE", home)

        assert_allowed("rm build/output.txt", home)
        assert_allowed("git push origin main", home)
        assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'", home)
        assert_allowed("npm test", home)

        log_file = home / ".claude" / "hooks" / "blocked.log"
        log_text = log_file.read_text(encoding="utf-8")
        assert "project=/tmp/example-project" in log_text
        assert "rule=rm -rf" in log_text
        assert "rule=DELETE FROM without WHERE" in log_text

    print("test_block_dangerous_bash.py passed")


if __name__ == "__main__":
    main()
