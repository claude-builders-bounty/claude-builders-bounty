import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("block_destructive_bash.py")


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command, "cwd": "/tmp/example-project"},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_blocks_required_patterns():
    blocked = [
        "rm -rf build",
        "psql -c 'DROP TABLE users;'",
        "git push --force origin main",
        "git push -f origin main",
        "sqlite3 app.db 'TRUNCATE users;'",
        "sqlite3 app.db 'DELETE FROM users;'",
    ]
    for command in blocked:
        result = run_hook(command)
        assert result.returncode != 0, command
        assert "Blocked destructive Bash command" in result.stderr


def test_allows_normal_commands():
    allowed = [
        "ls -la",
        "rm build/output.log",
        "git push origin main",
        "sqlite3 app.db 'DELETE FROM users WHERE id = 1;'",
        "npm test",
    ]
    for command in allowed:
        result = run_hook(command)
        assert result.returncode == 0, command
        assert result.stderr == ""
