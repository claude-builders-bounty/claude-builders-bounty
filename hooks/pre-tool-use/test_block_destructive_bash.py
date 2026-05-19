#!/usr/bin/env python3
"""Smoke tests for the destructive Bash pre-tool-use hook."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HOOK_PATH = Path(__file__).with_name("block_destructive_bash.py")

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
assert spec is not None
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def assert_blocked(command: str, expected_reason: str) -> None:
    reason = hook.find_block_reason(command)
    assert reason == expected_reason, f"expected {expected_reason!r}, got {reason!r} for {command!r}"


def assert_allowed(command: str) -> None:
    reason = hook.find_block_reason(command)
    assert reason is None, f"expected allowed command, got {reason!r} for {command!r}"


def test_patterns() -> None:
    assert_blocked("rm -rf /tmp/project", "rm -rf")
    assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
    assert_blocked("git push origin main --force", "git push --force")
    assert_blocked("TRUNCATE audit_log", "TRUNCATE")
    assert_blocked("DELETE FROM users;", "DELETE FROM without WHERE")
    assert_allowed("DELETE FROM users WHERE id = 1;")
    assert_blocked("git push origin main --force-with-lease", "git push --force")
    assert_allowed("rm -r ./build")


def test_payload_extraction() -> None:
    assert hook.extract_command({"tool_input": {"command": "npm test"}}) == "npm test"
    assert hook.extract_command({"input": {"cmd": "npm run build"}}) == "npm run build"
    assert hook.extract_command({"command": "python -m pytest"}) == "python -m pytest"


if __name__ == "__main__":
    test_patterns()
    test_payload_extraction()
    print("hook tests passed")
