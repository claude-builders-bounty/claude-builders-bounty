#!/usr/bin/env python3
"""Block destructive Bash commands before Claude Code runs them."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class BlockReason:
    pattern: str
    reason: str


BLOCKLIST: tuple[BlockReason, ...] = (
    BlockReason(
        r"\brm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b",
        "recursive force delete command",
    ),
    BlockReason(
        r"\bsudo\s+rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b",
        "privileged recursive force delete command",
    ),
    BlockReason(
        r"\b(?:git\s+push\b[^\n;&|]*\s--force(?:-with-lease)?|git\s+push\b[^\n;&|]*\s-f\b)",
        "force push command",
    ),
    BlockReason(r"\bgit\s+reset\s+--hard\b", "hard git reset command"),
    BlockReason(r"\bgit\s+clean\b[^\n;&|]*\s-[A-Za-z]*[fF][A-Za-z]*[dD]\b", "force clean command"),
    BlockReason(r"\bDROP\s+(?:DATABASE|SCHEMA|TABLE)\b", "destructive SQL drop command"),
    BlockReason(r"\bTRUNCATE\s+(?:TABLE\s+)?[A-Za-z_][\w.]*\b", "destructive SQL truncate command"),
    BlockReason(r"\bDELETE\s+FROM\s+[A-Za-z_][\w.]*\s*(?:;|$)", "SQL delete without a WHERE clause"),
    BlockReason(
        r"\bdd\s+.*\bof=/dev/(?:sd[a-z]\d*|nvme\d+n\d+(?:p\d+)?|disk\d+|rdisk\d+)\b",
        "raw disk overwrite command",
    ),
    BlockReason(r"\bmkfs(?:\.[A-Za-z0-9]+)?\s+/dev/", "filesystem formatting command"),
    BlockReason(
        r">\s*/dev/(?:sd[a-z]\d*|nvme\d+n\d+(?:p\d+)?|disk\d+|rdisk\d+)\b",
        "direct write to block device",
    ),
    BlockReason(r"\bchmod\s+-R\s+777\s+(?:/|~|\.{1,2})(?:\s|$)", "broad recursive permission change"),
)


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.replace("\\\n", " ")).strip()


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def targets_root_delete(command: str) -> bool:
    words = shell_words(command)
    if not words:
        return False

    for index, word in enumerate(words):
        if word != "rm":
            continue
        args = words[index + 1 :]
        has_recursive = any(arg.startswith("-") and ("r" in arg.lower() or "R" in arg) for arg in args)
        has_force = any(arg.startswith("-") and "f" in arg.lower() for arg in args)
        targets = [arg for arg in args if not arg.startswith("-")]
        if has_recursive and has_force and any(target in {"/", "/*", "~", "$HOME"} for target in targets):
            return True
    return False


def delete_without_where(command: str) -> bool:
    statements = [part.strip() for part in re.split(r";|\n", command) if part.strip()]
    for statement in statements:
        if re.search(r"\bDELETE\s+FROM\s+[A-Za-z_][\w.]*\b", statement, flags=re.IGNORECASE):
            if not re.search(r"\bWHERE\b", statement, flags=re.IGNORECASE):
                return True
    return False


def find_block_reason(command: str) -> str | None:
    normalized = normalize_command(command)
    if targets_root_delete(normalized):
        return "recursive force delete targeting a root or home directory"

    if delete_without_where(normalized):
        return "SQL delete without a WHERE clause"

    for block in BLOCKLIST:
        if re.search(block.pattern, normalized, flags=re.IGNORECASE):
            return block.reason
    return None


def log_blocked_command(reason: str, command: str) -> None:
    log_path = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "command": command,
        }
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except OSError:
        pass


def deny(reason: str, command: str) -> None:
    log_blocked_command(reason, command)
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}. Command: {command}",
        }
    }
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = find_block_reason(command)
    if reason:
        deny(reason, normalize_command(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
