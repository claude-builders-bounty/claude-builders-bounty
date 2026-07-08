#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "hooks/block-dangerous-bash.py"


def run_hook(command: str, home: Path, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "Blocked destructive Bash command" in hook_output["permissionDecisionReason"]


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        home = Path(temp_dir)
        blocked_commands = [
            "rm -rf build",
            "rm -fr /tmp/example",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "sqlite3 app.db 'TRUNCATE audit_log'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in blocked_commands:
            assert_blocked(command, home)

        allowed_commands = [
            "rm build.log",
            "git push origin main",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "python3 -m pytest",
            "echo safe",
        ]
        for command in allowed_commands:
            result = run_hook(command, home)
            assert result.returncode == 0
            assert result.stdout == ""

        other_tool = run_hook("rm -rf build", home, tool_name="Read")
        assert other_tool.returncode == 0
        assert other_tool.stdout == ""

        log_path = home / ".claude/hooks/blocked.log"
        lines = log_path.read_text().splitlines()
        assert len(lines) == len(blocked_commands)
        first = json.loads(lines[0])
        assert first["attempted_command"] == "rm -rf build"
        assert first["project_path"] == "/tmp/example-project"
        assert "timestamp" in first

    print("tests_ok=true")


if __name__ == "__main__":
    main()
