#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Destructive Command Interceptor
Intercepts and blocks dangerous filesystem, git, and SQL commands before execution.
Complies with Claude Code hook specifications (~/.claude/hooks/).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

# Ensure UTF-8 output across platforms
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Default path for blocked command audit logging
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# Destructive Patterns & Human-Readable Explanations
RULES = [
    {
        "name": "Recursive Force Removal",
        "pattern": re.compile(
            r"\brm\s+([^\n;|&]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive|-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r[a-zA-Z]*)\b",
            re.IGNORECASE,
        ),
        "reason": "Destructive recursive deletion ('rm -rf') detected. This operation permanently removes directory trees without confirmation.",
    },
    {
        "name": "Git Force Push",
        "pattern": re.compile(
            r"\bgit\s+([^\n;|&]*\s+)?push\s+([^\n;|&]*\s+)?(--force|-f|--force-with-lease|\+[a-zA-Z0-9_\-\./]+)\b",
            re.IGNORECASE,
        ),
        "reason": "Force push ('git push --force') detected. Overwriting remote history can destroy collaborator work and branches.",
    },
    {
        "name": "SQL Drop Table",
        "pattern": re.compile(r"\bDROP\s+TABLE\s+([a-zA-Z0-9_\.\"`'\[\]]+)", re.IGNORECASE),
        "reason": "Destructive SQL operation ('DROP TABLE') detected. This destroys the database schema and all contained table records.",
    },
    {
        "name": "SQL Truncate Table",
        "pattern": re.compile(r"\bTRUNCATE(\s+TABLE)?\s+([a-zA-Z0-9_\.\"`'\[\]]+)", re.IGNORECASE),
        "reason": "Destructive SQL operation ('TRUNCATE') detected. This permanently purges all rows from the specified table.",
    },
    {
        "name": "SQL Delete Without Where",
        "pattern": re.compile(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\.\"`'\[\]]+)", re.IGNORECASE),
        "validator": lambda cmd: is_unbounded_delete(cmd),
        "reason": "Destructive SQL operation ('DELETE FROM' without 'WHERE' clause) detected. This clears all table data.",
    },
    {
        "name": "Disk Overwrite or Formatting",
        "pattern": re.compile(r"\b(mkfs(\.[a-zA-Z0-9]+)?|dd\s+if=[^\n;|&]*\s+of=/dev/[a-zA-Z0-9]+)\b", re.IGNORECASE),
        "reason": "Low-level storage formatting or raw disk overwrite command detected.",
    },
    {
        "name": "Fork Bomb",
        "pattern": re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE),
        "reason": "Denial-of-service fork bomb pattern intercepted.",
    },
]


def is_unbounded_delete(cmd: str) -> bool:
    """Check if a DELETE FROM statement lacks a WHERE clause."""
    for match in re.finditer(r"\bDELETE\s+FROM\s+([^\n;]+)", cmd, re.IGNORECASE):
        clause = match.group(0).upper()
        if "WHERE" not in clause:
            return True
    return False


def strip_echo_commands(cmd: str) -> str:
    """Removes innocuous echo/printf lines to avoid false positives on doc generation."""
    lines = []
    for line in cmd.splitlines():
        trimmed = line.strip()
        if re.match(r"^(echo|printf)\b", trimmed):
            continue
        lines.append(line)
    return "\n".join(lines)


def log_blocked_command(command: str, project_path: str, reason: str, rule_name: str) -> None:
    """Appends blocked command attempt to ~/.claude/hooks/blocked.log with ISO timestamp."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED ({rule_name})\n"
            f"  Directory: {project_path}\n"
            f"  Command:   {command.strip()}\n"
            f"  Reason:    {reason}\n"
            f"{'-' * 70}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def check_command(command: str, project_path: str | None = None) -> tuple[bool, str | None, str | None]:
    """
    Evaluates command against safety rules.
    Returns: (is_blocked: bool, rule_name: str | None, reason: str | None)
    """
    if not command or not command.strip():
        return False, None, None

    cleaned_cmd = strip_echo_commands(command)

    for rule in RULES:
        pattern = rule["pattern"]
        if pattern.search(cleaned_cmd):
            validator = rule.get("validator")
            if validator and not validator(cleaned_cmd):
                continue
            return True, rule["name"], rule["reason"]

    return False, None, None


def extract_command_from_payload(raw_input: str) -> tuple[str, str]:
    """Parses JSON tool payload or raw command string from Claude Code."""
    cwd = os.getcwd()
    cmd = raw_input.strip()

    if raw_input.strip().startswith("{") and raw_input.strip().endswith("}"):
        try:
            data = json.loads(raw_input)
            if "input" in data and isinstance(data["input"], dict):
                cmd = data["input"].get("command", "")
            elif "command" in data:
                cmd = data.get("command", "")
            if "cwd" in data:
                cwd = data["cwd"]
        except Exception:
            pass

    return cmd, cwd


def main():
    parser = argparse.ArgumentParser(description="Claude Code PreToolUse Safety Interceptor")
    parser.add_argument("--command", type=str, default=None, help="Direct command string to inspect")
    parser.add_argument("--cwd", type=str, default=None, help="Working directory path")
    args = parser.parse_args()

    project_path = args.cwd or os.getcwd()

    if args.command is not None:
        cmd = args.command
    else:
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()
            cmd, extracted_cwd = extract_command_from_payload(raw_input)
            if not args.cwd:
                project_path = extracted_cwd
        else:
            cmd = ""

    is_blocked, rule_name, reason = check_command(cmd, project_path)

    if is_blocked:
        log_blocked_command(cmd, project_path, reason, rule_name)
        error_msg = (
            f"\n\033[1;31m[BLOCKED BY CLAUDE CODE PRE-TOOL-USE GUARD]\033[0m\n"
            f"Rule Triggered: {rule_name}\n"
            f"Explanation:    {reason}\n"
            f"Blocked Input:  '{cmd.strip()}'\n"
            f"Logged to:      {LOG_FILE}\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
