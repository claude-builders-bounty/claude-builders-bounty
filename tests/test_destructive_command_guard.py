#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "destructive_command_guard.py"


def run(
    command: str,
    *,
    home: Path | None = None,
    payload_overrides: dict[str, object] | None = None,
) -> subprocess.CompletedProcess[str]:
    payload: dict[str, object] = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/claude-hook-test",
    }
    if payload_overrides:
        payload.update(payload_overrides)
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
    )


def test_allowed_commands_pass() -> None:
    for command in ["git status", "python3 -m pytest", "rm -r build", "DELETE FROM logs WHERE id = 1"]:
        proc = run(command)
        assert proc.returncode == 0, (command, proc.returncode, proc.stderr)


def test_blocked_commands_fail() -> None:
    cases = [
        "rm -rf build",
        "rm -fr build",
        "rm --recursive --force build",
        "rm --force --recursive build",
        "sudo rm -fr /tmp/example",
        "psql -c 'DROP TABLE users'",
        "git push --force origin main",
        "git push -f",
        "git push --force-with-lease",
        "TRUNCATE audit_log",
        "DELETE FROM users;",
        "DELETE FROM users\n",
    ]
    for command in cases:
        proc = run(command)
        assert proc.returncode == 2, (command, proc.returncode, proc.stderr)
        assert "Blocked destructive Bash command" in proc.stderr


def test_non_bash_payloads_are_ignored() -> None:
    proc = run("rm -rf build", payload_overrides={"tool_name": "Read"})
    assert proc.returncode == 0, proc.stderr


def test_blocked_attempt_is_logged_with_required_fields() -> None:
    with tempfile.TemporaryDirectory() as home_dir:
        home = Path(home_dir)
        proc = run("DELETE FROM users;", home=home)
        assert proc.returncode == 2, proc.stderr

        log_path = home / ".claude" / "hooks" / "blocked.log"
        assert log_path.exists()
        line = log_path.read_text(encoding="utf-8").strip()
        assert "rule=DELETE FROM without WHERE" in line
        assert "project=/tmp/claude-hook-test" in line
        assert "command=DELETE FROM users;" in line
        assert line[:4].isdigit() and "T" in line.split("\t", 1)[0]


def test_top_level_command_payload_is_supported() -> None:
    payload = {"tool_name": "Bash", "command": "TRUNCATE audit_log", "cwd": "/tmp/top-level"}
    with tempfile.TemporaryDirectory() as home_dir:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**os.environ, "HOME": home_dir},
        )
    assert proc.returncode == 2, proc.stderr
    assert "TRUNCATE" in proc.stderr


if __name__ == "__main__":
    test_allowed_commands_pass()
    test_blocked_commands_fail()
    test_non_bash_payloads_are_ignored()
    test_blocked_attempt_is_logged_with_required_fields()
    test_top_level_command_payload_is_supported()
    print("all tests passed")
