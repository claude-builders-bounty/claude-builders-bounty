#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — block destructive bash commands before they run.

Blocks:  rm -rf/-fr, DROP TABLE, TRUNCATE, DELETE FROM without WHERE, git push --force
Allows:  git push --force-with-lease (safer than --force), and anything tagged `guard:allow`
Logs:    every block to ~/.claude/hooks/blocked.log (timestamp, project path, command, reason)

Protocol: reads the hook JSON on stdin; exit 2 blocks (stderr is fed back to Claude),
exit 0 allows. Never raises — a parse error allows the command rather than wedging the shell.
"""

import datetime
import json
import os
import re
import sys

LOG_PATH = os.environ.get("CLAUDE_BLOCK_LOG", os.path.expanduser("~/.claude/hooks/blocked.log"))
BYPASS = "guard:allow"

SEG_SPLIT = re.compile(r"&&|\|\||[;|\n]")
RM_RE = re.compile(r"^rm\s+((?:-{1,2}[\w-]+\s+)*)")


def block_reason(command):
    """Return a human reason if the command should be blocked, else None."""
    if not command:
        return None
    if BYPASS in command:
        return None

    # split into sub-commands so `a && b` is checked piece by piece
    segments = [s.strip() for s in SEG_SPLIT.split(command) if s.strip()]

    for seg in segments:
        # rm with both recursive and force
        m = RM_RE.match(seg)
        if m:
            flags = m.group(1)
            short = "".join(re.findall(r"(?<!-)-([A-Za-z]+)", flags))
            long_ = re.findall(r"--[\w-]+", flags)
            if ("r" in short or "R" in short or "--recursive" in long_) and (
                "f" in short or "--force" in long_
            ):
                return "`rm` with recursive + force — deletes silently, no undo"

        # SQL: only when it is bare SQL or handed to a real SQL runner, so
        # `echo "DROP TABLE"` and commit messages don't trip it
        runner = re.match(
            r"^(?:sudo\s+)?(?:psql|mysql|mariadb|sqlite3?|duckdb|clickhouse-client|pgcli)\b", seg
        )
        sql = seg if runner else re.sub(r'"[^"]*"|\'[^\']*\'', " ", seg)
        if re.search(r"\bdrop\s+table\b", sql, re.I):
            return "`DROP TABLE` — drops the table and its data"
        if re.search(r"\btruncate\b", sql, re.I):
            return "`TRUNCATE` — empties the table with no WHERE guard"
        if re.search(r"\bdelete\s+from\b", sql, re.I) and not re.search(r"\bwhere\b", sql, re.I):
            return "`DELETE FROM` without a WHERE clause — hits every row"

        # git push --force (but --force-with-lease is safe)
        g = re.search(r"\bgit\s+push\b([^;&|\n]*)", seg)
        if g:
            args = g.group(1)
            if "--force-with-lease" in args:
                pass  # safer variant, allow
            elif "--force" in args or re.search(r"(^|\s)-f(\s|$)", args):
                return "`git push --force` — can clobber remote history (prefer --force-with-lease)"

    return None


def log_block(command, cwd, reason):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {cwd} | {reason} | $ {command}\n")
    except OSError:
        pass  # logging must never break the hook


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # unreadable input -> allow

    cmd = (payload.get("tool_input") or {}).get("command", "")
    cwd = payload.get("cwd") or os.getcwd()

    reason = block_reason(cmd)
    if not reason:
        sys.exit(0)

    log_block(cmd, cwd, reason)
    sys.stderr.write(
        "BLOCKED by destructive-bash guard\n"
        f"  reason : {reason}\n"
        f"  command: {cmd}\n"
        f"  project: {cwd}\n"
        f"  logged : {LOG_PATH}\n"
        f"To proceed anyway, re-issue the command with `{BYPASS}` somewhere in it "
        f"(e.g. append `# {BYPASS}`).\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
