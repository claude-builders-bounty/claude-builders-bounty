#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Reads the JSON hook payload from stdin, checks for dangerous patterns,
logs every blocked attempt, and outputs a JSON decision for Claude.

Install:
    cp hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
    chmod +x ~/.claude/hooks/pre_tool_use.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# ---------------------------------------------------------------------------
# Dangerous patterns — each is (compiled_regex, human_label)
# ---------------------------------------------------------------------------
def _p(pattern: str, flags: int = re.IGNORECASE) -> re.Pattern[str]:
    return re.compile(pattern, flags)


DANGEROUS: list[tuple[re.Pattern[str], str]] = [
    # ── Filesystem destruction ────────────────────────────────────────────
    (
        _p(
            r"\brm\b[^|&;\n]*?"
            r"("
            r"-[^\s-]*r[^\s-]*f"          # combined -rf or -xrxfx
            r"|-[^\s-]*f[^\s-]*r"          # combined -fr or -xfxrx
            r"|-[^\s]*r[^|&;\n]*-[^\s]*f"  # split: -r ... -f
            r"|-[^\s]*f[^|&;\n]*-[^\s]*r"  # split: -f ... -r
            r"|--recursive[^|&;\n]*--force"
            r"|--force[^|&;\n]*--recursive"
            r")"
        ),
        "rm -rf — recursive forced removal; permanently destroys files/directories",
    ),
    (
        _p(r"\brm\b[^|&;]*?--no-preserve-root"),
        "rm --no-preserve-root — can delete the entire root filesystem",
    ),
    (
        _p(r"\bdd\b[^|&;]*\bof=/dev/[sh]d[a-z]"),
        "dd to block device — irreversibly overwrites raw disk data",
    ),
    (
        _p(r">\s*/dev/[sh]d[a-z]"),
        "redirect to block device — irreversibly overwrites raw disk data",
    ),
    # ── Database destruction ──────────────────────────────────────────────
    (
        _p(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b"),
        "DROP TABLE/DATABASE/SCHEMA — permanently destroys database objects",
    ),
    (
        _p(r"\bTRUNCATE\s+(TABLE\s+)?\w"),
        "TRUNCATE TABLE — removes all rows; not recoverable without a backup",
    ),
    # DELETE FROM without WHERE — multi-line safe negative lookahead
    (
        _p(r"\bDELETE\s+FROM\s+\w[^;]*?;", re.IGNORECASE | re.DOTALL),
        "DELETE FROM — potential table-wipe; requires WHERE clause",
    ),
    # ── Git destructive push ──────────────────────────────────────────────
    (
        _p(r"\bgit\s+push\b[^|&;\n]*\s(--force|-[fF])(?!-with-lease)(\s|$)"),
        "git push --force — rewrites remote history; can destroy collaborators' commits",
    ),
    # ── Dangerous system operations ───────────────────────────────────────
    (
        _p(r"\bchmod\b[^|&;]*?(-R\s+)?777\s+/"),
        "chmod 777 on root path — makes system files world-writable",
    ),
    (
        _p(r":\s*\(\s*\)\s*\{.*?:\s*\|.*?:\s*&\s*\}"),
        "fork bomb — exhausts system processes and crashes the machine",
    ),
]

# Patterns that are WARNED but not blocked (logged only)
WARN_ONLY: list[tuple[re.Pattern[str], str]] = [
    (
        _p(r"\bgit\s+push\b[^|&;\n]*--force-with-lease"),
        "git push --force-with-lease — safer force push; verify remote state is as expected",
    ),
]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def is_delete_without_where(command: str) -> bool:
    """Return True if the command contains DELETE FROM ... with no WHERE."""
    # Normalize whitespace/newlines so we can scan the full statement.
    for stmt in re.findall(r"\bDELETE\s+FROM\s+[^;]+", command, re.IGNORECASE | re.DOTALL):
        if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
            return True
    return False


def check(command: str) -> tuple[list[str], list[str]]:
    """
    Returns (block_reasons, warn_reasons).

    The DELETE-without-WHERE pattern gets special handling; all other patterns
    use the compiled regexes from DANGEROUS.
    """
    blocks: list[str] = []
    warns: list[str] = []

    for pattern, label in DANGEROUS:
        # Skip the generic DELETE pattern here; handled separately below.
        if "DELETE FROM" in label:
            continue
        if pattern.search(command):
            blocks.append(label)

    if is_delete_without_where(command):
        blocks.append(
            "DELETE FROM without WHERE — would delete every row in the table"
        )

    for pattern, label in WARN_ONLY:
        if pattern.search(command):
            warns.append(label)

    return blocks, warns


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(level: str, command: str, details: str) -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "command": command,
        "details": details,
        "project_path": os.getcwd(),
    }
    with BLOCKED_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _blocked_message(command: str, reasons: list[str]) -> str:
    reason_lines = "\n".join(f"  • {r}" for r in reasons)
    return (
        f"🚫 BLOCKED — destructive command prevented\n\n"
        f"Command:  {command}\n\n"
        f"Reason(s):\n{reason_lines}\n\n"
        f"This command was blocked because it could cause irreversible damage. "
        f"If you are certain it is safe, run it manually outside Claude Code.\n"
        f"Blocked attempts are logged to: {BLOCKED_LOG}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command: str = payload.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    block_reasons, warn_reasons = check(command)

    for reason in warn_reasons:
        _log("WARN", command, reason)

    if block_reasons:
        _log("BLOCK", command, "; ".join(block_reasons))
        print(json.dumps({
            "decision": "block",
            "reason": _blocked_message(command, block_reasons),
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
