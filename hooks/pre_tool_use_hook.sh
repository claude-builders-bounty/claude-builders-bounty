#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

When installed as a pre-tool-use hook, this script:
1. Intercepts bash commands before execution
2. Checks against known destructive patterns
3. Blocks dangerous commands and logs the attempt
4. Returns allow/deny decision with clear feedback

Usage with Claude Code:
1. Save this file as ~/.claude/hooks/pre_tool_use_hook.sh
2. Make executable: chmod +x ~/.claude/hooks/pre_tool_use_hook.sh
3. Add to hooks configuration or let Claude Code auto-detect
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

# Patterns to block (case-insensitive, ordered by severity)
BLOCKED_PATTERNS = [
    {
        "pattern": r"rm\s+-[A-Za-z]*r[A-Za-z]*f",
        "severity": "HIGH",
        "reason": "BLOCKED: Recursive delete (rm -rf) detected. This deletes files without confirmation.",
        "suggestion": "Use 'trash' command or move files to temp directory first"
    },
    {
        "pattern": r"rm\s+-[A-Za-z]*f.*-r[^a-zA-Z]",
        "severity": "HIGH",
        "reason": "BLOCKED: Force recursive delete detected.",
        "suggestion": "Use 'trash' command or move files to temp directory first"
    },
    {
        "pattern": r"(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
        "severity": "HIGH",
        "reason": "BLOCKED: SQL DROP statement detected. This permanently deletes database objects.",
        "suggestion": "Use transactions or backup before deletion"
    },
    {
        "pattern": r"(?i)\bTRUNCATE\s+",
        "severity": "HIGH", 
        "reason": "BLOCKED: TRUNCATE statement detected. Deletes all data without logging.",
        "suggestion": "Use DELETE with WHERE clause or transaction"
    },
    {
        "pattern": r"(?i)git\s+push\s+[^\n]*--force",
        "severity": "MEDIUM",
        "reason": "BLOCKED: Force push detected. Overwrites remote history.",
        "suggestion": "Use 'git push --force-with-lease' instead"
    },
    {
        "pattern": r"(?i)\bDELETE\s+FROM\s+\w+(?!\s+WHERE\b)",
        "severity": "HIGH",
        "reason": "BLOCKED: DELETE FROM without WHERE clause. Deletes all rows.",
        "suggestion": "Add WHERE clause to target specific rows"
    },
    {
        "pattern": r"(?i)\bsudo\s+rm\s+-rf\s+\/[^\w]",
        "severity": "CRITICAL",
        "reason": "BLOCKED: System deletion attempt (sudo rm -rf /). This would destroy the system.",
        "suggestion": "This command should NEVER be run"
    },
    {
        "pattern": r"(?i):\(\)\{[^}]*\}\s*;",
        "severity": "CRITICAL",
        "reason": "BLOCKED: Fork bomb syntax detected. System crash imminent.",
        "suggestion": "Remove this from your script"
    },
    {
        "pattern": r"(?i)\bsudo\s+mkfs",
        "severity": "HIGH",
        "reason": "BLOCKED: Filesystem format command detected. Erases all data on partition.",
        "suggestion": "Verify device path and consider backup first"
    },
    {
        "pattern": r"(?i)\bdd\s+if=",
        "severity": "MEDIUM",
        "reason": "BLOCKED: dd command detected. Can overwrite disk contents.",
        "suggestion": "Double-check input/output paths before using dd"
    }
]

# Log file configuration
LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

def find_matching_pattern(command):
    """Check command against all blocked patterns."""
    for rule in BLOCKED_PATTERNS:
        try:
            if re.search(rule["pattern"], command):
                return rule
        except re.error:
            continue
    return None

def check_command(command):
    """Main check function. Returns (blocked: bool, message: str)"""
    rule = find_matching_pattern(command)
    if rule:
        return False, f"{rule['reason']}\nSuggestion: {rule['suggestion']}"
    return True, "Command allowed: No destructive patterns detected."

def log_blocked_attempt(command, reason, project_path):
    """Log the blocked attempt to audit log."""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] "
        f"STATUS: BLOCKED | "
        f"SEVERITY: {reason.split('severity:', 1)[-1] if 'severity:' in reason else 'HIGH'} | "
        f"COMMAND: '{command}' | "
        f"PATH: {project_path}\n"
    )
    
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def main():
    """
    Main hook function.
    
    Reads command from stdin (either JSON from stdin or command line arg),
    checks against patterns, logs if blocked, and outputs decision.
    """
    command = ""
    project_path = os.getcwd()
    
    # Read input - Claude Code passes JSON to stdin with command info
    if not sys.stdin.isatty():
        try:
            input_data = sys.stdin.read().strip()
            if input_data:
                data = json.loads(input_data)
                command = data.get("command", "")
                project_path = data.get("cwd", os.getcwd())
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Fallback: read from first command line argument
    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    
    # Final fallback: just read stdin as the command
    if not command:
        command = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    if not command:
        print("ALLOW: No command provided")
        sys.exit(0)
    
    # Perform check
    allowed, message = check_command(command)
    
    if not allowed:
        # Log the blocked attempt
        log_blocked_attempt(command, message, project_path)
        
        # Output denial with clear message for Claude
        print(f"DENY: {message}")
        
        # Create a feedback file that Claude can see
        feedback_path = os.path.join(LOG_DIR, "feedback.md")
        with open(feedback_path, "w") as f:
            f.write(f"# Blocked Command\n\n")
            f.write(f"**Command:** `{command}`\n")
            f.write(f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}\n\n")
            f.write(f"{message}\n\n")
            f.write(f"Project: {project_path}\n")
        
        sys.exit(1)
    else:
        print(f"ALLOW: {message}")
        sys.exit(0)

if __name__ == "__main__":
    main()
