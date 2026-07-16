"""Tests for pre-tool-use destructive command blocker."""
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent / "pre_tool_use_block_destructive.py"


def run_hook(command: str, tool_name: str = "Bash") -> dict:
    """Run the hook with a simulated command and return the response."""
    inp = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=inp,
        capture_output=True,
        text=True,
    )
    if result.returncode == 2:
        return json.loads(result.stdout)
    return {"decision": "allow"}


# Tests for blocked commands
def test_block_rm_rf():
    r = run_hook("rm -rf /tmp/test")
    assert r["decision"] == "block"
    assert "rm -rf" in r["reason"]


def test_block_rm_fr():
    r = run_hook("rm -fr /home")
    assert r["decision"] == "block"


def test_block_drop_table():
    r = run_hook("psql -c 'DROP TABLE users'")
    assert r["decision"] == "block"
    assert "DROP" in r["reason"]


def test_block_truncate():
    r = run_hook("psql -c 'TRUNCATE TABLE logs'")
    assert r["decision"] == "block"


def test_block_delete_without_where():
    r = run_hook("psql -c 'DELETE FROM users'")
    assert r["decision"] == "block"
    assert "DELETE" in r["reason"]


def test_block_delete_with_where_allowed():
    r = run_hook("psql -c 'DELETE FROM users WHERE id = 1'")
    assert r["decision"] == "allow"


def test_block_git_push_force():
    r = run_hook("git push --force origin main")
    assert r["decision"] == "block"
    assert "force" in r["reason"].lower()


def test_block_git_reset_hard():
    r = run_hook("git reset --hard HEAD~3")
    assert r["decision"] == "block"


def test_block_mkfs():
    r = run_hook("mkfs.ext4 /dev/sda1")
    assert r["decision"] == "block"


def test_block_dd_to_device():
    r = run_hook("dd if=/dev/zero of=/dev/sda bs=1M")
    assert r["decision"] == "block"


def test_block_fork_bomb():
    r = run_hook(":(){ :|:& };:")
    assert r["decision"] == "block"


# Tests for allowed commands
def test_allow_ls():
    r = run_hook("ls -la")
    assert r["decision"] == "allow"


def test_allow_git_status():
    r = run_hook("git status")
    assert r["decision"] == "allow"


def test_allow_python():
    r = run_hook("python3 script.py")
    assert r["decision"] == "allow"


def test_allow_normal_rm():
    r = run_hook("rm file.txt")
    assert r["decision"] == "allow"


def test_allow_non_bash_tool():
    r = run_hook("rm -rf /", tool_name="Read")
    assert r["decision"] == "allow"


def test_allow_empty_command():
    r = run_hook("")
    assert r["decision"] == "allow"
