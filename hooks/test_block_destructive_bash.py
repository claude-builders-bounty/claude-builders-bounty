import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("block_destructive_bash.py")


def run_hook(command: str) -> subprocess.CompletedProcess:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/project",
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_blocks_destructive_commands():
    dangerous = [
        "rm -rf build",
        "psql -c 'DROP TABLE users'",
        "git push origin main --force",
        "sqlite3 app.db 'TRUNCATE sessions'",
        "sqlite3 app.db 'DELETE FROM users'",
    ]
    for command in dangerous:
        result = run_hook(command)
        assert result.returncode == 2, command
        assert "Blocked destructive Bash command" in result.stderr


def test_allows_normal_commands():
    allowed = [
        "ls -la",
        "rm -r build",
        "git push origin main",
        "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        "python -m pytest",
    ]
    for command in allowed:
        result = run_hook(command)
        assert result.returncode == 0, command


if __name__ == "__main__":
    test_blocks_destructive_commands()
    test_allows_normal_commands()
    print("hook tests passed")
