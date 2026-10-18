#!/usr/bin/env python3
"""Tests for destructive-guard.py — pipes the hook's stdin JSON contract,
asserts exit code 2 (deny) on dangerous commands and 0 (allow) on safe ones.

Run: python test_hook.py
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "hooks", "destructive-guard.py")

BLOCKED = [
    "rm -rf /tmp/x",
    "rm -fr node_modules",
    "git push --force origin main",
    "git push -f origin main",
    "DROP TABLE users;",
    "TRUNCATE TABLE sessions",
    "DELETE FROM users",
    "git reset --hard origin/main",
]
ALLOWED = [
    "ls -la",
    "git status",
    "DELETE FROM users WHERE id = 3",
    "rm file.txt",
    "git push origin feature-branch",
    "pytest -q",
]


def run_hook(command):
    event = {"tool_name": "Bash",
             "tool_input": {"command": command}, "cwd": tempfile.gettempdir()}
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                       capture_output=True, text=True)
    return p.returncode


def main():
    fails = []
    for c in BLOCKED:
        rc = run_hook(c)
        if rc != 2:
            fails.append(f"should block but allowed (rc={rc}): {c}")
    for c in ALLOWED:
        rc = run_hook(c)
        if rc != 0:
            fails.append(f"should allow but blocked (rc={rc}): {c}")
    for f in fails:
        print("FAIL:", f)
    print(f"{len(BLOCKED)+len(ALLOWED)-len(fails)}/"
          f"{len(BLOCKED)+len(ALLOWED)} checks passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
