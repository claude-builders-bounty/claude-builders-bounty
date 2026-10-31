#!/usr/bin/env python3
"""Local verification for block-destructive-hook.py (trial only, no submission)."""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "block-destructive-hook.py")

BLOCKED = [
    "rm -rf /",
    "sudo rm -rf build/",
    "rm -fr tmp",
    "rm -rfv x",
    "git push --force",
    "git push -f origin main",
    "DROP TABLE users",
    "drop table users",
    "TRUNCATE TABLE logs",
    "DELETE FROM users",
    'psql -c "DELETE FROM users"',
    "rm -rf / && echo hi",
]

ALLOWED = [
    "rm file.txt",
    "rm -r old_dir",
    "git push origin main",
    "DELETE FROM users WHERE id = 1",
    "SELECT * FROM users",
    "ls -la",
    "echo hello",
    "npm install",
    "mkdir -p out",
]


def run_hook(command, home):
    env = dict(os.environ, HOME=home)
    payload = json.dumps({
        "cwd": "/tmp/demo-project",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    })
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True,
        text=True, env=env, timeout=10,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def main():
    failures = []
    with tempfile.TemporaryDirectory() as home:
        for cmd in BLOCKED:
            code, out, err = run_hook(cmd, home)
            if code != 2 or "Blocked" not in err:
                failures.append(f"BLOCKED case failed: {cmd!r} -> exit {code}, err {err!r}")
        for cmd in ALLOWED:
            code, out, err = run_hook(cmd, home)
            if code != 0:
                failures.append(f"ALLOWED case failed: {cmd!r} -> exit {code}, err {err!r}")
        log_path = os.path.join(home, ".claude", "hooks", "blocked.log")
        lines = open(log_path).read().strip().splitlines() if os.path.exists(log_path) else []
        if len(lines) != len(BLOCKED):
            failures.append(f"blocked.log has {len(lines)} lines, expected {len(BLOCKED)}")
        for cmd in BLOCKED:
            if not any(cmd in line and "/tmp/demo-project" in line for line in lines):
                failures.append(f"blocked.log missing entry for: {cmd!r}")

    print(f"blocked cases: {len(BLOCKED)}, allowed cases: {len(ALLOWED)}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
