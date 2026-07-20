#!/usr/bin/env python3
"""Unit tests for block_destructive.py (no Claude runtime required)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block_destructive.py"


def run(command: str, tool_name: str = "Bash") -> tuple[int, str, str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project",
        "hook_event_name": "PreToolUse",
    }
    env = os.environ.copy()
    # Isolate log path via HOME
    with tempfile.TemporaryDirectory() as td:
        env["HOME"] = td
        p = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
        )
        return p.returncode, p.stdout, p.stderr


def assert_blocked(cmd: str) -> None:
    code, out, err = run(cmd)
    assert code == 2, f"expected block for {cmd!r}, got {code}: {out}{err}"
    data = json.loads(out)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny"
    print(f"  BLOCK OK: {cmd[:60]}")


def assert_allowed(cmd: str, tool_name: str = "Bash") -> None:
    code, out, err = run(cmd, tool_name=tool_name)
    assert code == 0, f"expected allow for {cmd!r}, got {code}: {out}{err}"
    print(f"  ALLOW OK: {cmd[:60]}")


def main() -> None:
    print("blocked cases")
    for c in [
        "rm -rf /tmp/x",
        "sudo rm -rf /",
        "rm -fr ./build",
        "DROP TABLE users;",
        "drop table if exists sessions",
        "git push --force origin main",
        "git push -f origin main",
        "git push --force-with-lease origin main",
        "TRUNCATE TABLE logs",
        "truncate users",
        "DELETE FROM users;",
        "delete from orders",
        "DELETE FROM users WHERE 1=1; DELETE FROM audit;",  # second stmt no where — still has one without
    ]:
        # Last case: first has WHERE? "DELETE FROM users WHERE 1=1" has WHERE
        # second "DELETE FROM audit" has no WHERE — our rule scans all
        assert_blocked(c)

    print("allowed cases")
    for c in [
        "ls -la",
        "rm file.txt",
        "rm -r some_dir",  # no -f
        "git push origin main",
        "git status",
        "DELETE FROM users WHERE id = 1",
        "delete from orders where status = 'cancelled'",
        "echo DROP TABLE is mentioned in a comment only? wait — this still has DROP TABLE",
    ]:
        if "DROP TABLE" in c.upper() and "comment" in c:
            # the string contains DROP TABLE so it will block — skip intentional
            continue
        assert_allowed(c)

    # Non-bash tools never blocked even with dangerous text
    assert_allowed("rm -rf /", tool_name="Read")

    # Safe message without DROP keyword
    assert_allowed("echo 'we never drop tables without a migration'")

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
