#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive Bash commands.

Reads the hook JSON from stdin. On a match, logs to
~/.claude/hooks/blocked.log, prints the reason to stderr and exits 2
(Claude Code feeds stderr back to Claude and blocks the call).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# rm with both recursive and force flags (-rf, -fr, -r -f, --recursive --force)
RM_RE = re.compile(r"(?:^|[;&|(`]|\s)rm\s+((?:-\S+\s+|--\s+)*)", re.I)
GIT_FORCE_RE = re.compile(
    r"\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*(?:\s--force(?!-with-lease)\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)")
DROP_RE = re.compile(r"\bDROP\s+TABLE\b", re.I)
TRUNC_RE = re.compile(r"\bTRUNCATE\b(?:\s+TABLE)?\s+\S+", re.I)
DELETE_RE = re.compile(r"\bDELETE\s+FROM\b[^;]*(?:;|$)", re.I)


def _rm_destructive(cmd):
    for m in RM_RE.finditer(cmd):
        flags = [t for t in m.group(1).split() if t.startswith("-") and t != "--"]
        short = "".join(f[1:] for f in flags if not f.startswith("--"))
        longs = [f for f in flags if f.startswith("--")]
        rec = "r" in short.lower() or "--recursive" in longs
        force = "f" in short or "--force" in longs
        if rec and force:
            return True
    return False


def check(cmd):
    """Return a reason string if cmd must be blocked, else None."""
    if _rm_destructive(cmd):
        return "`rm -rf` (recursive forced delete) can irreversibly destroy files."
    if GIT_FORCE_RE.search(cmd):
        return "`git push --force` can overwrite remote history."
    if DROP_RE.search(cmd):
        return "`DROP TABLE` permanently deletes a database table."
    if TRUNC_RE.search(cmd):
        return "`TRUNCATE` permanently deletes all rows of a table."
    for m in DELETE_RE.finditer(cmd):
        if not re.search(r"\bWHERE\b", m.group(0), re.I):
            return "`DELETE FROM` without a WHERE clause deletes every row."
    return None


def log_block(cmd, project, reason):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ts}\tproject={project}\tcommand={cmd!r}\treason={reason}\n")
    except OSError as e:
        print(f"block-destructive: could not write log: {e}", file=sys.stderr)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: do not interfere
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str):
        return 0
    reason = check(cmd)
    if reason is None:
        return 0
    project = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_block(cmd, project, reason)
    print(f"BLOCKED by block-destructive hook: {reason}\n"
          f"Command: {cmd}\n"
          "Ask the user for explicit confirmation or use a safer alternative "
          "(e.g. scoped delete, `--force-with-lease`, a DELETE with WHERE).",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
