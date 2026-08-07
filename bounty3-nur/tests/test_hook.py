#!/usr/bin/env python3
"""Tests for block_destructive_commands.py — run with:
   python3 tests/test_hook.py
No external dependencies; pure stdlib subprocess + json.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(os.path.dirname(HERE), "block_destructive_commands.py")

PASS = 0
FAIL = 0


def run_hook(command, tool_name="Bash", cwd="/tmp/project", env_log=None):
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command} if command is not None else {},
        "cwd": cwd,
    })
    env = os.environ.copy()
    if env_log:
        env["HOME"] = env_log
    result = subprocess.run(
        [sys.executable, HOOK],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok  - {label}")
    else:
        FAIL += 1
        print(f" FAIL - {label}")


def main():
    tmp_home = tempfile.mkdtemp()

    # 1. rm -rf must be blocked
    r = run_hook("rm -rf /some/path", env_log=tmp_home)
    check("rm -rf is blocked (exit 2)", r.returncode == 2)
    check("rm -rf reason mentions recursive", "recursive" in r.stderr.lower())

    # 2. rm -fr (flags reversed) must also be blocked
    r = run_hook("rm -fr build/", env_log=tmp_home)
    check("rm -fr is blocked", r.returncode == 2)

    # 3. plain rm of a single file must be allowed
    r = run_hook("rm build/output.log", env_log=tmp_home)
    check("rm single file is allowed", r.returncode == 0)

    # 4. forced git push must be blocked
    r = run_hook("git push origin main --force", env_log=tmp_home)
    check("git push --force is blocked", r.returncode == 2)

    r = run_hook("git push -f origin main", env_log=tmp_home)
    check("git push -f is blocked", r.returncode == 2)

    # 5. normal git push must be allowed
    r = run_hook("git push origin main", env_log=tmp_home)
    check("normal git push is allowed", r.returncode == 0)

    # 6. DROP TABLE blocked
    r = run_hook("psql -c 'DROP TABLE users;'", env_log=tmp_home)
    check("DROP TABLE is blocked", r.returncode == 2)

    # 7. TRUNCATE blocked
    r = run_hook("mysql -e 'TRUNCATE orders;'", env_log=tmp_home)
    check("TRUNCATE is blocked", r.returncode == 2)

    # 8. DELETE FROM without WHERE blocked
    r = run_hook("sqlite3 db.sqlite \"DELETE FROM sessions;\"", env_log=tmp_home)
    check("DELETE FROM without WHERE is blocked", r.returncode == 2)

    # 9. DELETE FROM with WHERE allowed
    r = run_hook("sqlite3 db.sqlite \"DELETE FROM sessions WHERE id=1;\"", env_log=tmp_home)
    check("DELETE FROM with WHERE is allowed", r.returncode == 0)

    # 10. non-Bash tool calls are ignored
    r = run_hook("rm -rf /", tool_name="Read", env_log=tmp_home)
    check("non-Bash tool is always allowed", r.returncode == 0)

    # 11. empty/missing command doesn't crash
    r = run_hook(None, env_log=tmp_home)
    check("missing command does not crash", r.returncode == 0)

    # 12. malformed JSON on stdin fails open, not closed
    result = subprocess.run(
        [sys.executable, HOOK], input="not json {{{", capture_output=True, text=True,
    )
    check("malformed JSON fails open (exit 0)", result.returncode == 0)

    # 13. blocked attempts are logged to blocked.log under HOME
    log_path = os.path.join(tmp_home, ".claude", "hooks", "blocked.log")
    check("blocked.log was created", os.path.exists(log_path))
    if os.path.exists(log_path):
        with open(log_path) as f:
            lines = [json.loads(line) for line in f if line.strip()]
        check("blocked.log has structured JSONL entries", len(lines) >= 1)
        check("log entry has timestamp/command/project_path/reason",
              all(k in lines[0] for k in ("timestamp", "attempted_command", "project_path", "reason")))

    # 14. stdout carries the modern hookSpecificOutput deny decision
    r = run_hook("rm -rf /tmp/x", env_log=tmp_home)
    try:
        out = json.loads(r.stdout.strip())
        check("stdout has hookSpecificOutput.permissionDecision=deny",
              out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny")
    except json.JSONDecodeError:
        check("stdout has hookSpecificOutput.permissionDecision=deny", False)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
