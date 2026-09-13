#!/usr/bin/env python3
"""Tests for the destructive-command PreToolUse hook.

Runs the hook as a subprocess with a throwaway HOME, feeding it real
PreToolUse payloads on stdin, and checks the decision, the log file, and the
settings.json install path.

    python3 test_hook.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block_destructive_bash.py"
PROJECT_PATH = "/home/dev/demo-project"

# (command, expected rule or None when the command must be allowed)
CASES = [
    # Everyday commands must pass straight through.
    ("ls", None),
    ("ls -la /tmp", None),
    ("npm test", None),
    ("git status", None),
    ("git push", None),
    ("git push origin main", None),
    ("git push --force-with-lease origin main", None),
    ("rm file.txt", None),
    ("rm -r build", None),
    ("rm -f stale.lock", None),
    ('psql -c "DELETE FROM users WHERE id=1"', None),
    ('psql -c "SELECT * FROM users"', None),
    ("npm run truncate-logs", None),
    ("python3 truncate.py --dry-run", None),
    # Destructive text quoted inside a read-only command is not an action.
    ('echo "rm -rf /"', None),
    ('grep -rn "DROP TABLE" migrations/', None),
    ('echo "DROP TABLE users" > migration.sql', None),

    # rm -rf, including flag spellings and wrappers.
    ("rm -rf /tmp/x", "rm-rf"),
    ("rm -fr /tmp/x", "rm-rf"),
    ("rm -r -f /tmp/x", "rm-rf"),
    ("rm -Rf /tmp/x", "rm-rf"),
    ("rm --recursive --force /tmp/x", "rm-rf"),
    ("sudo rm -rf /", "rm-rf"),
    ("cd /tmp && rm -rf build", "rm-rf"),
    ("find /tmp -name '*.log' | xargs rm -rf", "rm-rf"),
    ('bash -c "rm -rf /tmp/x"', "rm-rf"),

    # Force pushes.
    ("git push --force", "git-force-push"),
    ("git push -f origin main", "git-force-push"),
    ("git push origin main --force", "git-force-push"),
    ("git push origin +main:main", "git-force-push"),

    # SQL.
    ('psql -c "DROP TABLE users"', "sql-drop-table"),
    ('psql -c "drop table users"', "sql-drop-table"),
    ('mysql -e "TRUNCATE logs"', "sql-truncate"),
    ("truncate -s 0 important.log", "sql-truncate"),
    ('psql -c "DELETE FROM users"', "sql-delete-without-where"),
    ('psql -c "delete from users;"', "sql-delete-without-where"),
    ('psql -c "DELETE FROM a WHERE id=1; DELETE FROM b"', "sql-delete-without-where"),

    # Commands the tokenizer rejects (unbalanced quote) fall back to patterns.
    ('rm -rf "/tmp/x', "rm-rf"),
    ('git push --force "oops', "git-force-push"),
    ('echo "hello', None),
]


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = []

    def check(self, name, ok, detail=""):
        if ok:
            self.passed += 1
            print("  pass  {}".format(name))
        else:
            self.failed.append(name)
            print("  FAIL  {}{}".format(name, ": " + detail if detail else ""))


def run_hook(home, payload):
    env = dict(os.environ, HOME=str(home))
    env.pop("CLAUDE_PROJECT_DIR", None)
    process = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return process


def bash_payload(command):
    return {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": PROJECT_PATH,
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_use_id": "toolu_test",
    }


def decision_of(process):
    """Return the permissionDecision from a hook run, or None when silent."""
    if process.returncode != 0:
        raise AssertionError("hook exited {}: {}".format(process.returncode, process.stderr))
    if not process.stdout.strip():
        return None, ""
    payload = json.loads(process.stdout)
    specific = payload["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse", specific
    return specific["permissionDecision"], specific.get("permissionDecisionReason", "")


def test_decisions(home, results):
    print("\nallow / block decisions")
    for command, expected_rule in CASES:
        process = run_hook(home, bash_payload(command))
        try:
            decision, reason = decision_of(process)
        except (AssertionError, json.JSONDecodeError, KeyError) as error:
            results.check(command, False, str(error))
            continue
        if expected_rule is None:
            results.check(command, decision is None, "expected allow, got {}".format(decision))
        else:
            ok = decision == "deny" and expected_rule in reason
            results.check(
                command, ok, "expected deny/{}, got {}".format(expected_rule, decision or "allow")
            )


def test_blocked_log(home, results):
    print("\nblocked.log")
    log = home / ".claude" / "hooks" / "blocked.log"
    results.check("log written to ~/.claude/hooks/blocked.log", log.exists())
    if not log.exists():
        return

    entries = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
    expected_blocks = sum(1 for _, rule in CASES if rule is not None)
    results.check(
        "one entry per blocked attempt",
        len(entries) == expected_blocks,
        "expected {}, found {}".format(expected_blocks, len(entries)),
    )
    results.check(
        "entries carry timestamp, command, project path",
        all(
            entry.get("timestamp")
            and entry.get("command")
            and entry.get("project_path") == PROJECT_PATH
            for entry in entries
        ),
    )
    results.check(
        "timestamps are ISO-8601 UTC",
        all(entry["timestamp"].endswith("Z") and "T" in entry["timestamp"] for entry in entries),
    )
    results.check(
        "rules recorded",
        {entry["rule"] for entry in entries}
        == {rule for _, rule in CASES if rule is not None},
    )


def test_ignores_other_input(home, results):
    print("\nnon-Bash and malformed input")
    read_payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/rm -rf.txt"},
    }
    decision, _ = decision_of(run_hook(home, read_payload))
    results.check("non-Bash tool ignored", decision is None)

    env = dict(os.environ, HOME=str(home))
    process = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, env=env
    )
    results.check(
        "malformed stdin allows the call",
        process.returncode == 0 and not process.stdout.strip(),
        process.stdout + process.stderr,
    )

    empty = decision_of(run_hook(home, bash_payload("")))[0]
    results.check("empty command allowed", empty is None)


def test_install(results):
    print("\ninstall / uninstall")
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        env = dict(os.environ, HOME=str(home))
        settings = home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        existing = {
            "hooks": {
                "PostToolUse": [
                    {"matcher": "Edit", "hooks": [{"type": "command", "command": "prettier"}]}
                ]
            }
        }
        settings.write_text(json.dumps(existing, indent=2))

        first = subprocess.run(
            [sys.executable, str(HOOK), "--install"], capture_output=True, text=True, env=env
        )
        results.check("--install succeeds", first.returncode == 0, first.stderr)

        data = json.loads(settings.read_text())
        results.check(
            "existing hooks preserved", data["hooks"].get("PostToolUse") == existing["hooks"]["PostToolUse"]
        )
        groups = data["hooks"].get("PreToolUse", [])
        registered = [
            hook["command"]
            for group in groups
            for hook in group.get("hooks", [])
            if "block_destructive_bash.py" in hook.get("command", "")
        ]
        results.check("PreToolUse entry added", len(registered) == 1, str(groups))
        results.check(
            "matcher targets Bash", any(group.get("matcher") == "Bash" for group in groups)
        )

        second = subprocess.run(
            [sys.executable, str(HOOK), "--install"], capture_output=True, text=True, env=env
        )
        reinstalled = json.loads(settings.read_text())
        results.check(
            "--install is idempotent",
            second.returncode == 0 and reinstalled == data,
            second.stdout + second.stderr,
        )

        removal = subprocess.run(
            [sys.executable, str(HOOK), "--uninstall"], capture_output=True, text=True, env=env
        )
        after = json.loads(settings.read_text())
        results.check(
            "--uninstall removes only our entry",
            removal.returncode == 0 and after == existing,
            json.dumps(after),
        )


def main():
    results = Results()
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        test_decisions(home, results)
        test_blocked_log(home, results)
        test_ignores_other_input(home, results)
    test_install(results)

    total = results.passed + len(results.failed)
    print("\n{}/{} checks passed".format(results.passed, total))
    if results.failed:
        print("failed: {}".format(", ".join(results.failed)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
