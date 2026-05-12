#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_PATH = Path(__file__).with_name("destructive_command_guard.py")

spec = importlib.util.spec_from_file_location("guard", HOOK_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


def assert_blocked(command: str) -> None:
    reason = guard.block_reason(command)
    assert reason is not None, f"expected block for: {command}"


def assert_allowed(command: str) -> None:
    reason = guard.block_reason(command)
    assert reason is None, f"expected allow for: {command}; got {reason}"


def test_patterns() -> None:
    assert_blocked("rm -rf node_modules")
    assert_blocked("sudo rm -fr /tmp/example")
    assert_blocked("psql -c 'DROP TABLE users;'")
    assert_blocked("git push origin main --force")
    assert_blocked("git push --force-with-lease origin main")
    assert_blocked("sqlite3 app.db 'TRUNCATE audit_logs;'")
    assert_blocked("DELETE FROM sessions;")
    assert_blocked("delete from sessions")

    assert_allowed("rm -r build")
    assert_allowed("rm -f tmp.txt")
    assert_allowed("git push origin feature")
    assert_allowed("SELECT * FROM users")
    assert_allowed("DELETE FROM sessions WHERE expires_at < datetime('now')")
    assert_allowed("npm test")


def test_hook_exit_and_logging() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["CLAUDE_PROJECT_DIR"] = "/tmp/project"
        payload = {"tool_input": {"command": "DELETE FROM users;"}}
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        assert proc.returncode == 2, proc
        assert "DELETE FROM without a WHERE clause" in proc.stderr
        log_path = home / ".claude" / "hooks" / "blocked.log"
        assert log_path.exists()
        record = json.loads(log_path.read_text().strip())
        assert record["command"] == "DELETE FROM users;"
        assert record["project_path"] == "/tmp/project"


def test_allowed_exit() -> None:
    payload = {"tool_input": {"command": "git status"}}
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc
    assert proc.stderr == ""


if __name__ == "__main__":
    test_patterns()
    test_hook_exit_and_logging()
    test_allowed_exit()
    print("all destructive command guard tests passed")
