#!/usr/bin/env python3
"""
Claude Code Pre-tool-use Hook: Destructive Bash Command Blocker

This hook intercepts Bash tool calls and blocks dangerous patterns:
- rm -rf without confirmation
- DROP TABLE statements
- TRUNCATE statements
- DELETE FROM without WHERE clause
- git push --force (unless --force-with-lease)

Installation:
    mkdir -p ~/.claude/hooks
    cp pre-tool-use.py ~/.claude/hooks/
    chmod +x ~/.claude/hooks/pre-tool-use.py

Log: ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Patterns to block (regex)
DESTRUCTIVE_PATTERNS = {
    "rm -rf": r"rm\s+(-[a-zA-Z]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?(\S+\s*)?",
    "rm -fr": r"rm\s+(-[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*\s+)?(\S+\s*)?",
    "DROP TABLE": r"DROP\s+TABLE\s+(IF\s+EXISTS\s+)?(\w+)",
    "TRUNCATE": r"TRUNCATE\s+(TABLE\s+)?(\w+)",
    "DELETE FROM no WHERE": r"DELETE\s+FROM\s+\w+",  # Will check for WHERE separately
}

# Git push --force pattern (allow --force-with-lease)
GIT_FORCE_PATTERN = r"git\s+push\s+([^\s]+\s+)*--force(?!--with-lease)"


def log_blocked(command: str, reason: str) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log"""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    project_path = os.getcwd()
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {reason} | Command: {command.strip()} | Project: {project_path}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)


def check_destructive(command: str) -> dict:
    """Check if command matches any destructive pattern."""
    cmd_lower = command.lower()

    # Check git push --force (special case - allow --force-with-lease)
    if re.search(GIT_FORCE_PATTERN, command, re.IGNORECASE):
        if "--force-with-lease" not in command:
            return {
                "blocked": True,
                "reason": "git push --force detected. Use --force-with-lease for safety.",
                "pattern": "git push --force"
            }

    # Check rm -rf / -fr / -r -f / -f -r / --recursive --force
    if "rm" in cmd_lower:
        tokens = cmd_lower.split()
        # Find index of rm
        try:
            rm_idx = -1
            for idx, token in enumerate(tokens):
                if token == "rm" or token.endswith("/rm"):
                    rm_idx = idx
                    break

            if rm_idx != -1:
                has_r = False
                has_f = False
                for token in tokens[rm_idx+1:]:
                    # Stop checking if we hit a pipe or another command separator
                    if token in [";", "&&", "||", "|"]:
                        break
                    if token.startswith("-") and not token.startswith("--"):
                        if "r" in token or "R" in token:
                            has_r = True
                        if "f" in token:
                            has_f = True
                    elif token == "--recursive":
                        has_r = True
                    elif token == "--force":
                        has_f = True
                if has_r and has_f:
                    return {
                        "blocked": True,
                        "reason": "rm -rf can destroy entire directories. Consider using safer deletion.",
                        "pattern": "rm -rf"
                    }
        except Exception:
            pass

    # DROP TABLE
    if re.search(DESTRUCTIVE_PATTERNS["DROP TABLE"], command, re.IGNORECASE):
        return {
            "blocked": True,
            "reason": "DROP TABLE will permanently delete table data. Use TRUNCATE or soft delete instead.",
            "pattern": "DROP TABLE"
        }

    # TRUNCATE
    match = re.search(DESTRUCTIVE_PATTERNS["TRUNCATE"], command, re.IGNORECASE)
    if match:
        return {
            "blocked": True,
            "reason": "TRUNCATE removes all rows from a table. Consider using DELETE with WHERE instead.",
            "pattern": "TRUNCATE"
        }

    # DELETE FROM without WHERE
    if "delete from" in cmd_lower:
        pos = cmd_lower.find("delete from")
        if "where" not in cmd_lower[pos:]:
            return {
                "blocked": True,
                "reason": "DELETE FROM without WHERE deletes ALL rows. Add a WHERE clause.",
                "pattern": "DELETE FROM (no WHERE)"
            }

    return {"blocked": False, "reason": None, "pattern": None}


def main():
    """Main hook entry point."""
    # Read tool call from stdin (JSON)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Failed to parse input: {e}"}), flush=True)
        return

    # Check if this is a Bash tool call
    if input_data.get("tool") != "Bash":
        # Not a bash call, let it through
        print(json.dumps({"allowed": True}), flush=True)
        return

    command = input_data.get("command", "")
    if not command:
        print(json.dumps({"allowed": True}), flush=True)
        return

    # Check for destructive patterns
    result = check_destructive(command)

    if result["blocked"]:
        log_blocked(command, result["pattern"])

        # Write block message to stderr (Claude will see this)
        error_msg = f"""
╔══════════════════════════════════════════════════════════════╗
║  ⛔ BLOCKED: Destructive Command Detected                     ║
╠══════════════════════════════════════════════════════════════╣
║ Pattern: {result['pattern']}
║ Reason: {result['reason']}
║
║ Command: {command[:200]}
║ Logged to: ~/.claude/hooks/blocked.log
╚══════════════════════════════════════════════════════════════╝
"""
        print(json.dumps({
            "allowed": False,
            "error_msg": error_msg.strip()
        }), flush=True)
    else:
        # Allow the command
        print(json.dumps({"allowed": True}), flush=True)


if __name__ == "__main__":
    main()
