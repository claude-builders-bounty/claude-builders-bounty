#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads a PreToolUse JSON payload on stdin. Exits 0 when the command is
safe. When the command matches a destructive pattern, it appends an
entry to ~/.claude/hooks/blocked.log and exits 2 with a message on
stderr, which Claude Code feeds back to the model as the block reason.

Install and register in 2 commands (see README.md).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# rm flags that combine recursive and force in one or more flag args:
# -rf, -fr, -rRf, -f -r, --recursive --force, --force --recursive
RM_FLAG = re.compile(r"-[a-zA-Z]*(?:r[a-zA-Z]*f|f[a-zA-Z]*r)[a-zA-Z]*")
RM_LONG = re.compile(r"--recursive|--force", re.I)

RULES = [
    (re.compile(r"\bgit\s+push\b[^|;&>]*(?:--force(?:-with-lease|-if-includes)?\b|-\w*f\w*)", re.I),
     "git push --force rewrites remote history"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I),
     "DROP TABLE destroys a database table"),
    (re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.I),
     "TRUNCATE wipes all rows from a table"),
]

DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE_CLAUSE = re.compile(r"\bWHERE\b", re.I)
RM_CMD = re.compile(r"\brm\b(.*)", re.S)


def rm_is_destructive(seg):
    m = RM_CMD.search(seg)
    if not m:
        return False
    args = m.group(1)
    short_flags = re.findall(r"-[a-zA-Z]+", args)
    combined = "".join(f[1:] for f in short_flags)
    if "r" in combined.lower() and "f" in combined.lower():
        return True
    longs = set(x.lower() for x in RM_LONG.findall(args))
    return "--recursive" in longs and "--force" in longs


def check(command):
    for seg in re.split(r"[;|&\n]|&&|\|\|", command):
        seg = seg.strip()
        if not seg:
            continue
        for rx, reason in RULES:
            if rx.search(seg):
                return reason
        if rm_is_destructive(seg):
            return "rm with recursive+force flags (rm -rf and variants) can delete entire trees"
        if DELETE_FROM.search(seg) and not WHERE_CLAUSE.search(seg):
            return "DELETE FROM without a WHERE clause wipes every row"
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open: never break the session on bad input

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = check(command)
    if reason is None:
        sys.exit(0)

    project = payload.get("cwd") or os.getcwd()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"{ts}\t{project}\t{command}\n")
    except OSError:
        pass

    sys.stderr.write(
        f"Blocked by pre-tool-use safety hook: {reason}.\n"
        f"Command: {command}\n"
        f"Logged to {LOG_PATH}. If this is truly intended, ask the user "
        "to run it manually or adjust the hook rules."
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
