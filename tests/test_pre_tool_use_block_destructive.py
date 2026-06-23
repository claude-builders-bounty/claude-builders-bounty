import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre_tool_use_block_destructive.py"


def run_hook(command: str, tmp_path: Path):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(tmp_path / "project"),
    }
    env = os.environ.copy()
    env["CLAUDE_HOOK_LOG_PATH"] = str(tmp_path / "blocked.log")
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_allows_normal_bash_commands(tmp_path):
    result = run_hook("git status && npm test", tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert not (tmp_path / "blocked.log").exists()


def test_ignores_non_bash_tool_payload(tmp_path):
    payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    env = os.environ.copy()
    env["CLAUDE_HOOK_LOG_PATH"] = str(tmp_path / "blocked.log")

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert not (tmp_path / "blocked.log").exists()


def test_blocks_recursive_force_remove(tmp_path):
    result = run_hook("sudo rm -rf /tmp/demo", tmp_path)

    assert result.returncode == 2
    assert "recursive force" in result.stderr.lower()
    assert "rm -rf /tmp/demo" in (tmp_path / "blocked.log").read_text()


def test_blocks_drop_table(tmp_path):
    result = run_hook("psql -c 'DROP TABLE users'", tmp_path)

    assert result.returncode == 2
    assert "drop table" in result.stderr.lower()


def test_blocks_truncate(tmp_path):
    result = run_hook("mysql -e 'TRUNCATE TABLE audit_log'", tmp_path)

    assert result.returncode == 2
    assert "truncate" in result.stderr.lower()


def test_blocks_force_push(tmp_path):
    result = run_hook("git push origin main --force-with-lease", tmp_path)

    assert result.returncode == 2
    assert "force-pushing" in result.stderr.lower()


def test_blocks_delete_without_where(tmp_path):
    result = run_hook("psql -c 'DELETE FROM sessions'", tmp_path)

    assert result.returncode == 2
    assert "where clause" in result.stderr.lower()


def test_allows_delete_with_where(tmp_path):
    result = run_hook("psql -c 'DELETE FROM sessions WHERE id = 123'", tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""


def test_block_log_contains_project_path_and_rule(tmp_path):
    result = run_hook("DROP TABLE invoices", tmp_path)

    assert result.returncode == 2
    lines = (tmp_path / "blocked.log").read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["project_path"] == str(tmp_path / "project")
    assert entry["rule"] == "drop table"
    assert entry["command"] == "DROP TABLE invoices"
    assert "timestamp" in entry
