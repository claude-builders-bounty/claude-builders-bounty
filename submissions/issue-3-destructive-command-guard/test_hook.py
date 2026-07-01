#!/usr/bin/env python3
"""
Runs block-destructive.py as a subprocess (JSON on stdin, exactly how Claude Code
invokes it) and checks that dangerous commands are denied and normal ones pass.

    python3 test_hook.py
"""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-destructive.py")

# (command, should_be_blocked)
CASES = [
    # --- must BLOCK ---
    ("rm -rf /", True),
    ("rm -fr build", True),
    ("rm -r -f node_modules", True),
    ("sudo rm -Rf /var/tmp/x", True),
    ("rm --recursive --force dist", True),
    ("ls && rm -rf ./cache", True),                       # dangerous 2nd segment
    ("git push --force origin main", True),
    ("git push -f", True),
    ("psql -c 'DROP TABLE users'", True),
    ("mysql -e 'drop database prod'", True),
    ("sqlite3 app.db 'TRUNCATE logs'", True),
    ("psql -c 'DELETE FROM sessions'", True),             # no WHERE
    ("echo hi; DELETE FROM orders", True),
    # --- must ALLOW (normal commands, no interference) ---
    ("rm file.txt", False),                               # not recursive+force
    ("rm -r old_dir", False),                             # recursive but not force
    ("rm -i secret.txt", False),
    ("git push origin main", False),
    ("git push --force-with-lease origin feature", False),  # the safe variant
    ("psql -c 'DELETE FROM sessions WHERE id = 5'", False),  # has WHERE
    ("psql -c 'SELECT * FROM users'", False),
    ("ls -la && npm run build", False),
    ("grep -rf patterns.txt src/", False),                # -rf here is grep flags, but...
]

# NOTE: the last case ("grep -rf") is intentionally a known trade-off — see README.
# grep's -r/-f are unrelated to rm, but our matcher keys on the leading command, so
# because the segment starts with `grep` (not `rm`), it is correctly ALLOWED.


def run(command):
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/demo-project",
    })
    env = {**os.environ, "CLAUDE_HOOK_LOG": os.path.join(os.path.dirname(HOOK), ".test-blocked.log")}
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload,
        capture_output=True, text=True, timeout=10, env=env,
    )
    blocked = False
    if proc.stdout.strip():
        try:
            out = json.loads(proc.stdout)
            blocked = out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        except ValueError:
            pass
    return blocked, proc


def main():
    passed = failed = 0
    for command, expect_block in CASES:
        blocked, proc = run(command)
        ok = blocked == expect_block
        if proc.returncode != 0:
            ok = False
        tag = "PASS" if ok else "FAIL"
        verb = "BLOCK" if blocked else "allow"
        want = "BLOCK" if expect_block else "allow"
        print(f"[{tag}] {verb:5} (want {want:5})  {command}")
        if ok:
            passed += 1
        else:
            failed += 1
            if proc.stderr:
                print("       stderr:", proc.stderr.strip())
    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
