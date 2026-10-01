#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Installed as a `pre-tool-use` hook matching the `Bash` tool.
Receives JSON on stdin (Claude Code hooks format), inspects the
command string, and blocks dangerous patterns.

Exit 0  → command allowed (passthrough)
Exit 1  → command blocked; denial message written to stderr
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Dangerous patterns: (regex, human-readable reason)
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS = [
    (r'\brm\s+-[rf]|\brm\s+-[rf]', "rm -rf (recursive force delete)"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE (destructive SQL)"),
    (r'\bgit\s+push\s+--force', "git push --force (force overwrite remote)"),
    (r'\bTRUNCATE\b', "TRUNCATE (wipes table data)"),
    # DELETE FROM without WHERE — case-insensitive, multiline-aware
    (r'DELETE\s+FROM\s+(?!.*\bWHERE\b)', "DELETE FROM without WHERE clause"),
]

# Log file path
BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def load_event() -> dict:
    """Read and parse the Claude Code hook event from stdin."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def extract_command(event: dict) -> str:
    """Pull the bash command from the Claude Code hook event."""
    # Claude Code sends: {"tool_name": "Bash", "input": {"command": "..."}}
    tool_input = event.get("input", {})
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    return ""


def check_dangerous(command: str) -> str | None:
    """Return the reason string if the command is dangerous, else None."""
    cmd_upper = command.upper()
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_upper, re.IGNORECASE | re.DOTALL):
            return reason
    return None


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked-attempt entry to ~/.claude/hooks/blocked.log."""
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = f"[{ts}] BLOCKED reason={reason} command={command!r} project={project_path}\n"
    BLOCKED_LOG.write_text(BLOCKED_LOG.read_text() if BLOCKED_LOG.exists() else "" + entry, encoding="utf-8")


def main() -> None:
    event = load_event()
    command = extract_command(event)
    project_path = event.get("tool_input", {}).get("description", "") or event.get("cwd", "") or Path.cwd().as_posix()

    if not command:
        # No command to inspect — allow passthrough
        sys.exit(0)

    reason = check_dangerous(command)
    if reason:
        log_blocked(command, reason, project_path)
        denial = (
            f"🛡️ BLOCKED: {reason}\n"
            f"   Command: {command}\n"
            f"   This command was intercepted by the pre-tool-use safety hook.\n"
            f"   If this is intentional, review ~/.claude/hooks/blocked.log and "
            f"override manually after confirming safety."
        )
        print(denial, file=sys.stderr)
        sys.exit(1)

    # Safe — allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()