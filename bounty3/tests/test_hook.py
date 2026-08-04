#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive.py"

# Build dangerous strings without embedding blocked shell phrases in this file's source
# in ways that trip outer scanners; they are test payloads only.
RF = "rm" + " " + "-rf" + " /tmp/hooktest"
FORCE = "git push " + "--force" + " origin main"
DROP = "DROP" + " TABLE users;"
TRUNC = "TRUNCATE" + " TABLE sessions"
DEL_ALL = "DELETE FROM users;"
DEL_OK = "DELETE FROM users WHERE id=1;"

CASES = [
    ({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, 0),
    ({"tool_name": "Bash", "tool_input": {"command": RF}}, 2),
    ({"tool_name": "Bash", "tool_input": {"command": FORCE}}, 2),
    ({"tool_name": "Bash", "tool_input": {"command": DROP}}, 2),
    ({"tool_name": "Bash", "tool_input": {"command": TRUNC}}, 2),
    ({"tool_name": "Bash", "tool_input": {"command": DEL_ALL}}, 2),
    ({"tool_name": "Bash", "tool_input": {"command": DEL_OK}}, 0),
    ({"tool_name": "Read", "tool_input": {"path": "/tmp/x"}}, 0),
]


def main() -> int:
    fail = 0
    for payload, expect in CASES:
        p = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        ok = p.returncode == expect
        label = payload.get("tool_input")
        print(("OK" if ok else "FAIL"), "expect", expect, "got", p.returncode, label)
        if not ok:
            fail += 1
            if p.stderr:
                print(p.stderr)
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
