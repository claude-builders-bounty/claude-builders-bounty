import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre_tool_use_blocker.py"


def run_hook(payload, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
    )


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp/project"}


def test_blocks_required_patterns(tmp_path):
    commands = [
        "rm -rf build",
        "psql -c 'DROP TABLE users'",
        "git push origin main --force",
        "TRUNCATE audit_log;",
        "DELETE FROM users;",
    ]
    for command in commands:
        result = run_hook(bash(command), tmp_path)
        assert result.returncode == 2, command
        assert "Blocked by pre-tool-use safety hook" in result.stderr

    log_file = tmp_path / ".claude" / "hooks" / "blocked.log"
    log_text = log_file.read_text()
    assert "rm -rf build" in log_text
    assert "/tmp/project" in log_text


def test_allows_normal_commands(tmp_path):
    result = run_hook(bash("python -m pytest"), tmp_path)
    assert result.returncode == 0
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "hooks" / "blocked.log").exists()


def test_allows_delete_with_where(tmp_path):
    result = run_hook(bash("DELETE FROM users WHERE id = 1;"), tmp_path)
    assert result.returncode == 0


def test_ignores_non_bash_tool(tmp_path):
    result = run_hook({"tool_name": "Read", "tool_input": {"file_path": "README.md"}}, tmp_path)
    assert result.returncode == 0
