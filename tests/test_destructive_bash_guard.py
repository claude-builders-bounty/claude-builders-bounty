#!/usr/bin/env python3
"""Unit tests for the destructive Bash guard hook."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "hooks" / "destructive-bash-guard" / "destructive_bash_guard.py"

spec = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
assert spec and spec.loader
hook = importlib.util.module_from_spec(spec)
sys.modules["destructive_bash_guard"] = hook
spec.loader.exec_module(hook)


def payload(command: str, tool_name: str = "Bash") -> str:
    return json.dumps(
        {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "project_path": "/tmp/example-project",
        }
    )


def run_hook(command: str, home: Path, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload(command, tool_name),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, expected_pattern: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_hook(command, Path(tmp))
        assert result.returncode == 2, (command, result.stdout, result.stderr)
        assert expected_pattern in result.stdout
        log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
        log_record = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert log_record["command"] == command
        assert log_record["project_path"] == "/tmp/example-project"
        assert log_record["reason"] == expected_pattern


def assert_allowed(command: str, tool_name: str = "Bash") -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_hook(command, Path(tmp), tool_name)
        assert result.returncode == 0, (command, result.stdout, result.stderr)
        assert result.stdout == ""
        assert not (Path(tmp) / ".claude" / "hooks" / "blocked.log").exists()


def test_acceptance_criteria_blocked_patterns() -> None:
    assert_blocked("rm -rf build/", "rm -rf")
    assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
    assert_blocked("git push origin main --force", "git push --force")
    assert_blocked("git push --force-with-lease origin feature", "git push --force")
    assert_blocked("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE")
    assert_blocked("psql -c \"DELETE FROM users;\"", "DELETE FROM without WHERE")


def test_safe_commands_are_allowed() -> None:
    assert_allowed("rm -r build/")
    assert_allowed("git push origin feature")
    assert_allowed("psql -c \"DELETE FROM users WHERE id = 42;\"")
    assert_allowed("python3 -m pytest")
    assert_allowed("echo 'DROP TABLE appears in docs only'", tool_name="Write")


def test_rule_function_directly_handles_spacing_and_wrappers() -> None:
    assert hook.find_block_reason("sudo rm   -fr /tmp/example").name == "rm -rf"
    assert hook.find_block_reason("env GIT_TRACE=1 git push origin HEAD --force-with-lease").name == "git push --force"
    assert hook.find_block_reason("DELETE FROM audit_log WHERE created_at < now();") is None


if __name__ == "__main__":
    tests = [
        test_acceptance_criteria_blocked_patterns,
        test_safe_commands_are_allowed,
        test_rule_function_directly_handles_spacing_and_wrappers,
    ]
    for test in tests:
        test()
        print(f"ok - {test.__name__}")
