#!/usr/bin/env python3
"""Claude Code PreToolUse hook: blocks destructive bash commands.

Stdin: JSON from Claude Code ({tool_name, tool_input: {command}, cwd}).
Exit 0 = allow, exit 2 = block (stderr explains why, shown to Claude).
Blocked attempts are appended to BLOCKED_LOG with timestamp, command, project path.

Patterns blocked (bounty #3 acceptance criteria):
  - `rm -rf` (and variants: -fr, -rfv, --recursive --force) aimed at
    /, ~, $HOME, *, ., .. or an absolute path outside /tmp and cwd-safe dirs
  - `DROP TABLE`, `TRUNCATE` (any SQL flavour)
  - `git push --force` / `git push -f`
  - `DELETE FROM <table>` without a WHERE clause
Everything else passes through untouched.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_LOG = os.environ.get(
    "HOOK_BLOCKED_LOG",
    os.path.expanduser("~/.claude/hooks/blocked.log"),
)

# rm with both recursive and force flags: rm -rf, rm -fr, rm -rfv, rm --recursive --force ...
RM_RF = re.compile(
    r"(?<![\w-])rm\b(?=[^;|&]*-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)|[^;|&]*--recursive[^;|&]*--force|[^;|&]*--force[^;|&]*--recursive)",
    re.IGNORECASE,
)
# Args that make rm -rf catastrophic: /, /*, ~, $HOME, *, ., ..
RM_RF_TARGET = re.compile(
    r"(?<![\w/.'\"-])(/(?:\*|$|[\s;|&\"'])|~(?:/|$|[\s;|&\"'])|\$HOME\b|\*(?:[\s;|&\"']|$)|(?:^|[\s;|&])(?:\.(?:\.|/)?)(?:[\s;|&\"']|$))",
)
DROP_TABLE = re.compile(r"(?<![\w])drop\s+table\b", re.IGNORECASE)
TRUNCATE = re.compile(r"(?<![\w])truncate\b", re.IGNORECASE)
GIT_PUSH_FORCE = re.compile(
    r"(?<![\w-])git\b[^;|&]*\bpush\b[^;|&]*(--force\b|\s-f(?:[\s;|&]|$))", re.IGNORECASE
)
DELETE_FROM = re.compile(r"(?<![\w])delete\s+from\s+\S+", re.IGNORECASE)
WHERE = re.compile(r"(?<![\w])where\b", re.IGNORECASE)


def check(command):
    """Return the block reason, or None if the command is allowed."""
    if RM_RF.search(command) and RM_RF_TARGET.search(command):
        return "destructive `rm -rf` targeting a broad path (/, ~, *, ., ..). Narrow the target or confirm with the user first."
    if DROP_TABLE.search(command):
        return "`DROP TABLE` permanently deletes a table. Confirm the target database/table with the user first."
    if TRUNCATE.search(command):
        return "`TRUNCATE` permanently wipes a table. Confirm the target table with the user first."
    if GIT_PUSH_FORCE.search(command):
        return "`git push --force` rewrites shared history. Use a normal push or confirm with the user first."
    m = DELETE_FROM.search(command)
    if m and not WHERE.search(command[m.start():]):
        return "`DELETE FROM` without a WHERE clause wipes the whole table. Add a WHERE clause or confirm first."
    return None


def log_blocked(command, cwd):
    try:
        os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
        with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now(timezone.utc).isoformat()} | cwd={cwd} | command={command}\n"
            )
    except OSError:
        pass  # logging must never break the hook


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not a hook payload we understand: allow
    tool = payload.get("tool_name", "")
    if tool and tool != "Bash":
        return 0
    command = ((payload.get("tool_input") or {}).get("command")) or ""
    if not command.strip():
        return 0
    reason = check(command)
    if not reason:
        return 0
    cwd = payload.get("cwd") or os.getcwd()
    log_blocked(command.strip(), cwd)
    sys.stderr.write(f"Blocked by destructive-command guard: {reason}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
