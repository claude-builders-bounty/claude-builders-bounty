#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: blocks destructive bash commands.

Intercepts every Bash tool call. If the command matches a destructive pattern,
exits with code 2 (Claude Code's "block + show stderr to Claude" signal) and
writes a line to ~/.claude/hooks/blocked.log.

Install:
    mkdir -p ~/.claude/hooks
    curl -o ~/.claude/hooks/block-destructive.py https://raw.githubusercontent.com/phoenix7956/claude-review-bounty/main/.claude/hooks/block-destructive.py
    chmod +x ~/.claude/hooks/block-destructive.py
    # Then in ~/.claude/settings.json:
    # { "hooks": { "PreToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/block-destructive.py" }] }] } }
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# (pattern, regex_flags, human_readable_reason)
# Order matters: more specific patterns checked first.
DESTRUCTIVE_PATTERNS: list[tuple[str, int, str]] = [
    # ── Filesystem destruction ──────────────────────────────────────
    (r"\brm\s+(-[a-zA-Z]*[rRfF][a-zA-Z]*\s+)+", re.IGNORECASE, "Recursive or force rm with combined flags"),
    (r"\brm\s+(-{1,2}(?:recursive|r|force|f)[^\s]*\s+)+(?:/|\.|\*|~)", re.IGNORECASE, "rm -rf / (or root-level path)"),
    (r"\brm\s+-rf?\s+/\s*$", re.IGNORECASE, "rm -rf / (root filesystem)"),
    (r"\brmdir\s+/\s*$", re.IGNORECASE, "rmdir / (root directory)"),
    (r">\s*/dev/sd[a-z]", 0, "Overwrite raw block device"),
    (r"\bmkfs\.", 0, "Format filesystem"),
    (r"\bdd\s+.*of=/dev/", 0, "dd write to block device"),

    # ── Git destruction ─────────────────────────────────────────────
    (r"\bgit\s+push\s+.*--force(?:\b|$|-with-lease|-if-includes)", 0, "git push --force (rewrites remote history)"),
    (r"\bgit\s+push\s+-f\b", 0, "git push -f (rewrites remote history)"),
    (r"\bgit\s+reset\s+--hard\b", 0, "git reset --hard (discards uncommitted changes)"),
    (r"\bgit\s+clean\s+-fdx\b", 0, "git clean -fdx (deletes untracked + ignored)"),
    (r"\bgit\s+branch\s+-D\b", 0, "git branch -D (force-delete, even unmerged)"),
    (r"\bgit\s+stash\s+drop\b", 0, "git stash drop (discards stashed work)"),
    (r"\bgit\s+checkout\s+--\s+\.", 0, "git checkout -- . (discards all working changes)"),
    (r"\bgit\s+restore\s+--staged\s+--worktree\s+\.", 0, "git restore --staged --worktree . (full discard)"),

    # ── Database destruction ────────────────────────────────────────
    (r"\bDROP\s+(TABLE|DATABASE|INDEX|SCHEMA|VIEW|TRIGGER|PROCEDURE|FUNCTION|USER|ROLE)\b", re.IGNORECASE, "Destructive SQL DROP"),
    (r"\bTRUNCATE\s+(TABLE\b)?\b", re.IGNORECASE, "Destructive SQL TRUNCATE"),
    # DELETE FROM <tbl> with NO WHERE: parse whole command
    (r"\bDELETE\s+FROM\s+\w+\s*(?!.*\bWHERE\b)", re.IGNORECASE | re.DOTALL, "DELETE FROM without WHERE"),
    (r"\bUPDATE\s+\w+\s+SET\s+(?!.*\bWHERE\b)", re.IGNORECASE | re.DOTALL, "UPDATE without WHERE"),
    (r"\bDROP\s+DATABASE\b", re.IGNORECASE, "Destructive SQL DROP DATABASE"),
    (r"\bREVOKE\s+ALL\b", re.IGNORECASE, "REVOKE ALL"),

    # ── System / privilege escalation ──────────────────────────────
    (r"\bchmod\s+(-R\s+)?777\b", 0, "chmod 777 (world-writable)"),
    (r"\bchown\s+-R\s+\w+:\w+\s+/(?:\s|$)", 0, "chown -R on root"),
    (r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;:", 0, "Fork bomb"),
    (r"\bshutdown\b|\breboot\b|\bpoweroff\b|\bhalt\b", 0, "System shutdown/reboot"),
    (r"\bmkfs\b|\bfdisk\b|\bparted\b", 0, "Partition manipulation"),

    # ── Network / exfiltration ──────────────────────────────────────
    (r"\bcurl\s+.*\|\s*(?:sh|bash|zsh)\b", 0, "curl | sh (download + execute)"),
    (r"\bwget\s+.*\|\s*(?:sh|bash|zsh)\b", 0, "wget | sh (download + execute)"),
    (r"\bnc\s+-e\b", 0, "nc -e (remote shell)"),

    # ── macOS specific (Hermes runs on macOS) ───────────────────────
    (r"\bsudo\s+rm\s+-rf?\s+/", re.IGNORECASE, "sudo rm -rf /"),
    (r"\bdiskutil\s+(eraseDisk|partitionDisk|unmountDisk)\b", 0, "diskutil destructive"),
    (r"\bdefaults\s+delete\s+.*\s+.*", 0, "defaults delete (system config loss)"),
]


def check_command(command: str) -> tuple[bool, str]:
    """Return (blocked, reason). blocked=True if the command matches a destructive pattern."""
    # Normalize: strip newlines so multi-line SQL still triggers
    normalized = " ".join(command.split())
    for pattern, flags, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, normalized, flags):
            return True, reason
    return False, ""


def log_block(command: str, reason: str, cwd: str) -> None:
    """Append a line to ~/.claude/hooks/blocked.log (best-effort, never raises)."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] cwd={cwd} | reason={reason} | cmd={command[:500]}\n")
    except Exception:
        pass  # Logging must never block the hook itself


def main() -> int:
    # Read hook payload from stdin (Claude Code passes JSON)
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0  # No input → nothing to check
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0  # Malformed input → don\'t block, let Claude see the error

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0  # Only intercept Bash

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return 0

    cwd = payload.get("cwd", os.getcwd())

    blocked, reason = check_command(command)
    if not blocked:
        return 0  # allow

    log_block(command, reason, cwd)
    # Exit code 2 = block + show stderr to Claude. Message format helps Claude explain.
    sys.stderr.write(
        f"BLOCKED by block-destructive.py: {reason}\n"
        f"Command: {command[:300]}\n"
        f"Logged to: {LOG_PATH}\n"
        f"If this is intentional, ask the user to whitelist or refactor the command.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
