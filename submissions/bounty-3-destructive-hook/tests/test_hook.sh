#!/usr/bin/env bash
set -euo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/pre-tool-use.py"

python3 - "$HOOK" <<'PY'
import json, subprocess, sys

hook = sys.argv[1]
cases = [
    ("rm -rf /tmp", 2),
    ("DROP TABLE users", 2),
    ("TRUNCATE TABLE logs", 2),
    ("git push origin main --force", 2),
    ("DELETE FROM orders", 2),
    ("DELETE FROM orders WHERE id = 1", 0),
    ("git status", 0),
    ("ls -la", 0),
]

for cmd, expected in cases:
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "/tmp/test"}
    proc = subprocess.run(["python3", hook], input=json.dumps(payload), text=True, capture_output=True)
    if proc.returncode != expected:
        print(f"FAIL expected={expected} got={proc.returncode} cmd={cmd!r}", file=sys.stderr)
        sys.exit(1)
    print(f"PASS {cmd!r}")

print("All hook tests passed.")
PY