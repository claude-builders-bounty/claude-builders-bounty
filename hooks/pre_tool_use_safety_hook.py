#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
Intercepts destructive bash operations and records blocked attempts.
Follows Anthropic Claude Code Hooks specification.
"""

import sys
import os
import json
import re
from datetime import datetime

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Forbidden destructive patterns
FORBIDDEN_PATTERNS = [
    (
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b|\brm\s+-(?:r\s+-f|f\s+-r)\b",
        "Recursive force removal (rm -rf)"
    ),
    (
        r"\bDROP\s+TABLE\b",
        "Destructive SQL DROP TABLE command"
    ),
    (
        r"\bgit\s+push\b.*(?:\s+--force|-f\b)",
        "Forced git push (git push --force)"
    ),
    (
        r"\bTRUNCATE(?:\s+TABLE)?\b",
        "Destructive SQL TRUNCATE TABLE command"
    ),
]

def check_command(command_str: str, project_path: str = "") -> (bool, str):
    """
    Evaluates command against destructive safety rules.
    Returns (is_allowed, block_reason).
    """
    if not command_str:
        return True, ""

    # Check for DELETE FROM without WHERE clause
    if re.search(r"\bDELETE\s+FROM\b", command_str, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", command_str, re.IGNORECASE):
            reason = "Unrestricted SQL DELETE FROM without WHERE clause"
            log_dir = os.path.dirname(BLOCKED_LOG_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().isoformat()
            log_line = (
                f"[{timestamp}] [BLOCKED] Reason: {reason} | "
                f"Path: {project_path or os.getcwd()} | "
                f"Command: {command_str.strip()}\n"
            )
            try:
                with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            return False, reason

    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            # Log the blocked attempt
            log_dir = os.path.dirname(BLOCKED_LOG_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            timestamp = datetime.now().isoformat()
            log_line = (
                f"[{timestamp}] [BLOCKED] Reason: {reason} | "
                f"Path: {project_path or os.getcwd()} | "
                f"Command: {command_str.strip()}\n"
            )
            try:
                with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as e:
                sys.stderr.write(f"Warning: could not write to blocked.log: {e}\n")

            return False, reason

    return True, ""

def main():
    # Support both JSON payload on stdin (Claude Code standard) and direct CLI invocation
    command_text = ""
    project_path = os.getcwd()

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                try:
                    payload = json.loads(raw_input)
                    tool_name = payload.get("tool_name") or payload.get("tool") or ""
                    tool_input = payload.get("tool_input") or {}
                    project_path = payload.get("cwd") or payload.get("project_path") or os.getcwd()

                    if tool_name.lower() in ["bash", "terminal", "execute_command"]:
                        command_text = tool_input.get("command") or tool_input.get("cmd") or ""
                    else:
                        # Non-bash tool invocation, allow immediately
                        print(json.dumps({"decision": "allow"}))
                        sys.exit(0)
                except json.JSONDecodeError:
                    command_text = raw_input.strip()
        except Exception:
            pass

    # If invoked directly with command line arguments
    if not command_text and len(sys.argv) > 1:
        command_text = " ".join(sys.argv[1:])

    allowed, reason = check_command(command_text, project_path)

    if not allowed:
        error_msg = (
            f"🚫 [SAFETY HOOK BLOCKED] Destructive command detected: {reason}.\n"
            f"Command: '{command_text.strip()}'\n"
            f"Logged to: {BLOCKED_LOG_PATH}"
        )
        # Inform Claude Code via both stderr and JSON response
        sys.stderr.write(error_msg + "\n")
        print(json.dumps({
            "decision": "block",
            "reason": error_msg
        }))
        sys.exit(1)

    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

if __name__ == "__main__":
    main()
