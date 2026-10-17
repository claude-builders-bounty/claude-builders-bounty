#!/usr/bin/env python3
"""Tests for block_destructive.py — runs the real hook as a subprocess.

    python test_hook.py     ->  prints results, exits 1 on any failure
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "block_destructive.py")

BLOCK = [
    "rm -rf node_modules",
    "rm -fr build",
    "rm -r -f dist",
    "rm --recursive --force tmp",
    "psql -c 'DROP TABLE users'",
    "DROP TABLE users;",
    "TRUNCATE TABLE logs",
    "TRUNCATE sessions;",
    "DELETE FROM users",
    "psql -d app -c 'DELETE FROM users'",
    "git push --force",
    "git push -f origin main",
    "ls && rm -rf tmp",
    "mysql -e 'TRUNCATE sessions'",
]

ALLOW = [
    "ls -la",
    "rm file.txt",
    "rm -r dir",
    "rm -f file",
    "git push",
    "git push --force-with-lease",
    "git push origin feature/x",
    "DELETE FROM users WHERE id = 1",
    "psql -c 'DELETE FROM users WHERE id=1'",
    "npm test",
    'echo "DROP TABLE users"',
    'git commit -m "DROP TABLE fix"',
    "pytest -q",
    "guard:allow rm -rf node_modules",
]


def run(command, log):
    env = dict(os.environ, CLAUDE_BLOCK_LOG=log)
    payload = json.dumps({"cwd": "/proj/demo", "tool_input": {"command": command}})
    p = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )
    return p.returncode, p.stderr


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "blocked.log")

        for cmd in BLOCK:
            rc, err = run(cmd, log)
            ok = rc == 2 and "BLOCKED" in err
            fails += 0 if ok else 1
            print(f"{'OK  ' if ok else 'FAIL'}  block(exit {rc})  {cmd}")

        for cmd in ALLOW:
            rc, err = run(cmd, log)
            ok = rc == 0
            fails += 0 if ok else 1
            print(f"{'OK  ' if ok else 'FAIL'}  allow(exit {rc})  {cmd}")

        # the log must contain timestamp, project path and command for each block
        lines = open(log, encoding="utf-8").read().strip().splitlines() if os.path.exists(log) else []
        log_ok = len(lines) == len(BLOCK) and all(
            "/proj/demo" in ln and "|" in ln and ln.startswith("[") for ln in lines
        )
        fails += 0 if log_ok else 1
        print(f"{'OK  ' if log_ok else 'FAIL'}  log: {len(lines)} lines, all with timestamp+path (expected {len(BLOCK)})")

        # sample of the log format
        if lines:
            print("\nsample log line:\n  " + lines[0])

    print("\n" + ("ALL PASS" if fails == 0 else f"{fails} FAILED"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
