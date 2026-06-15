#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks dangerous bash commands before execution.

Exit codes:
  0 = allow (no decision, normal permission flow applies)
  2 = block (stderr shown to Claude; command is denied)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS = [
    # ── rm destructive flags (handles -rf, -fr, -r -f, --recursive --force) ──
    (r"\brm\s+.*?(?:-[rf]{0,2}r[rf]*|--recursive)\b", "rm with recursive flag"),
    # ── git push --force / -f / --force-with-lease ──
    (r"\bgit\s+push\s+.*?(?:--force-with-lease|--force|-f\b)", "git push --force"),
    # ── SQL DROP ──
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP TABLE/DATABASE"),
    # ── SQL TRUNCATE ──
    (r"\bTRUNCATE\s+(?:TABLE\s+)?\w", "TRUNCATE"),
    # ── DELETE FROM without WHERE clause ──
    (r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", "DELETE FROM without WHERE"),
    # ── destructive disk ops ──
    (r"\b(dd\s+if=|mkfs\.|mkswap\b)", "destructive disk operation"),
    # ── chmod 777 on system paths ──
    (r"\bchmod\s+.*777\s+/(?:etc|usr|var|bin|sbin|lib|opt|root|sys)", "chmod 777 on system path"),
    # ── fork bomb ──
    (r":\(\)\s*\{[^}]*:[^}]*\}", "fork bomb"),
    # ── curl piped to shell interpreter ──
    (r"\bcurl\s+.*\|\s*(?:ba)?sh\b", "curl pipe bash"),
]

# ── False-positive allowlist ──
# Commands that contain substring matches of dangerous patterns but are safe.
# IMPORTANT: these only apply when the overall command context is obviously safe.
ALLOWLIST = [
    # Package managers (may echo "cleaning node_modules" then run rm -rf internally)
    r"\bnpm\s+(run|exec|start|test|build|ci|clean|publish)",
    r"\bpip\s+(install|uninstall|download|list|show|check)",
    r"\byarn\s+(add|remove|install|build|start|test|run)",
    r"\bcargo\s+(build|run|test|check|clean|install|add|remove)",
    # Safe git operations (not push --force)
    r"\bgit\s+(status|log|diff|show|add|commit|checkout|branch|stash|pull|fetch|merge|rebase\s+-i[^m]*)",
    # GitHub CLI (safe operations)
    r"\bgh\s+(pr|issue|repo|auth|config|gist|release)\s",
    # Informational commands that just display text
    r"^(echo|printf)\s+['\"].*['\"]\s*$",
]


def ensure_log_dir() -> str:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    return LOG_PATH


def log_block(attempted: str, cwd: str) -> None:
    log_path = ensure_log_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": attempted,
        "project_path": cwd,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def is_allowed(command: str) -> bool:
    for pattern in ALLOWLIST:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def find_threat(command: str) -> tuple[str, str] | None:
    for pattern, label in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            return pattern, label
    return None


def format_block_message(command: str, label: str) -> str:
    return "\n".join([
        "",
        "╔══════════════════════════════════════════════╗",
        "║  ⛔  COMMAND BLOCKED — SECURITY HOOK        ║",
        "╠══════════════════════════════════════════════╣",
        f"║  Pattern:  {label:<36s}║",
        "╠══════════════════════════════════════════════╣",
        f"║  Command:  {command[:50]:<36s}║" if len(command) <= 50 else
        f"║  Cmd:      {command[:47]}...║",
        "╠══════════════════════════════════════════════╣",
        "║  This command matched a destructive         ║",
        "║  pattern and was blocked to prevent data     ║",
        "║  loss. If you are certain this is safe,      ║",
        "║  temporarily disable the hook or use a       ║",
        "║  safer alternative (e.g. 'mv to trash'       ║",
        "║  instead of 'rm -rf').                       ║",
        "╚══════════════════════════════════════════════╝",
        "",
    ])


def main() -> None:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)  # Can't parse → don't block

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)  # Only handle Bash

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    cwd = input_data.get("cwd", os.getcwd())

    # Allowlist check first
    if is_allowed(command):
        sys.exit(0)

    # Threat check
    threat = find_threat(command)
    if threat is None:
        sys.exit(0)  # No threat detected

    _pattern, label = threat

    # Block it
    log_block(command, cwd)
    print(format_block_message(command, label), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
