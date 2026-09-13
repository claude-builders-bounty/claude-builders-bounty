#!/usr/bin/env python3
"""Self-test for block_destructive_bash.py - run: python test_hook.py"""
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock
import tempfile

sys.path.insert(0, str(Path(__file__).parent))
from block_destructive_bash import detect_violation, main

BLOCKED = [
    "rm -rf /",
    "rm -rf ./build",
    "sudo rm -fr /tmp/x",
    "psql -c 'DROP TABLE users;'",
    "mysql -e 'drop table sessions'",
    "psql -c 'TRUNCATE TABLE events'",
    "git push --force origin main",
    "git push -f origin main",
    "psql -c 'DELETE FROM users'",
    "psql -c \"DELETE FROM orders\"",
]
ALLOWED = [
    "ls -la",
    "npm test",
    "git push origin main",
    "git push --force-with-lease origin main",
    "rm README.md",
    "rm -i old.txt",
    "grep -r 'DROP TABLE' ./docs",
    "# rm -rf / (commented example in docs)",
    "psql -c 'DELETE FROM users WHERE id = 1'",
    "psql -c 'SELECT * FROM users;'",
    "",
]

fails = 0
for cmd in BLOCKED:
    rule, _ = detect_violation(cmd)
    status = "OK  " if rule else "FAIL"
    if not rule:
        fails += 1
    print(f"[{status}] should BLOCK: {cmd} -> {rule}")

for cmd in ALLOWED:
    rule, _ = detect_violation(cmd)
    status = "OK  " if not rule else "FAIL"
    if rule:
        fails += 1
    print(f"[{status}] should ALLOW: {cmd!r} -> {rule}")

# End-to-end: blocked command exits 2 + writes log; allowed exits 0
with tempfile.TemporaryDirectory() as tmp:
    fake_home = Path(tmp)
    with mock.patch("block_destructive_bash.Path.home", return_value=fake_home):
        payload = json.dumps({"tool_name": "Bash",
                              "tool_input": {"command": "rm -rf /"},
                              "cwd": "/proj/demo"})
        sys.stdin = io.StringIO(payload)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main()
        log = fake_home / ".claude" / "hooks" / "blocked.log"
        ok = (code == 2 and log.exists()
              and "rm -rf /" in log.read_text() and "cwd=/proj/demo" in log.read_text())
        print(f"[{'OK  ' if ok else 'FAIL'}] e2e BLOCK exits 2 + logs (code={code}, log={log.exists()})")
        if not ok:
            fails += 1

        sys.stdin = io.StringIO(json.dumps({"tool_input": {"command": "npm test"}, "cwd": "/proj/demo"}))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main()
        ok = code == 0
        print(f"[{'OK  ' if ok else 'FAIL'}] e2e ALLOW exits 0 (code={code})")
        if not ok:
            fails += 1

sys.stdin = sys.__stdin__
print("ALL PASS" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
