#!/usr/bin/env python3

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def run_hook(payload, home):
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


def test_pattern_detection():
    blocked = [
        "rm -rf /tmp/demo",
        "DROP TABLE users;",
        "git push origin main --force",
        "TRUNCATE audit_log;",
        "DELETE FROM users;",
    ]
    for command in blocked:
        if module.first_block_reason(command) is None:
            raise AssertionError(f"should block: {command}")

    allowed = [
        "rm -r /tmp/demo",
        "git push origin feature/safe",
        "DELETE FROM users WHERE id = 1;",
        "echo 'DROP by later migration note'",
    ]
    for command in allowed:
        if module.first_block_reason(command) is not None:
            raise AssertionError(f"should allow: {command}")


def test_hook_blocks_and_logs():
    with tempfile.TemporaryDirectory() as temp_home:
        result = run_hook(
            {"tool_input": {"command": "rm -rf build"}, "cwd": "/repo"},
            Path(temp_home),
        )
        assert_equal(result.returncode, 2, "blocked return code")
        if "Blocked destructive Bash command" not in result.stderr:
            raise AssertionError(result.stderr)
        log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
        log_text = log_path.read_text(encoding="utf-8")
        if "/repo\trm -rf" not in log_text:
            raise AssertionError(log_text)


def test_hook_allows_normal_commands():
    with tempfile.TemporaryDirectory() as temp_home:
        result = run_hook(
            {"tool_input": {"command": "git status --short"}, "cwd": "/repo"},
            Path(temp_home),
        )
        assert_equal(result.returncode, 0, "allowed return code")
        log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
        if log_path.exists():
            raise AssertionError("normal commands must not be logged")


def main():
    test_pattern_detection()
    test_hook_blocks_and_logs()
    test_hook_allows_normal_commands()
    print("All tests passed")


if __name__ == "__main__":
    main()
