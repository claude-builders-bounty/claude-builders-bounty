#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Guard Hook
Intercepts destructive bash commands before execution and logs security events.
"""

import sys
import os
import re
import json
from datetime import datetime

# Blocked pattern definitions
BLOCKED_PATTERNS = [
    {
        "name": "Recursive Force Removal (rm -rf)",
        "custom_check": lambda cmd: is_recursive_force_rm(cmd),
        "description": "Recursive force removal of directories/files is blocked to prevent irreversible filesystem data loss."
    },
    {
        "name": "SQL DROP TABLE / VIEW / DATABASE",
        "regex": r"(?i)\bDROP\s+(TABLE|VIEW|DATABASE|SCHEMA)\b",
        "description": "Dropping database tables or schemas is blocked to prevent irreversible data loss."
    },
    {
        "name": "Git Force Push",
        "regex": r"\bgit\s+push\s+.*(-f|--force|--force-with-lease)\b",
        "description": "Git force-pushing is blocked to prevent overwriting remote branch history."
    },
    {
        "name": "SQL TRUNCATE",
        "regex": r"(?i)\bTRUNCATE(\s+TABLE)?\b",
        "description": "Truncating database tables is blocked to prevent accidental deletion of all records."
    },
    {
        "name": "SQL DELETE Without WHERE",
        "custom_check": lambda cmd: is_unbounded_delete(cmd),
        "description": "Unbounded SQL DELETE without a WHERE clause is blocked to prevent wiping entire tables."
    }
]

def is_recursive_force_rm(cmd: str) -> bool:
    """Checks for recursive force removal across any flag combination or prefix."""
    tokens = cmd.split()
    if not tokens:
        return False
    is_rm = False
    rm_idx = -1
    for i, tok in enumerate(tokens):
        if tok in ("rm", "/bin/rm", "/usr/bin/rm") or tok.endswith("/rm"):
            is_rm = True
            rm_idx = i
            break
    if not is_rm:
        return False

    has_r = False
    has_f = False
    for tok in tokens[rm_idx + 1:]:
        if tok in ("--recursive", "-r", "-R"):
            has_r = True
        elif tok in ("--force", "-f"):
            has_f = True
        elif tok.startswith("-") and not tok.startswith("--"):
            flags = tok[1:]
            if "r" in flags or "R" in flags:
                has_r = True
            if "f" in flags or "F" in flags:
                has_f = True
    return has_r and has_f

def is_unbounded_delete(cmd: str) -> bool:
    """Checks for SQL DELETE statement that omits a WHERE clause."""
    lower = cmd.lower()
    if "delete from" in lower:
        # Check if 'where' exists after 'delete from'
        parts = lower.split("delete from")
        for part in parts[1:]:
            if "where" not in part:
                return True
    return False

def split_shell_pipeline(cmd_str: str) -> list[str]:
    parts = re.split(r"(?:&&|\|\||[;\n])", cmd_str)
    return [p.strip() for p in parts if p.strip()]

def is_safe_prose_command(cmd: str) -> bool:
    tokens = cmd.strip().split()
    if not tokens:
        return True
    first = tokens[0].lower()
    if first in ("echo", "printf", "grep", "rg", "ag", "#"):
        return True
    if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] in ("commit", "log", "diff"):
        return True
    return False

def evaluate_single_command(cmd: str) -> tuple[bool, str, str]:
    if is_safe_prose_command(cmd):
        return False, "", ""
    for rule in BLOCKED_PATTERNS:
        if "regex" in rule and re.search(rule["regex"], cmd):
            return True, rule["name"], rule["description"]
        if "custom_check" in rule and rule["custom_check"](cmd):
            return True, rule["name"], rule["description"]
    return False, "", ""

def evaluate_command(command_str: str) -> tuple[bool, str, str]:
    """
    Evaluates a command against the security rules, checking individual pipeline commands.
    Returns: (is_blocked, pattern_name, reason)
    """
    sub_cmds = split_shell_pipeline(command_str)
    for sub in sub_cmds:
        blocked, name, reason = evaluate_single_command(sub)
        if blocked:
            return True, name, reason
    return False, "", ""

def log_blocked_attempt(command: str, rule_name: str, cwd: str = ""):
    log_dir = os.environ.get("CLAUDE_HOOKS_DIR", os.path.expanduser("~/.claude/hooks"))
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        log_dir = os.path.join(cwd or os.getcwd(), ".claude_hooks")
        os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, "blocked.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_path = cwd or os.getcwd()
    
    entry = f"[{timestamp}] BLOCKED: rule='{rule_name}' | path='{project_path}' | command='{command}'\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def main():
    """
    Hook Entrypoint.
    Supports:
    1. Direct CLI invocation: `pre_tool_use_guard.py "rm -rf /tmp/foo"`
    2. Claude Code JSON payload from stdin: `{"tool": "bash", "command": "..."}`
    """
    command_to_check = ""
    cwd = os.getcwd()

    if len(sys.argv) > 1:
        command_to_check = " ".join(sys.argv[1:])
    else:
        # Read from stdin if piped
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                try:
                    payload = json.loads(stdin_data)
                    command_to_check = payload.get("command") or payload.get("cmd") or payload.get("input", {}).get("command", "")
                    cwd = payload.get("cwd") or os.getcwd()
                except json.JSONDecodeError:
                    command_to_check = stdin_data
        except Exception:
            pass

    if not command_to_check:
        # No command to inspect, permit pass-through
        sys.exit(0)

    is_blocked, rule_name, reason = evaluate_command(command_to_check)

    if is_blocked:
        log_blocked_attempt(command_to_check, rule_name, cwd)
        error_msg = (
            f"\n⛔ [SECURITY HOOK BLOCKED COMMAND]\n"
            f"Rule Triggered: {rule_name}\n"
            f"Attempted Command: {command_to_check}\n"
            f"Reason: {reason}\n"
            f"Action: Execution aborted. Please use safer non-destructive alternatives or request explicit user confirmation.\n"
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Allowed
    sys.exit(0)

if __name__ == "__main__":
    main()
