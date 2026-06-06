#!/usr/bin/env python3

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"
spec = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def assert_blocked(command, expected):
    reason = hook.blocked_reason(command)
    assert reason is not None, f"expected block for: {command}"
    assert expected in reason, reason


def assert_allowed(command):
    reason = hook.blocked_reason(command)
    assert reason is None, f"expected allow for: {command}, got {reason}"


def run_tests():
    assert_blocked("rm -rf /tmp/example", "rm -rf")
    assert_blocked("DROP TABLE users", "DROP TABLE")
    assert_blocked("git push --force origin main", "forced git pushes")
    assert_blocked("git push -f origin main", "forced git pushes")
    assert_blocked("TRUNCATE TABLE audit_log", "TRUNCATE")
    assert_blocked("DELETE FROM users", "DELETE FROM without WHERE")
    assert_blocked("psql -c 'SELECT 1'; DELETE FROM sessions;", "DELETE FROM without WHERE")

    assert_allowed("rm -r ./build")
    assert_allowed("echo 'rm -rf /tmp/example'")
    assert_allowed("git push origin feature/destructive-command-hook")
    assert_allowed("DELETE FROM users WHERE id = 42")
    assert_allowed("SELECT 'DROP TABLE users'")
    assert hook.extract_command({"tool_name": "Bash", "tool_input": {"command": "echo ok"}}) == "echo ok"
    assert hook.extract_command({"tool_name": "Read", "tool_input": {"command": "rm -rf /"}}) == ""


if __name__ == "__main__":
    run_tests()
    print("all tests passed")
