"""Unit test suite for pre-tool-use destructive bash command blocker hook."""

import json
from pathlib import Path
import subprocess
import sys
import pytest

HOOK_SCRIPT = Path(__file__).parent.parent / "hooks" / "pre_tool_use_block_destructive.py"


def run_hook(command: str, tmp_path: Path, tool_name: str = "Bash") -> tuple[int, str, str]:
    """Helper to run the hook script with given command and temp log path."""
    log_file = tmp_path / "blocked.log"
    env = {"BLOCKED_LOG_PATH": str(log_file)}

    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": str(tmp_path)
    })

    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=payload,
        text=True,
        capture_output=True,
        env=env
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_allowed_safe_commands(tmp_path: Path):
    safe_commands = [
        "ls -la",
        "git status",
        "npm test",
        "pytest tests/",
        "DELETE FROM users WHERE id = 42;",
        "git push origin main",
        "rm file.txt",
    ]
    for cmd in safe_commands:
        code, stdout, stderr = run_hook(cmd, tmp_path)
        assert code == 0, f"Expected safe command to pass: '{cmd}', got stderr: {stderr}"


@pytest.mark.parametrize("cmd,expected_reason", [
    ("rm -rf /tmp/data", "Recursive force removal (`rm -rf`)"),
    ("rm -fr /tmp/data", "Recursive force removal (`rm -rf`)"),
    ("DROP TABLE users;", "SQL `DROP TABLE`"),
    ("drop table orders;", "SQL `DROP TABLE`"),
    ("git push --force origin main", "Force pushing to git"),
    ("git push -f origin main", "Force pushing to git"),
    ("TRUNCATE TABLE session_logs;", "SQL `TRUNCATE`"),
    ("DELETE FROM analytics;", "SQL `DELETE FROM` statement without a `WHERE` clause"),
])
def test_blocked_destructive_commands(tmp_path: Path, cmd: str, expected_reason: str):
    code, stdout, stderr = run_hook(cmd, tmp_path)
    assert code == 1, f"Expected command to be blocked: '{cmd}'"
    assert "SECURITY HOOK BLOCKED" in stderr
    assert expected_reason in stderr

    # Verify logfile entry
    log_file = tmp_path / "blocked.log"
    assert log_file.exists(), "Logfile was not created"
    log_content = log_file.read_text(encoding="utf-8")
    assert cmd in log_content
    assert str(tmp_path) in log_content
