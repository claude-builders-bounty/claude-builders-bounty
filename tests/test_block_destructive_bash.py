#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


def run(command: str):
    event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp/project"}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_blocked(command: str, pattern: str):
    result = run(command)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), f"expected output for {command!r}"
    data = json.loads(result.stdout)
    output = data["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert pattern in output["permissionDecisionReason"]


def assert_allowed(command: str):
    result = run(command)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", result.stdout


def main():
    assert_blocked("rm -rf /tmp/build", "rm -rf")
    assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
    assert_blocked("git push --force origin main", "git push --force")
    assert_blocked("git push -f origin main", "git push --force")
    assert_blocked("sqlite3 app.db 'TRUNCATE TABLE events'", "TRUNCATE")
    assert_blocked("psql -c 'DELETE FROM users'", "DELETE FROM without WHERE")
    assert_allowed("rm /tmp/build.log")
    assert_allowed("git push origin main")
    assert_allowed("psql -c 'DELETE FROM users WHERE id = 42'")
    assert_allowed("npm test")
    print("destructive bash hook tests passed")


if __name__ == "__main__":
    main()
