import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("pre_tool_use_guard.py")


def run(command: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"cwd": "/tmp/project", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=False,
    )


def test_safe_commands_are_allowed():
    for command in ("ls -la", "git push origin main", "DELETE FROM users WHERE id = 1"):
        assert run(command).returncode == 0


def test_dangerous_commands_are_denied():
    for command in (
        "rm -rf ./build",
        "DROP TABLE users",
        "git push --force origin main",
        "TRUNCATE TABLE users",
        "DELETE FROM users",
    ):
        result = run(command)
        assert result.returncode == 2
        assert "Blocked dangerous command" in result.stderr
        assert '"decision": "deny"' in result.stdout
