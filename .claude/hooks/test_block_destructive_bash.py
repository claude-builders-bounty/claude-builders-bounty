import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("block_destructive_bash.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def test_required_patterns_are_blocked():
    cases = {
        "rm -rf /tmp/build": "recursive force delete",
        "rm -r -f /tmp/build": "recursive force delete",
        "rm -fr /tmp/build": "recursive force delete",
        "psql -c 'DROP TABLE users'": "DROP TABLE",
        "git push origin main --force": "forced git push",
        "git push --force-with-lease": "forced git push",
        "psql -c 'TRUNCATE audit_log'": "TRUNCATE",
        "psql -c 'DELETE FROM users'": "DELETE statement without WHERE",
    }

    for command, expected in cases.items():
        assert expected in guard.find_block_reason(command)


def test_safe_commands_are_allowed():
    allowed = [
        "npm test",
        "git push origin feature-branch",
        "rm ./single-file.txt",
        "psql -c 'DELETE FROM users WHERE id = 1'",
        "python -m pytest",
    ]

    for command in allowed:
        assert guard.find_block_reason(command) is None


def test_hook_outputs_deny_json_for_blocked_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /tmp/build"},
        "cwd": "/work/project",
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "rm -rf" in hook_output["permissionDecisionReason"]

    log_entries = (tmp_path / ".claude" / "hooks" / "blocked.log").read_text().splitlines()
    assert len(log_entries) == 1
    entry = json.loads(log_entries[0])
    assert entry["command"] == "rm -rf /tmp/build"
    assert entry["project_path"] == "/work/project"


def test_hook_allows_normal_command_without_stdout():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "npm test"},
        "cwd": "/work/project",
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
