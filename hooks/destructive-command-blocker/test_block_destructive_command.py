#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("block_destructive_command.py")


def run_hook(command: str) -> tuple[dict, Path]:
    tmpdir = Path(tempfile.mkdtemp())
    log_path = tmpdir / "blocked.log"
    env = os.environ.copy()
    env["CLAUDE_BLOCKED_LOG_PATH"] = str(log_path)
    payload = {
        "session_id": "test",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/workspace/project",
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    output = json.loads(result.stdout) if result.stdout.strip() else {}
    return output, log_path


def assert_blocked(command: str, reason_fragment: str) -> None:
    output, log_path = run_hook(command)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert reason_fragment in hook_output["permissionDecisionReason"]
    log_entry = json.loads(log_path.read_text(encoding="utf-8"))
    assert log_entry["command"] == command
    assert log_entry["project_path"] == "/workspace/project"


def assert_allowed(command: str) -> None:
    output, log_path = run_hook(command)
    assert output == {}
    assert not log_path.exists()


def main() -> None:
    assert_blocked("rm -rf dist", "rm -rf")
    assert_blocked("rm -fr dist", "rm -rf")
    assert_blocked("rm -r -f dist", "rm -rf")
    assert_blocked("git push --force origin main", "git push --force")
    assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
    assert_blocked("psql -c 'TRUNCATE users'", "TRUNCATE")
    assert_blocked("psql -c 'DELETE FROM users'", "DELETE FROM without a WHERE")
    assert_allowed("rm dist/file.txt")
    assert_allowed("git push origin main")
    assert_allowed("truncate -s 0 build.log")
    assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")
    assert_allowed("npm test")


if __name__ == "__main__":
    main()
