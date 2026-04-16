#!/usr/bin/env python3
"""Tests for block-destructive.py hook."""

import json
import subprocess
import tempfile
import os
from pathlib import Path

HOOK = Path(__file__).parent / "block-destructive.py"

def run_hook(tool_input: dict) -> dict | None:
    """Run the hook with given stdin and return parsed JSON or None."""
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return None  # No output = approved


def test_blocks_rm_rf():
    for cmd in ["rm -rf /tmp/data", "rm -fr /tmp/data", "rm -Rf /tmp/data"]:
        resp = run_hook({"tool_name": "Bash", "tool_input": {"command": cmd}})
        assert resp is not None, f"Should block: {cmd}"
        assert resp["decision"] == "block"
        print(f"  ✅ Blocked: {cmd}")


def test_blocks_drop_table():
    resp = run_hook({"tool_name": "Bash", "tool_input": {"command": "DROP TABLE users;"}})
    assert resp and resp["decision"] == "block"
    print("  ✅ Blocked: DROP TABLE")


def test_blocks_git_push_force():
    for cmd in ["git push --force origin main", "git push -f"]:
        resp = run_hook({"tool_name": "Bash", "tool_input": {"command": cmd}})
        assert resp and resp["decision"] == "block"
        print(f"  ✅ Blocked: {cmd}")


def test_blocks_truncate():
    resp = run_hook({"tool_name": "Bash", "tool_input": {"command": "TRUNCATE TABLE logs;"}})
    assert resp and resp["decision"] == "block"
    print("  ✅ Blocked: TRUNCATE")


def test_blocks_delete_without_where():
    resp = run_hook({"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users;"}})
    assert resp and resp["decision"] == "block"
    print("  ✅ Blocked: DELETE FROM (no WHERE)")


def test_allows_delete_with_where():
    resp = run_hook({"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users WHERE id=1;"}})
    assert resp is None
    print("  ✅ Allowed: DELETE FROM ... WHERE")


def test_allows_normal_commands():
    safe_cmds = [
        "ls -la",
        "git status",
        "python3 main.py",
        "rm temp.txt",  # rm without -rf is fine
        "git push origin main",
        "cat file.txt",
    ]
    for cmd in safe_cmds:
        resp = run_hook({"tool_name": "Bash", "tool_input": {"command": cmd}})
        assert resp is None, f"Should allow: {cmd}"
        print(f"  ✅ Allowed: {cmd}")


def test_ignores_non_bash_tools():
    resp = run_hook({"tool_name": "Read", "tool_input": {"file_path": "test.py"}})
    assert resp is None
    print("  ✅ Ignores non-Bash tools")


def test_logs_blocked_attempt():
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    if log_path.exists():
        log_path.unlink()
    run_hook({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/test"}})
    assert log_path.exists(), "Log file should be created"
    content = log_path.read_text()
    assert "BLOCKED" in content
    assert "rm -rf" in content
    print("  ✅ Logs blocked attempts")


if __name__ == "__main__":
    print("Running hook tests...\n")
    test_blocks_rm_rf()
    test_blocks_drop_table()
    test_blocks_git_push_force()
    test_blocks_truncate()
    test_blocks_delete_without_where()
    test_allows_delete_with_where()
    test_allows_normal_commands()
    test_ignores_non_bash_tools()
    test_logs_blocked_attempt()
    print("\n🎉 All tests passed!")
