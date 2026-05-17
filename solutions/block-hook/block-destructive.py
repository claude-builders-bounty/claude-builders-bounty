#!/usr/bin/env python3
"""
block-destructive.py - Claude Code pre-tool-use hook that blocks destructive bash commands.

This hook intercepts bash commands before execution and blocks dangerous patterns:
  - rm -rf (recursive force removal)
  - DROP TABLE (database destruction)
  - git push --force (destructive git operation)
  - TRUNCATE (database mass deletion)
  - DELETE FROM without WHERE clause (accidental mass deletion)

Installation: see README.md
"""

import json
import sys
import os
import re
from datetime import datetime

# ── Dangerous patterns ──────────────────────────────────────────────
# Each entry: (compiled_regex, human_readable_name, explanation)
DANGEROUS_PATTERNS = [
    (
        re.compile(
            r'\brm\s+'  # rm command
            r'(?:'       # options can be combined or separate
            r'-[a-zA-Z]*f[a-zA-Z]*(?:\s|$)'  # combined flags with f (-rf, -frf, -f)
            r'|'
            r'(?:-[a-zA-Z]+\s+)*'  # preceding flags without f (-r, -i, etc.)
            r'-[a-zA-Z]*f[a-zA-Z]*'  # the flag group containing f
            r')',
            re.IGNORECASE
        ),
        "rm -rf",
        "Recursive force removal (`rm -rf`) can delete entire filesystems irreversibly."
    ),
    (
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        "DROP TABLE",
        "`DROP TABLE` destroys an entire database table. This is irreversible without a backup."
    ),
    (
        re.compile(r'\bgit\s+push\s+--force\b', re.IGNORECASE),
        "git push --force",
        "`git push --force` overwrites remote history, potentially losing commits from collaborators."
    ),
    (
        re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
        "TRUNCATE",
        "`TRUNCATE` removes ALL rows from a table instantly. This cannot be rolled back in some databases."
    ),
    (
        re.compile(r'\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)', re.IGNORECASE | re.DOTALL),
        "DELETE FROM without WHERE",
        "`DELETE FROM` without a `WHERE` clause removes ALL rows from the table."
    ),
]

# Extra patterns that are suspicious but not in the core list
EXTRA_WARNINGS = [
    re.compile(r'\bchmod\s+-R\s+777\b', re.IGNORECASE),
    re.compile(r'\bmv\s+[^\s]+\s+/dev/null\b', re.IGNORECASE),
    re.compile(r'\bdd\s+if=[^\s]+\s+of=/dev/[a-z]+\b', re.IGNORECASE),
]


def get_blocked_log_path():
    """Get the path to the blocked.log file."""
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(hook_dir, "blocked.log")


def log_blocked(command, pattern_name, reason):
    """Log a blocked command attempt to blocked.log."""
    log_path = get_blocked_log_path()
    timestamp = datetime.utcnow().isoformat() + "Z"
    project_path = os.getcwd()
    
    log_entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "pattern": pattern_name,
        "reason": reason,
        "project_path": project_path,
    }
    
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Silently fail if logging is not possible
    
    return log_entry


def check_command(command):
    """
    Check a command string against dangerous patterns.
    Returns (is_dangerous, pattern_name, explanation, log_entry) or None if safe.
    """
    for pattern, name, explanation in DANGEROUS_PATTERNS:
        if pattern.search(command):
            log_entry = log_blocked(command, name, explanation)
            return True, name, explanation, log_entry
    
    # Check extra warnings (log but don't block)
    for pattern in EXTRA_WARNINGS:
        if pattern.search(command):
            # Just log, don't block
            log_blocked(command, "warning", f"Suspicious pattern matched: {pattern.pattern}")
    
    return None


def handle_pre_tool_use(input_data):
    """
    Handle a PreToolUse event.
    
    Expected input format:
    {
        "hookEventName": "PreToolUse",
        "toolCall": {
            "name": "Bash",
            "input": {
                "command": "the actual bash command"
            },
            "toolCallId": "call_xxx"
        },
        ...
    }
    """
    # Extract the tool call details
    tool_call = input_data.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_input = tool_call.get("input", {})
    command = ""
    
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
    elif isinstance(tool_input, str):
        command = tool_input
    
    # Only check Bash tool calls
    if tool_name != "Bash" or not command:
        return {"permissionDecision": "allow"}
    
    # Check for dangerous patterns
    result = check_command(command)
    
    if result is not None:
        is_dangerous, pattern_name, explanation, log_entry = result
        return {
            "permissionDecision": "deny",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecisionReason": (
                    f"🚫 BLOCKED by safety hook: detected '{pattern_name}'\n\n"
                    f"Reason: {explanation}\n\n"
                    f"Attempted command: `{command}`\n"
                    f"Logged to: {get_blocked_log_path()}\n\n"
                    f"If you need to run this command, use the CLI directly, "
                    f"or temporarily disable this hook."
                ),
            },
        }
    
    return {"permissionDecision": "allow"}


def main():
    """Main entry point: read JSON from stdin, write decision to stdout."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # No input, allow by default
            print(json.dumps({"permissionDecision": "allow"}))
            return
        
        input_data = json.loads(raw_input)
        result = handle_pre_tool_use(input_data)
        print(json.dumps(result))
    
    except json.JSONDecodeError as e:
        # If we can't parse the input, allow the command
        print(json.dumps({
            "permissionDecision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecisionReason": f"Warning: hook could not parse input ({e})",
            },
        }))
    except Exception as e:
        # Fail safe - allow the command if the hook itself has an error
        print(json.dumps({
            "permissionDecision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecisionReason": f"Warning: hook error: {e}",
            },
        }))


if __name__ == "__main__":
    main()
