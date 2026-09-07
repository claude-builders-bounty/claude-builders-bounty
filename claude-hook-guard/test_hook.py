"""pytest suite for claude-hook-guard hook.py.

Run:  python -m pytest -v
(No third-party deps; imports the sibling hook.py directly.)
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).with_name("hook.py")


def load_hook():
    spec = importlib.util.spec_from_file_location("hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hook = load_hook()

# ---------------------------------------------------------------------------
# The 5 required dangerous patterns: every one must BLOCK
# ---------------------------------------------------------------------------

BLOCK_CASES = [
    ("rm -rf /", "rm_recursive"),
    ("rm -rf ./build", "rm_recursive"),
    ("rm -fr /tmp/x", "rm_recursive"),
    ("rm -r mydir", "rm_recursive"),
    ("rm -R mydir", "rm_recursive"),
    ("rm --recursive somedir", "rm_recursive"),
    ("sudo rm -rf /tmp/x", "rm_recursive"),
    ("/bin/rm -rf /tmp/x", "rm_recursive"),
    ('"rm" -rf /tmp/x', "rm_recursive"),
    ("'rm' -rf /tmp/x", "rm_recursive"),
    ("sudo /bin/rm -rf /tmp/x", "rm_recursive"),
    ("echo hi; rm -rf /tmp/x", "rm_recursive"),
    ("echo hi && rm -rf /tmp/x", "rm_recursive"),
    ("DROP TABLE users", "drop_table"),
    ("drop table users", "drop_table"),
    ("Drop Temporary Table t", "drop_table"),
    ('psql -c "DROP TABLE users;"', "drop_table"),
    ("git push --force origin main", "git_push_force"),
    ("git push -f origin main", "git_push_force"),
    ("git push --force origin main && echo done", "git_push_force"),
    ("git push origin +main", "git_push_force"),
    ("git push origin +refs/heads/main", "git_push_force"),
    ('git push origin "+main"', "git_push_force"),
    ("TRUNCATE TABLE users", "truncate"),
    ("truncate users", "truncate"),
    ('psql -c "truncate table sessions;"', "truncate"),
    ("DELETE FROM users", "delete_no_where"),
    ("delete from users", "delete_no_where"),
    ("DELETE FROM a WHERE x=1; DELETE FROM b", "delete_no_where"),
]


@pytest.mark.parametrize("command,rule", BLOCK_CASES)
def test_dangerous_commands_blocked(command, rule):
    blocked, got_rule, reason = hook.check_command(command)
    assert blocked, f"should BLOCK: {command!r}"
    assert got_rule == rule, f"wrong rule for {command!r}: {got_rule}"
    assert reason, "blocked commands must carry a reason for Claude"


# ---------------------------------------------------------------------------
# Normal commands: every one must PASS THROUGH (exit 0, silent)
# ---------------------------------------------------------------------------

ALLOW_CASES = [
    "ls -la",
    "ls",
    "git status",
    "git diff",
    "git log --oneline -5",
    "git push origin main",
    "git push --force-with-lease origin main",
    "git push --force-if-includes origin main",
    "npm test",
    "npm run build",
    "echo hello",
    "mkdir -p build && npm run build",
    "rm file.txt",
    "rm -f file.txt",
    "rm -i file.txt",
    "SELECT * FROM users",
    "SELECT * FROM users WHERE id = 1",
    "DELETE FROM users WHERE id = 1",
    "delete from users where id=1",
    "grep -rf pattern .",
    "git pull --force",
    "",
    "   ",
]


@pytest.mark.parametrize("command", ALLOW_CASES)
def test_normal_commands_allowed(command):
    blocked, rule, _ = hook.check_command(command)
    assert not blocked, f"should ALLOW: {command!r} (matched {rule})"


# ---------------------------------------------------------------------------
# Documented edge-case choices
# ---------------------------------------------------------------------------

def test_force_with_lease_allowed_but_force_blocked():
    assert hook.check_command("git push --force origin main")[0] is True
    assert hook.check_command("git push --force-with-lease origin main")[0] is False


def test_delete_with_where_allowed_without_blocked():
    assert hook.check_command("DELETE FROM users")[0] is True
    assert hook.check_command("DELETE FROM users WHERE id = 1")[0] is False


def test_sql_case_insensitive():
    assert hook.check_command("drop table t")[0] is True
    assert hook.check_command("truncate t")[0] is True
    assert hook.check_command("delete from t")[0] is True


# ---------------------------------------------------------------------------
# Hook I/O contract: stdin JSON -> exit code + stdout JSON + stderr + log
# ---------------------------------------------------------------------------

def _run_hook(payload, env_extra=None):
    env = dict(os.environ)
    env.pop("CLAUDE_HOOK_BLOCKED_LOG", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return proc


def test_hook_blocks_rm_via_stdin_json(tmp_path):
    log = tmp_path / "blocked.log"
    proc = _run_hook(
        {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "/tmp/proj"},
        {"CLAUDE_HOOK_BLOCKED_LOG": str(log)},
    )
    assert proc.returncode == 2, f"blocked must exit 2, got {proc.returncode}: {proc.stderr}"
    data = json.loads(proc.stdout)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert data["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "rm" in data["hookSpecificOutput"]["permissionDecisionReason"].lower()
    assert "rm" in proc.stderr.lower()  # human message also on stderr
    logged = log.read_text(encoding="utf-8")
    assert "rm -rf /" in logged and "/tmp/proj" in logged and "BLOCKED" in logged


def test_hook_allows_normal_command(tmp_path):
    log = tmp_path / "blocked.log"
    proc = _run_hook(
        {"tool_name": "Bash", "tool_input": {"command": "npm test"}, "cwd": "/tmp/proj"},
        {"CLAUDE_HOOK_BLOCKED_LOG": str(log)},
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "", "allowed commands must stay silent on stdout"
    assert not log.exists(), "allowed commands must not be logged"


@pytest.mark.parametrize(
    "command",
    ["DROP TABLE t", "TRUNCATE TABLE t", "git push --force", "DELETE FROM t"],
)
def test_hook_blocks_each_required_pattern_end_to_end(tmp_path, command):
    log = tmp_path / "blocked.log"
    proc = _run_hook(
        {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/proj"},
        {"CLAUDE_HOOK_BLOCKED_LOG": str(log)},
    )
    assert proc.returncode == 2, command
    assert "deny" in proc.stdout
    assert command in log.read_text(encoding="utf-8")


def test_hook_empty_or_missing_command_allows():
    assert _run_hook({}).returncode == 0
    assert _run_hook({"tool_name": "Bash", "tool_input": {}}).returncode == 0
    assert _run_hook({"tool_name": "Bash"}).returncode == 0


def test_logging_format_has_timestamp_command_and_path(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_HOOK_BLOCKED_LOG", str(tmp_path / "b.log"))
    path = hook.log_blocked("DROP TABLE t", "/my/proj", "drop_table")
    assert path is not None
    line = Path(path).read_text(encoding="utf-8")
    assert "BLOCKED" in line and "DROP TABLE t" in line and "/my/proj" in line
    assert "rule=drop_table" in line
    assert line.startswith("[") and "]" in line  # timestamp bracket


def test_parse_hook_input_tolerates_garbage():
    assert hook.parse_hook_input("")[0] == ""
    assert hook.parse_hook_input("not json")[0] == ""
    cmd, cwd = hook.parse_hook_input(json.dumps({"tool_input": {"command": "ls"}, "cwd": "/x"}))
    assert cmd == "ls" and cwd == "/x"
