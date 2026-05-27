import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "destructive-command-guard.py"


def run_hook(command, tmp_path):
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(tmp_path / "project"),
    }
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_allows_normal_bash_command(tmp_path):
    result = run_hook("npm test", tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""
    assert not (tmp_path / ".claude" / "hooks" / "blocked.log").exists()


def test_blocks_required_dangerous_patterns_and_logs(tmp_path):
    commands = [
        "rm -rf dist",
        "DROP TABLE users",
        "git push --force origin main",
        "TRUNCATE audit_logs",
        "DELETE FROM sessions",
    ]

    for command in commands:
        result = run_hook(command, tmp_path)

        assert result.returncode == 0
        output = json.loads(result.stdout)
        hook_output = output["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "deny"
        assert "Blocked destructive Bash command" in hook_output["permissionDecisionReason"]

    log_path = tmp_path / ".claude" / "hooks" / "blocked.log"
    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(log_lines) == len(commands)
    for line, command in zip(log_lines, commands):
        entry = json.loads(line)
        assert entry["command"] == command
        assert entry["project_path"].endswith("project")
        assert entry["timestamp"]


def test_allows_delete_from_when_where_clause_is_present(tmp_path):
    result = run_hook("DELETE FROM sessions WHERE expires_at < NOW()", tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""
