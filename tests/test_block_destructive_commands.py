#!/usr/bin/env python3
"""Small local proof script for the destructive-command hook."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block_destructive_commands.py"


spec = importlib.util.spec_from_file_location("block_destructive_commands", HOOK)
hook = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(hook)


def assert_reason(command: str, expected_blocked: bool) -> None:
    reason = hook.blocked_reason(command)
    if expected_blocked and reason is None:
        raise AssertionError(f"Expected command to be blocked: {command}")
    if not expected_blocked and reason is not None:
        raise AssertionError(f"Expected command to be allowed, got {reason!r}: {command}")


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(ROOT),
    }
    env = os.environ.copy()
    env.update({"HOME": str(home), "USERPROFILE": str(home)})

    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def main() -> int:
    blocked = [
        "rm -rf build",
        "sudo rm -fr /tmp/demo",
        "psql -c 'DROP TABLE users'",
        "git push --force origin main",
        "sqlite3 app.db 'TRUNCATE sessions'",
        "psql -c 'DELETE FROM users;'",
    ]
    allowed = [
        "ls -la",
        "git status --short",
        "rm build/output.txt",
        "git push origin main",
        "psql -c 'DELETE FROM users WHERE id = 1;'",
    ]

    for command in blocked:
        assert_reason(command, True)
    for command in allowed:
        assert_reason(command, False)

    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        blocked_result = run_hook("rm -rf build", home)
        if blocked_result.returncode != 0:
            raise AssertionError(blocked_result.stderr)

        output = json.loads(blocked_result.stdout)
        decision = output["hookSpecificOutput"]["permissionDecision"]
        if decision != "deny":
            raise AssertionError(f"Expected deny decision, got {decision!r}")

        log_path = home / ".claude" / "hooks" / "blocked.log"
        log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        if log_entry["attempted_command"] != "rm -rf build":
            raise AssertionError(f"Unexpected log entry: {log_entry}")
        if log_entry["project_path"] != str(ROOT):
            raise AssertionError(f"Unexpected project path: {log_entry}")

        allowed_result = run_hook("git status --short", home)
        if allowed_result.returncode != 0 or allowed_result.stdout.strip():
            raise AssertionError(f"Expected normal command to pass silently: {allowed_result}")

    print("All destructive-command hook checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
