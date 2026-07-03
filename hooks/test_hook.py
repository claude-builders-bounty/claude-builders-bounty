"""Test destructive bash hook — all bounty acceptance patterns."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent / "block_destructive.py"
sys.path.insert(0, str(HOOK.parent))
import block_destructive as hook  # noqa: E402


def run_hook(cmd: str, cwd: str = "/test/project") -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"command": cmd}, "cwd": cwd})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )


def test_allows_safe_commands():
    for cmd in ("ls -la", "echo hello", "git status", "python -m pytest"):
        assert run_hook(cmd).returncode == 0, cmd


def test_blocks_destructive_patterns():
    blocked = (
        "rm -rf /",
        "rm -fr /tmp",
        "git push --force origin main",
        "git push origin main --force",
        "git push -f origin main",
        "DROP TABLE users",
        "TRUNCATE logs",
        "DELETE FROM users",
    )
    for cmd in blocked:
        r = run_hook(cmd)
        assert r.returncode == 2, cmd
        assert "BLOCKED" in r.stderr, cmd


def test_allows_delete_with_where():
    assert run_hook("DELETE FROM users WHERE id = 1").returncode == 0


def test_check_unit():
    assert hook.check("ls")[0] is True
    ok, reason = hook.check("rm -rf /tmp")
    assert ok is False and reason == "rm -rf"


def test_logs_blocked_attempt():
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "blocked.log"
        original = hook.LOG
        hook.LOG = log
        try:
            hook.log_block("rm -rf /", "rm -rf", "/my/project")
            assert log.exists()
            content = log.read_text(encoding="utf-8")
            assert "rm -rf" in content
            assert "/my/project" in content
            assert "rm -rf /" in content
        finally:
            hook.LOG = original


def test_end_to_end_logs_on_block():
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "HOME": tmp, "USERPROFILE": tmp}
        payload = json.dumps({"tool_input": {"command": "DROP TABLE secrets"}, "cwd": "/repo/acme"})
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
        )
        log = Path(tmp) / ".claude" / "hooks" / "blocked.log"
        assert r.returncode == 2
        assert log.exists()
        parts = log.read_text(encoding="utf-8").strip().split("\t")
        assert len(parts) == 4
        assert parts[2] == "/repo/acme"
        assert "DROP TABLE" in parts[3]


def test_allows_chained_safe_commands():
    assert run_hook("git log -1 && echo ok").returncode == 0


def test_blocks_destructive_in_chain():
    chained = (
        "echo starting && rm -rf /tmp/build",
        "git status; DROP TABLE audit",
        "npm test || git push --force origin main",
    )
    for cmd in chained:
        r = run_hook(cmd)
        assert r.returncode == 2, cmd
        assert "BLOCKED" in r.stderr, cmd


if __name__ == "__main__":
    test_allows_safe_commands()
    test_blocks_destructive_patterns()
    test_allows_delete_with_where()
    test_check_unit()
    test_logs_blocked_attempt()
    test_end_to_end_logs_on_block()
    test_allows_chained_safe_commands()
    test_blocks_destructive_in_chain()
    print("all tests passed")
