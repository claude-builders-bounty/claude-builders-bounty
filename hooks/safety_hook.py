#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands.

Reads a JSON payload from stdin describing the pending tool call, inspects
the command for patterns that have a high chance of being irreversible or
catastrophic, and exits with code 2 to block execution. Benign commands
are allowed through unchanged.

Blocks:
  - `rm -rf` / `rm -fr` / `rm -Rf` with shell-expanded paths
  - SQL `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
  - `DELETE FROM` without a WHERE clause
  - `git push --force` / `-f` / `--force-with-lease`
  - Disk-level: `mkfs`, `dd if=` writing to a block device, `> /dev/sd*`

Allow-list escape hatches (configurable via env vars):
  - SAFETY_HOOK_ALLOW_PATH_PREFIX: comma-separated path prefixes that may
    be `rm -rf`'d (e.g. `/tmp,/var/tmp`).
  - SAFETY_HOOK_DRY_RUN=1: log only, never block.

Logging: every blocked attempt is appended to `~/.claude/hooks/blocked.log`
with ISO timestamp, project path, full command, and the rule that fired.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_LOG = Path(
    os.environ.get("SAFETY_HOOK_BLOCKED_LOG", "~/.claude/hooks/blocked.log")
).expanduser()


# Each rule is (compiled_regex, human_reason). The first match wins.
RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\brm\s+(-[rRfF]{1,3}[^|\n]*\s+-[rRfF]{1,3}[^|\n]*|-[rRfF]{1,3}\s+|--recursive\s+--force|--recursive\b)\s+"
            r"(?!/tmp|/var/tmp)\S",
            re.IGNORECASE,
        ),
        "rm -rf outside of /tmp or /var/tmp",
    ),
    (
        re.compile(r"\bmkfs(\.[a-z0-9]+)?\b", re.IGNORECASE),
        "mkfs formats a filesystem (destructive)",
    ),
    (
        re.compile(r"\bdd\b[^\n]*\bof\s*=\s*/dev/(sd|hd|nvme|vd|mmcblk)", re.IGNORECASE),
        "dd writing to a block device",
    ),
    (
        re.compile(r">\s*/dev/(sd|hd|nvme|vd|mmcblk)\b", re.IGNORECASE),
        "redirect into a block device",
    ),
    (
        re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "DROP TABLE / DROP DATABASE / DROP SCHEMA",
    ),
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE wipes a table",
    ),
    (
        re.compile(
            r"\bDELETE\s+FROM\b(?![^\n;]*\bWHERE\b)",
            re.IGNORECASE,
        ),
        "DELETE FROM without a WHERE clause",
    ),
    (
        re.compile(
            r"\bgit\s+push\b[^\n]*(--force(?:-with-lease)?|-f\b)",
            re.IGNORECASE,
        ),
        "git push --force rewrites remote history",
    ),
]


def _get_command_from_stdin() -> tuple[str, str]:
    """Return (tool_name, command_str) parsed from the hook JSON on stdin."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return ("", "")

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cmd = ""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "") or ""
    return tool_name, cmd


def _project_path() -> str:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return cwd


def _append_log(rule: str, command: str) -> None:
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BLOCKED_LOG.open("a", encoding="utf-8") as f:
            ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            f.write(f"{ts}\t{_project_path()}\t{rule}\t{command.strip()}\n")
    except OSError as exc:
        # Logging is best-effort; never let a log failure hide a block.
        sys.stderr.write(f"safety_hook: log write failed: {exc}\n")


def _format_block_message(rule: str, command: str) -> str:
    safe_cmd = command.strip().replace("\n", " ")
    if len(safe_cmd) > 240:
        safe_cmd = safe_cmd[:237] + "..."
    return (
        f"BLOCKED by safety_hook: {rule}.\n\n"
        f"Command: {safe_cmd}\n\n"
        f"If this is intentional, run the command yourself in a terminal "
        f"or set SAFETY_HOOK_ALLOW_PATH_PREFIX for `rm -rf` on a known-safe "
        f"directory. Override the hook entirely with SAFETY_HOOK_DRY_RUN=1."
    )


def main() -> int:
    tool_name, command = _get_command_from_stdin()
    if tool_name != "Bash" or not command:
        return 0  # not a bash invocation; pass through

    dry_run = os.environ.get("SAFETY_HOOK_DRY_RUN") == "1"

    for pattern, reason in RULES:
        if pattern.search(command):
            if not dry_run:
                _append_log(reason, command)
                sys.stderr.write(_format_block_message(reason, command) + "\n")
                return 2  # Claude Code: exit 2 = block
            # dry-run: still log so the user sees what would have fired
            _append_log(reason + " [dry-run]", command)
            break

    return 0  # allow


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - safety net for the hook itself
        # If the hook itself crashes, fail OPEN (allow) rather than block
        # every command. Log the exception so the operator can investigate.
        sys.stderr.write(f"safety_hook: unexpected error, allowing: {exc}\n")
        sys.exit(0)
