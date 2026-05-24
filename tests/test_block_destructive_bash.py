import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block-destructive-bash" / "block_destructive_bash.py"


def run_hook(command: str, tmp_path: Path):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/repo"}
    env = os.environ.copy()
    env["CLAUDE_BLOCKED_LOG"] = str(tmp_path / "blocked.log")
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_normal_command_allowed(tmp_path):
    result = run_hook("git status && ls -la", tmp_path)
    assert result.returncode == 0
    assert not (tmp_path / "blocked.log").exists()


def test_rm_rf_blocked_and_logged(tmp_path):
    result = run_hook("rm -rf build", tmp_path)
    assert result.returncode == 1
    assert "rm -rf" in result.stderr
    assert "command=rm -rf build" in (tmp_path / "blocked.log").read_text()


def test_delete_from_without_where_blocked(tmp_path):
    result = run_hook("psql -c 'DELETE FROM users;'", tmp_path)
    assert result.returncode == 1
    assert "DELETE FROM without WHERE" in result.stderr


def test_delete_from_with_where_allowed(tmp_path):
    result = run_hook("psql -c 'DELETE FROM users WHERE id = 1;'", tmp_path)
    assert result.returncode == 0
