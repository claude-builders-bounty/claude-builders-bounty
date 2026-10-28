#!/usr/bin/env python3
"""Offline tests for block_destructive.py (no Claude Code required)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block_destructive.py"


def run(command: str, tool_name: str = "Bash", extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    payload = {"tool_name": tool_name, "tool_input": {"command": command}, "cwd": "/tmp/demo"}
    if extra:
        payload.update(extra)
    env = os.environ.copy()
    env["HOME"] = extra.get("HOME") if extra and "HOME" in extra else env["HOME"]
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def main() -> int:
    failures = 0

    def expect(name: str, command: str, blocked: bool, tool: str = "Bash") -> None:
        nonlocal failures
        with tempfile.TemporaryDirectory() as tmp:
            env_home = tmp
            payload = {
                "tool_name": tool,
                "tool_input": {"command": command},
                "cwd": "/tmp/demo",
            }
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": env_home},
                check=False,
            )
            is_blocked = proc.returncode == 2
            ok = is_blocked is blocked
            print(("PASS" if ok else "FAIL"), name, "rc", proc.returncode)
            if not ok:
                failures += 1
                print(proc.stdout)
                print(proc.stderr)
            if blocked and ok:
                log = Path(env_home) / ".claude" / "hooks" / "blocked.log"
                if not log.exists() or "demo" not in log.read_text():
                    print("FAIL", name, "missing log")
                    failures += 1

    expect("rm -rf", "rm -rf /tmp/foo", True)
    expect("rm -fr", "rm -fr ./build", True)
    expect("drop table", "sqlite3 app.db 'DROP TABLE users;'", True)
    expect("force push", "git push --force origin main", True)
    expect("force -f", "git push -f", True)
    expect("truncate", "psql -c 'TRUNCATE sessions'", True)
    expect("delete no where", "psql -c 'DELETE FROM users'", True)
    expect("delete with where", "psql -c 'DELETE FROM users WHERE id = 1'", False)
    expect("normal ls", "ls -la", False)
    expect("normal rm file", "rm README.md", False)
    expect("git status", "git status", False)
    expect("other tool", "rm -rf /", False, tool="Edit")

    if failures:
        print(f"{failures} failed")
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
