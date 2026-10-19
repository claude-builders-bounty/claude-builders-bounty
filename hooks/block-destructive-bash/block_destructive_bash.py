#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Interceptor
Blocks dangerous commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, unconstrained DELETE)
and logs attempts to ~/.claude/hooks/blocked.log.
"""
import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOKS_DIR / "blocked.log"

# Compile destructive command pattern matchers
PATTERNS = [
    # 1. rm -rf variations (including separated -r -f, combined -rf, --recursive --force)
    (
        re.compile(
            r"\brm\s+(?:[^\n\r;]*\s+)?(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive|-[a-zA-Z]*r[a-zA-Z]*\s+(?:[^\n\r;]*\s+)?-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*\s+(?:[^\n\r;]*\s+)?-[a-zA-Z]*r[a-zA-Z]*)\b",
            re.IGNORECASE
        ),
        "Recursive force removal (`rm -rf`)",
        "Use `trash-cli` or delete individual non-critical files specifically without `-rf` flags."
    ),
    # 2. DROP TABLE / DATABASE / SCHEMA
    (
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "Database Drop Operation (`DROP TABLE/DATABASE/SCHEMA`)",
        "Use database migration scripts with down/rollback semantics or soft deletion."
    ),
    # 3. git push --force / -f
    (
        re.compile(r"\bgit\s+push\s+(?:[^\n\r]*\s+)?(?:--force|-f|\+[a-zA-Z0-9_\-\/]+)\b", re.IGNORECASE),
        "Force git push (`git push --force`)",
        "Use standard `git push` or `--force-with-lease` after consulting the repository maintainer."
    ),
    # 4. TRUNCATE TABLE
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_\.\"`']+", re.IGNORECASE),
        "Table Truncation (`TRUNCATE`)",
        "Specify explicit DELETE queries with scoped WHERE conditions or backup snapshots."
    ),
    # 5. Dangerous disk / filesystem wipe
    (
        re.compile(r"\b(?:mkfs|dd\s+if=.*of=/dev/)\b", re.IGNORECASE),
        "Direct disk format or raw block write",
        "Filesystem creation and raw disk operations are strictly disallowed."
    ),
]

def check_delete_without_where(cmd: str) -> Optional[Tuple[str, str]]:
    """
    Check if query contains DELETE FROM without a corresponding WHERE clause.
    """
    # Look for DELETE FROM ... pattern
    delete_matches = list(re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\.\"`']+)(.*?)(?:;|$)", cmd, re.IGNORECASE | re.DOTALL))
    for match in delete_matches:
        clause_body = match.group(2)
        if not re.search(r"\bWHERE\b", clause_body, re.IGNORECASE):
            return (
                "Unconstrained SQL Delete (`DELETE FROM` without `WHERE`)",
                "Always specify a scoped `WHERE id = ...` or safety boundary condition."
            )
    return None

def extract_command(input_data: str) -> Optional[str]:
    """
    Extract the command from Claude Code stdin payload (JSON) or raw text.
    """
    if not input_data or not input_data.strip():
        return None
    
    # Try parsing as Claude Code tool execution payload
    try:
        data = json.loads(input_data)
        if isinstance(data, dict):
            # Check tool name
            tool_name = data.get("tool_name") or data.get("tool") or ""
            # If specified and not bash/terminal, ignore
            if tool_name and tool_name.lower() not in ("bash", "execute_command", "run_command", "terminal"):
                return None
            
            tool_input = data.get("tool_input") or data.get("input") or data.get("parameters") or {}
            if isinstance(tool_input, dict):
                return tool_input.get("command") or tool_input.get("cmd") or tool_input.get("CommandLine")
            elif isinstance(tool_input, str):
                return tool_input
    except Exception:
        pass
    
    # Fallback: treat raw string as the command line
    return input_data.strip()

def log_blocked_attempt(command: str, rule: str, cwd: str):
    """
    Logs blocked command attempt to ~/.claude/hooks/blocked.log
    """
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED: {rule}\n"
            f"  Command: {command}\n"
            f"  Project: {cwd}\n"
            f"------------------------------------------------------------------------\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to {LOG_FILE}: {e}\n")

def inspect_command(command: str, cwd: str) -> bool:
    """
    Inspect command string.
    Returns True if allowed, False if blocked.
    """
    # 1. Check compiled regex patterns
    for pattern, name, recommendation in PATTERNS:
        if pattern.search(command):
            block(command, name, recommendation, cwd)
            return False

    # 2. Check unconstrained DELETE queries
    delete_issue = check_delete_without_where(command)
    if delete_issue:
        name, recommendation = delete_issue
        block(command, name, recommendation, cwd)
        return False

    return True

def block(command: str, rule_name: str, recommendation: str, cwd: str):
    log_blocked_attempt(command, rule_name, cwd)
    
    msg = f"""
🛑 [Claude Code Security Hook] Command Blocked!
================================================================================
Violation Detected: {rule_name}
Attempted Command : {command.strip()[:160]}
Working Directory : {cwd}
Safety Guidance   : {recommendation}

Every blocked command is audited in: {LOG_FILE}
================================================================================
"""
    sys.stderr.write(msg)

def main():
    cwd = os.getcwd()
    raw_input = ""

    # Check CLI arguments first
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        # Check standard input if available
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()

    command = extract_command(raw_input)
    if not command:
        # No command detected, allow
        sys.exit(0)

    is_allowed = inspect_command(command, cwd)
    if not is_allowed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
