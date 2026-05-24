#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive_bash.py"


def run_hook(command: str, home: Path):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, expected: str, home: Path):
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), f"expected block output for {command!r}"
    data = json.loads(result.stdout)
    hook_out = data["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert expected in hook_out["permissionDecisionReason"]


def assert_allowed(command: str, home: Path):
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", f"expected allow/no output for {command!r}, got {result.stdout!r}"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        assert_blocked("rm -rf build/", "rm -rf", home)
        assert_blocked("git push --force origin main", "git push", home)
        assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE", home)
        assert_blocked("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE", home)
        assert_blocked("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM", home)
        assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'", home)
        assert_allowed("rm -r build/", home)
        assert_allowed("git push origin main", home)
        log_path = home / ".claude" / "hooks" / "blocked.log"
        assert log_path.exists(), "blocked.log was not created"
        log_text = log_path.read_text()
        assert "rm -rf build/" in log_text
        assert "project=/tmp/example-project" in log_text
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
