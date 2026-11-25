#!/usr/bin/env python3
"""Tests for block-destructive-bash.py.

Feeds sample PreToolUse hook payloads to the hook and asserts the right
exit code (2 = blocked, 0 = allowed), the right block message, and the
right log lines.

Run:  python3 test_hook.py

The tests run the hook with HOME pointed at a fresh temp directory, so the
real ~/.claude/hooks/blocked.log is never touched.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HOOK = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "block-destructive-bash.py"
)
FAKE_CWD = "/tmp/fake-project"

# (command, expected reason substring in the block message)
BLOCKED = [
    ("rm -rf /tmp/old-project", "rm -rf"),
    ('rm -rf "$HOME/cache"', "rm -rf"),
    ("sudo rm -rf /var/tmp/x", "rm -rf"),
    ("rm -fr node_modules", "rm -rf"),
    ("rm -r -f build", "rm -rf"),
    ("rm --recursive --force /tmp/x", "rm -rf"),
    ("rm -rf node_modules && npm install", "rm -rf"),
    ("ls && rm -rf /tmp/x", "rm -rf"),
    ("find . -name '*.log' -exec rm -rf {} \\;", "rm -rf"),
    ("rm -rf /tmp/x; DROP TABLE t;", "rm -rf"),  # two patterns at once
    ("DROP TABLE users;", "DROP TABLE"),
    ('psql -c "DROP TABLE IF EXISTS sessions"', "DROP TABLE"),
    ("git push --force origin main", "git push --force"),
    ("git push -f", "git push --force"),
    ("git push origin main --force", "git push --force"),
    ("TRUNCATE TABLE sessions;", "TRUNCATE"),
    ('mysql -e "TRUNCATE TABLE logs"', "TRUNCATE"),
    ("DELETE FROM users;", "DELETE FROM"),
    ('sqlite3 app.db "DELETE FROM tokens"', "DELETE FROM"),
    # SQL payloads are checked in their quoted form: `psql -c "DROP TABLE ..."`
    # is a real destructive command, so `echo "DROP TABLE ..."` is blocked too.
    ('echo "DROP TABLE users"', "DROP TABLE"),
]

ALLOWED = [
    "ls -la",
    "git status",
    "npm install",
    "mkdir -p build/output",
    "git push origin main",
    "git push --force-with-lease origin main",  # the safe force variant
    "DELETE FROM users WHERE id = 42;",
    "psql -c \"DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days'\"",
    'echo "rm -rf /"',          # rm -rf inside double quotes
    "echo 'rm -rf /tmp'",       # rm -rf inside single quotes
    "# rm -rf /",               # whole-line comment
    "echo hello # rm -rf /",    # trailing comment
    "rm -r /tmp/old",           # recursive but not forced
    "rm -f file.txt",           # forced but not recursive
    'grep -r "rm -rf" README.md',
    "truncate -s 0 app.log",    # the `truncate` file utility, not SQL
    "echo git push --force",    # git is an argument to echo, not a command
    "git commit -m 'force push'",
    'touch "rm -rf"',           # pattern is a quoted filename
    "cat file.txt | grep DROP",
]


def run_hook(command, home, tool_name="Bash"):
    """Run the hook once with a PreToolUse payload. Returns (rc, stderr)."""
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/test-transcript.jsonl",
        "cwd": FAKE_CWD,
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
    }
    env = dict(os.environ)
    env["HOME"] = home
    env.pop("BASH_GUARD_LOG", None)
    result = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stderr


def log_lines(home):
    path = os.path.join(home, ".claude", "hooks", "blocked.log")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def main():
    failures = []
    passed = 0
    with tempfile.TemporaryDirectory() as home:
        # --- Blocked commands: exit 2, reason in message, one log line. ---
        for command, reason in BLOCKED:
            before = len(log_lines(home))
            rc, stderr = run_hook(command, home)
            after = log_lines(home)
            problems = []
            if rc != 2:
                problems.append(f"exit code {rc}, expected 2")
            if reason.lower() not in stderr.lower():
                problems.append(f"stderr missing {reason!r}: {stderr!r}")
            if len(after) != before + 1:
                problems.append(
                    f"log gained {len(after) - before} lines, expected 1"
                )
            elif command not in after[-1] or FAKE_CWD not in after[-1]:
                problems.append(f"log line missing command/cwd: {after[-1]!r}")
            elif not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", after[-1]):
                problems.append(f"log line missing timestamp: {after[-1]!r}")
            if problems:
                failures.append((f"BLOCKED {command!r}", problems))
            else:
                passed += 1

        # --- Allowed commands: exit 0, silent, no new log line. ---
        for command in ALLOWED:
            before = len(log_lines(home))
            rc, stderr = run_hook(command, home)
            after = len(log_lines(home))
            problems = []
            if rc != 0:
                problems.append(f"exit code {rc}, expected 0")
            if stderr.strip():
                problems.append(f"unexpected stderr: {stderr!r}")
            if after != before:
                problems.append("log file grew for an allowed command")
            if problems:
                failures.append((f"ALLOWED {command!r}", problems))
            else:
                passed += 1

        # --- Non-Bash tool calls are ignored. ---
        rc, _ = run_hook("rm -rf /", home, tool_name="Read")
        if rc != 0:
            failures.append(("non-Bash tool", [f"exit code {rc}, expected 0"]))
        else:
            passed += 1

        # --- Malformed JSON input fails open (exit 0, no crash). ---
        env = dict(os.environ)
        env["HOME"] = home
        result = subprocess.run(
            [sys.executable, HOOK],
            input="this is not json",
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            failures.append(
                ("malformed JSON", [f"exit code {result.returncode}, expected 0"])
            )
        else:
            passed += 1

        # --- Empty command is allowed. ---
        rc, _ = run_hook("", home)
        if rc != 0:
            failures.append(("empty command", [f"exit code {rc}, expected 0"]))
        else:
            passed += 1

    total = passed + len(failures)
    print(f"{passed}/{total} tests passed")
    for name, problems in failures:
        print(f"FAIL: {name}")
        for problem in problems:
            print(f"      - {problem}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
