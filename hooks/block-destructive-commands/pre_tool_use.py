#!/usr/bin/env python3
"""
pre_tool_use.py — Claude Code pre-tool-use hook that blocks destructive bash commands.

Bounty: claude-builders-bounty #3 ($100, powered by Opire)
Acceptance criteria:
  - [x] Follows Claude Code hooks format (~/.claude/hooks/)
  - [x] Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
  - [x] Logs every blocked attempt to ~/.claude/hooks/blocked.log (timestamp, command, project path)
  - [x] Shows Claude a clear message explaining why the command was blocked
  - [x] Does not interfere with normal bash commands
  - [x] README with installation in 2 commands or fewer

Usage:
  Place this file at ~/.claude/hooks/pre_tool_use.py
  Register in settings.json:
    "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" } ] } ] }

Input:  JSON on stdin: {"tool_name": "Bash", "tool_input": {"command": "..."}}
Output: JSON on stdout: {"permissionDecision": "block"|"allow", "reason": "..."}
"""

import json
import os
import re
import sys
import datetime

# ── Patterns that are ALWAYS blocked ────────────────────────────────────────
ALWAYS_BLOCK = [
    # SQL destructive statements
    re.compile(r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', re.IGNORECASE),
    re.compile(r'\bTRUNCATE\s+', re.IGNORECASE),
    # Force push
    re.compile(r'\bgit\s+push\b.*(--force|-f)\b', re.IGNORECASE),
    # Raw disk / partition
    re.compile(r'\bmkfs\b', re.IGNORECASE),
    re.compile(r'\bdd\s+if=.*\bof=/dev/', re.IGNORECASE),
    # Privilege escalation bombs
    re.compile(r'\bchmod\s+(-R\s+)?777\s+/\s*$', re.IGNORECASE),
    re.compile(r'\bchown\s+-R\s+.*\s+/\s*$', re.IGNORECASE),
]

# ── DELETE FROM requires a WHERE clause (or LIMIT) ─────────────────────────
DELETE_WITHOUT_WHERE = re.compile(
    r'\bDELETE\s+FROM\b', re.IGNORECASE
)

RM_RE = re.compile(r'\brm\b', re.IGNORECASE)

def _check_rm(cmd: str) -> str | None:
    """Special handling for `rm`: block when recursive AND force flags are
    present, whether combined (-rf), split (-r -f), or long form
    (--recursive --force)."""
    if not RM_RE.search(cmd):
        return None
    idx = RM_RE.search(cmd).end()
    rest = cmd[idx:]
    flags = re.findall(r'--?[a-zA-Z-]+', rest)
    flagstr = ''.join(flags).lower()
    has_r = ('r' in flagstr) or ('recursive' in flagstr)
    has_f = ('f' in flagstr) or ('force' in flagstr)
    if has_r and has_f:
        return f"rm with recursive+force flags ({flagstr})"
    return None

def _strip_quoted_parts(cmd: str) -> str:
    """Remove single/double-quoted strings so we don't false-positive on
    e.g. echo 'DROP TABLE x' or grepping for patterns."""
    cmd = re.sub(r"'[^']*'", "''", cmd)
    cmd = re.sub(r'"[^"]*"', '""', cmd)
    return cmd

def _strip_comments(cmd: str) -> str:
    """Remove comments (naive split on #; adequate since the quote-stripped
    scan target is what we match against)."""
    return cmd.split('#')[0]

# ── Commands that only READ/output text — safe to scan the quote-stripped
# form only (their arguments are never executed, so quoted "DROP TABLE"
# inside them is just text). Other commands may execute their args
# (mysql -e "...", psql -c "..."), so for those we must also scan the raw
# command to catch quoted SQL.
READONLY_TOOLS = (
    'echo', 'printf', 'grep', 'rg', 'cat', 'head', 'tail',
    'wc', 'cut', 'sort', 'uniq', 'less', 'more', 'diff', 'comm',
)

def should_block(command: str) -> tuple[bool, str]:
    """Return (block, reason)."""
    if not command or not command.strip():
        return False, ""

    first = command.lstrip().split()[0].split('/')[-1] if command.split() else ""
    readonly = first in READONLY_TOOLS

    # Scan target selection:
    #  - readonly commands: only the quote-stripped form (their args are inert
    #    text; this kills `echo 'rm -rf /'` and `grep -r "DROP TABLE" .`)
    #  - everything else: also scan the RAW command so real executions like
    #    `mysql -e "DELETE FROM users"` are caught even though quoted.
    stripped = _strip_quoted_parts(_strip_comments(command))
    targets = [stripped] if readonly else [stripped, _strip_comments(command)]

    for target in targets:
        # rm recursive+force (combined or split flags)
        rm_reason = _check_rm(target)
        if rm_reason:
            return True, rm_reason

        for pat in ALWAYS_BLOCK:
            m = pat.search(target)
            if m:
                return True, f"Blocked pattern '{pat.pattern}' matched: {m.group(0).strip()[:80]}"

        # DELETE FROM without WHERE / LIMIT
        if DELETE_WITHOUT_WHERE.search(target):
            if re.search(r'\bWHERE\b|\bLIMIT\s+\d+', target, re.IGNORECASE):
                pass  # sane delete
            else:
                return True, "DELETE FROM without a WHERE/LIMIT clause"

    return False, ""

def log_blocked(command: str, reason: str) -> None:
    """Append a blocked event to ~/.claude/hooks/blocked.log"""
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    try:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        cwd = os.getcwd()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] project={cwd} command={command!r} reason={reason}\n")
    except Exception:
        # Never crash the tool call because logging failed.
        pass

def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # If we can't parse input, allow — never block Claude on our own bugs.
        print(json.dumps({"permissionDecision": "allow"}))
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    # Only guard Bash. Other tools (Read, Edit, etc.) pass through.
    if tool_name != "Bash":
        print(json.dumps({"permissionDecision": "allow"}))
        return

    command = tool_input.get("command", "")
    block, reason = should_block(command)
    if block:
        log_blocked(command, reason)
        print(json.dumps({
            "permissionDecision": "block",
            "reason": (
                f"[HookGuard] Command blocked because it looks destructive: {reason}. "
                "If this was intentional, refactor the command to be safer "
                "(e.g. use a targeted path, add WHERE/LIMIT, avoid --force)."
            ),
        }))
    else:
        print(json.dumps({"permissionDecision": "allow"}))

if __name__ == "__main__":
    main()
