#!/usr/bin/env python3
"""
pre-tool-use — Claude Code pre-tool-use hook (Python)
Blocks dangerous commands before execution.

Called by Claude Code before every Bash tool invocation.
Arguments come via stdin as JSON or command-line args.

Install:
    cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
    chmod +x ~/.claude/hooks/pre-tool-use

Exit 0 = allow, exit 1 = block with message.
"""

import json
import os
import re
import sys
from datetime import datetime

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")


# ══════════════════════════════════════════════════════════════════════════
#  PATTERN DEFINITIONS
#  (pattern, human_message)
# ══════════════════════════════════════════════════════════════════════════

PATTERNS = [
    # rm -rf variants
    (r"^rm\s+(-[a-z]*rf[a-z]*|-[a-z]*f[a-z]*r[a-z]*)", "rm -rf is blocked"),
    (r"^rm\s+.*--recursive.*--force", "rm -rf (recursive force) is blocked"),

    # DROP TABLE/DATABASE
    (r"\bdrop\s+(table|database)\b", "DROP TABLE/DATABASE is blocked"),

    # git push --force/-f (but NOT --force-with-lease)
    (r"git\s+push\s+.*--force(?!\S)", "git push --force is blocked: use --force-with-lease"),
    (r"git\s+push\s+(\S+\s+)*-f\b", "git push -f is blocked: use --force-with-lease"),

    # TRUNCATE
    (r"\btruncate\s+(table)?", "TRUNCATE is blocked: use DELETE with WHERE"),

    # chmod -R 777
    (r"chmod\s+(-[a-z]*[rR][a-z]*\s*)?777", "chmod 777 is blocked: use 755/644"),

    # chown -R
    (r"chown\s+(-[a-z]*[rR][a-z]*)", "chown -R is blocked"),

    # dd
    (r"^dd\s+(if=|of=)", "dd is blocked: disk overwrite risk"),

    # :(){ :|:& };: (fork bomb)
    (r":\s*\(\s*\)\s*\{", "fork bomb pattern blocked"),
]


def is_dangerous(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any dangerous pattern.
    Returns (is_dangerous, reason).
    """
    normalized = " ".join(command.split()).strip()
    lower = normalized.lower()

    # DELETE FROM without WHERE — special case
    if re.search(r"\bdelete\s+from\b", lower):
        if re.search(r"\bwhere\b", lower):
            return False, ""
        return True, "DELETE FROM without WHERE is blocked: add a WHERE clause"

    for pattern, message in PATTERNS:
        if re.search(pattern, lower):
            return True, message

    return False, ""


def log_blocked(tool_name: str, command: str):
    """Log a blocked attempt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project = os.getcwd()
    entry = f"[{timestamp}] BLOCKED | tool={tool_name} | project={project} | cmd={command}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass


def main():
    # ── Parse input ──────────────────────────────────────────────────────
    tool_name = ""
    command = ""

    # Try JSON from stdin (Claude Code passes structured input)
    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            tool_name = data.get("tool_name", data.get("tool", ""))
            command = data.get("command", data.get("arguments", ""))
            # command might be a list
            if isinstance(command, list):
                command = " ".join(command)
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: command-line args
    if not tool_name and len(sys.argv) > 1:
        tool_name = sys.argv[1]
    if not command and len(sys.argv) > 2:
        command = " ".join(sys.argv[2:])

    # ── Only intercept Bash ──────────────────────────────────────────────
    if tool_name.lower() not in ("bash", "shell", "exec", "run"):
        sys.exit(0)

    if not command.strip():
        sys.exit(0)

    # ── Check ────────────────────────────────────────────────────────────
    dangerous, reason = is_dangerous(command)
    if not dangerous:
        sys.exit(0)

    # ── Block ────────────────────────────────────────────────────────────
    log_blocked(tool_name, command.strip())

    import shutil
    width = shutil.get_terminal_size((80, 24)).columns

    print()
    print("=" * min(width, 78))
    print("  COMMAND BLOCKED BY SECURITY HOOK")
    print("=" * min(width, 78))
    print(f"  Command: {command.strip()}")
    print(f"  Reason:  {reason}")
    print(f"  Logged:  {LOG_FILE}")
    print("=" * min(width, 78))
    print()

    sys.exit(1)


if __name__ == "__main__":
    main()
