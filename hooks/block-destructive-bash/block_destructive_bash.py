#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: block destructive bash commands.

Reads JSON from stdin (Claude Code hook payload), inspects Bash tool calls,
and blocks dangerous patterns by exiting with code 2 and printing a JSON
decision to stdout. Allows everything else through with exit 0.

Install: see hooks/block-destructive-bash/README.md
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

LOG_PATH = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))
CONFIG_PATH = Path(os.path.expanduser("~/.claude/hooks/block_destructive_bash.config.json"))

# (pattern, human-readable reason). Patterns are case-insensitive regex.
DEFAULT_RULES: list[tuple[str, str]] = [
    # Filesystem nukes
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b",
     "rm -rf is destructive and irreversible"),
    (r"\brm\s+-rf?\s+(/|/\*|~|~/|\$HOME|\.)\s*$",
     "rm targeting root/home/cwd is catastrophic"),
    (r"\bmkfs(\.|\s)", "mkfs formats a filesystem — data loss"),
    (r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:", "fork bomb"),
    (r">\s*/dev/(sd[a-z]|nvme|disk|hd[a-z])", "writing to a raw block device destroys it"),
    (r"\bdd\s+.*\bof=/dev/(sd[a-z]|nvme|disk|hd[a-z])", "dd to a raw disk destroys it"),
    (r"\bchmod\s+(-[a-zA-Z]*\s+)?777\b", "chmod 777 is a security disaster"),

    # Git footguns
    (r"\bgit\s+push\s+(.*\s)?(-f\b|--force(-with-lease)?\b)", "force push rewrites remote history"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards uncommitted work"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f deletes untracked files"),
    (r"\bgit\s+checkout\s+\.\s*$", "git checkout . discards local changes"),

    # SQL footguns (match in -c/--execute strings or heredocs)
    (r"\bDROP\s+TABLE\b", "DROP TABLE drops a table"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE drops a database"),
    (r"\bTRUNCATE\b", "TRUNCATE wipes a table"),
    (r"\bDELETE\s+FROM\s+[\w\".`]+\s*(;|--|$)(?![\s\S]*\bWHERE\b)",
     "DELETE FROM without a WHERE clause wipes the table"),

    # Shutdown / reboot
    (r"\b(shutdown|halt|poweroff|reboot)\b", "system power command"),
]


def load_config() -> dict:
    """Load optional config: allowlist (regex) and extra rules."""
    if not CONFIG_PATH.exists():
        return {"allowlist": [], "extra_rules": [], "disabled_rules": []}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {"allowlist": [], "extra_rules": [], "disabled_rules": []}


def is_allowlisted(command: str, allowlist: list[str]) -> bool:
    for pat in allowlist:
        try:
            if re.search(pat, command, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


def find_violation(command: str, cfg: dict) -> tuple[str, str] | None:
    disabled = set(cfg.get("disabled_rules", []))
    rules = [(p, r) for (p, r) in DEFAULT_RULES if p not in disabled]
    for pat, reason in cfg.get("extra_rules", []):
        rules.append((pat, reason))

    for pat, reason in rules:
        try:
            if re.search(pat, command, re.IGNORECASE | re.MULTILINE):
                return pat, reason
        except re.error:
            continue
    return None


def log_blocked(command: str, reason: str, project: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        entry = {
            "timestamp": ts,
            "project": project,
            "reason": reason,
            "command": command,
        }
        with LOG_PATH.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never let logging break the hook


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0  # not our problem, let it through

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    cfg = load_config()
    project = payload.get("cwd") or os.getcwd()

    if is_allowlisted(command, cfg.get("allowlist", [])):
        return 0

    hit = find_violation(command, cfg)
    if not hit:
        return 0

    _pattern, reason = hit
    log_blocked(command, reason, project)

    # Claude Code: exit 2 = block + show stderr to model.
    # We also emit a structured decision JSON on stdout for hook consumers
    # that prefer structured output (newer hook protocol).
    decision = {
        "decision": "block",
        "reason": (
            f"Blocked by block-destructive-bash hook: {reason}.\n"
            f"Command: {command}\n"
            f"To allow this command, add a regex to the allowlist in "
            f"{CONFIG_PATH} or run it manually outside Claude Code."
        ),
    }
    print(json.dumps(decision))
    print(decision["reason"], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
