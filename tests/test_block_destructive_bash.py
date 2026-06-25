#!/usr/bin/env python3
"""Smoke tests for the destructive Bash Claude Code hook."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env={**os.environ, "HOME": str(home)},
        check=False,
    )


def load_hook_module():
    spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_blocks_required_patterns() -> None:
    hook = load_hook_module()
    blocked = [
        "rm -rf dist",
        "DROP TABLE users;",
        "git push origin main --force",
        "TRUNCATE audit_log;",
        "DELETE FROM users;",
    ]
    for command in blocked:
        assert hook.blocked_reason(command), command


def test_allows_safe_commands() -> None:
    hook = load_hook_module()
    allowed = [
        "ls -la",
        "git status --short",
        "rm -f tmp.txt",
        "DELETE FROM users WHERE id = 1;",
    ]
    for command in allowed:
        assert hook.blocked_reason(command) is None, command


def test_blocked_attempt_is_logged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        result = run_hook("rm -rf build", home)
        assert result.returncode == 2
        assert "Blocked destructive Bash command" in result.stderr

        log_path = home / ".claude" / "hooks" / "blocked.log"
        log_line = log_path.read_text(encoding="utf-8").strip()
        entry = json.loads(log_line)
        assert entry["command"] == "rm -rf build"
        assert entry["project_path"] == "/tmp/example-project"


if __name__ == "__main__":
    test_blocks_required_patterns()
    test_allows_safe_commands()
    test_blocked_attempt_is_logged()
    print("ok")
