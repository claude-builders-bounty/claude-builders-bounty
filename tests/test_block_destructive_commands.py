import json
import subprocess
import sys
from pathlib import Path

HOOK = (
    Path(__file__).resolve().parents[1]
    / "pre-tool-use"
    / "block_destructive_commands.py"
)


def run_hook(command: str) -> tuple[int, str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def test_blocks_rm_rf():
    code, out = run_hook("rm -rf /important")
    assert code == 0
    data = json.loads(out)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_force_push():
    code, out = run_hook("git push --force origin main")
    assert code == 0
    assert "deny" in out


def test_blocks_drop_table():
    code, out = run_hook("psql -c 'DROP TABLE users'")
    assert code == 0
    assert "deny" in out


def test_blocks_truncate():
    code, out = run_hook("TRUNCATE TABLE users")
    assert code == 0
    assert "deny" in out


def test_blocks_delete_without_where():
    code, out = run_hook("DELETE FROM users")
    assert code == 0
    assert "deny" in out


def test_allows_delete_with_where():
    code, out = run_hook("DELETE FROM users WHERE id = 1")
    assert code == 0
    assert out == ""


def test_allows_safe_commands():
    code, out = run_hook("ls -la && git status")
    assert code == 0
    assert out == ""
