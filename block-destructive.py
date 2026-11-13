#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Intercepts Bash tool calls before they run and denies commands that can
irreversibly destroy data, while letting normal commands through.

Blocked patterns:
  - rm -rf (recursive + force removal)
  - DROP TABLE (SQL)
  - git push --force / git push -f (not --force-with-lease, which is safe)
  - TRUNCATE (SQL)
  - DELETE FROM without a WHERE clause (SQL)

Every blocked attempt is logged to ~/.claude/hooks/blocked.log with a
timestamp, the attempted command, and the project path, and a clear
message is returned to Claude explaining why it was blocked.

Hook protocol (Claude Code):
  - Reads a JSON event on stdin. For PreToolUse / Bash the command lives
    in tool_input.command and the working directory in cwd.
  - To deny, prints {"hookSpecificOutput": {..., "permissionDecision":
    "deny", "permissionDecisionReason": "..."}} and exits 0.
  - To allow, exits 0 silently.
  - Also accepts a raw command on stdin or as argv[1] (handy for tests).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")


def _rm_is_destructive(command):
    """True when a real `rm` invocation uses recursive + force together.

    Handles combined flags (-rf / -fr), separate flags (-r -f), long flags
    (--recursive --force), and wrappers such as `sudo`. Only the first word
    of each shell segment counts as the command, so `echo "rm -rf"` (rm
    inside a quoted string) is NOT blocked, while `sudo rm -rf /` is.
    """
    segments = re.split(r"[;&|]+|\n", command)
    for seg in segments:
        s = seg.strip()
        # Strip leading wrappers (sudo / command / env) with their flags
        # and VAR=value assignments, e.g. `sudo -u alice rm -rf`.
        while True:
            m = re.match(r"^(sudo|command|env)\b\s*", s)
            if not m:
                break
            s = s[m.end():]
            while True:
                m2 = re.match(r"^(?:-[a-zA-Z]+\s+|\w+=\\S+\s+)", s)
                if not m2:
                    break
                tok = m2.group(0).strip()
                s = s[m2.end():]
                # -u takes a username argument.
                if tok == "-u":
                    m3 = re.match(r"^\S+\s*", s)
                    if m3:
                        s = s[m3.end():]
        m = re.match(r"^rm\b\s*(.*)$", s, re.DOTALL)
        if not m:
            continue
        # Collect flag tokens until the first non-flag token.
        flags = []
        for tok in m.group(1).split():
            if tok.startswith("-") and tok != "-":
                flags.append(tok)
            else:
                break
        has_r = has_f = False
        for fl in flags:
            if fl.startswith("--"):
                if fl == "--recursive":
                    has_r = True
                elif fl == "--force":
                    has_f = True
            else:
                if "r" in fl[1:]:
                    has_r = True
                if "f" in fl[1:]:
                    has_f = True
        if has_r and has_f:
            return True
    return False


# (pattern, human-readable reason)
BLOCKED = [
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE permanently deletes a database table and all its data. "
        "Use a migration / backup first, or confirm the exact table.",
    ),
    (
        # --force / -f as a standalone flag, but NOT --force-with-lease
        # (the safe variant that refuses to overwrite others' work).
        re.compile(
            r"\bgit\s+push\b[^;&|]*?(?:--force(?![-\w])|(?:^|\s)-f(?:\s|$))",
            re.IGNORECASE,
        ),
        "git push --force / -f can permanently overwrite remote history. "
        "Use --force-with-lease instead, which refuses when someone else "
        "pushed first.",
    ),
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE permanently deletes all rows of a table. Confirm the "
        "exact table and take a backup first.",
    ),
]


def _delete_without_where(command):
    """True when a DELETE FROM has no WHERE in the same statement."""
    for m in re.finditer(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        tail = command[m.end():]
        # Only the current statement counts (up to the next semicolon).
        tail = tail.split(";", 1)[0]
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            return True
    return False


def check(command):
    """Return the block reason for a command, or None when it is allowed."""
    if not command or not command.strip():
        return None
    if _rm_is_destructive(command):
        return (
            "rm with recursive + force flags (-rf) can irreversibly delete "
            "whole directory trees. Remove the -r/-f flags, target a "
            "specific path, or confirm the exact scope first."
        )
    for pattern, reason in BLOCKED:
        if pattern.search(command):
            return reason
    if _delete_without_where(command):
        return (
            "DELETE FROM without a WHERE clause would delete every row of "
            "the table. Add a WHERE clause that limits the rows, or confirm "
            "the exact scope first."
        )
    return None


def log_blocked(command, cwd):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        line = "%s | cwd=%s | command=%s\n" % (ts, cwd or "", command)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        # Logging must never break the hook itself.
        pass


def read_command():
    """Extract (command, cwd) from the hook JSON on stdin.

    Falls back to a raw command on stdin or argv[1] so the hook can be
    tested directly:  echo 'rm -rf /' | ./block-destructive.sh
    """
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if raw.strip():
        try:
            event = json.loads(raw)
            if isinstance(event, dict):
                tool_input = event.get("tool_input") or {}
                cmd = tool_input.get("command")
                if isinstance(cmd, str):
                    return cmd, event.get("cwd") or os.getcwd()
            # Not JSON: treat the whole stdin as the command.
            return raw.strip(), os.getcwd()
        except json.JSONDecodeError:
            return raw.strip(), os.getcwd()
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]), os.getcwd()
    return "", os.getcwd()


def main():
    command, cwd = read_command()
    reason = check(command)
    if reason is None:
        return 0
    log_blocked(command, cwd)
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive command: %s\nCommand: %s" % (reason, command)
            ),
        }
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
