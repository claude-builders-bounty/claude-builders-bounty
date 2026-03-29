#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Security Guard
Blocks destructive bash commands before execution.
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Critical system directories that should never be deleted
SYSTEM_DIRS = r"(?:/|/bin|/boot|/dev|/etc|/home|/lib|/lib64|/mnt|/opt|/proc|/root|/run|/sbin|/srv|/sys|/usr|/var)"

BLOCKED_PATTERNS = [
    {
        "pattern": r"^\s*rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]+\s+)*\/\s*$|^\s*rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]+\s+)*\/\s",
        "description": "Destructive deletion of root filesystem (rm -rf /)",
        "severity": "CRITICAL"
    },
    {
        "pattern": rf"^\s*rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]+\s+)*{SYSTEM_DIRS}(?:\/|\s|$)",
        "description": "Destructive deletion of critical system directories",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"DROP\s+TABLE\s+\w+",
        "description": "Database table deletion (DROP TABLE)",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"DROP\s+DATABASE\s+\w+",
        "description": "Database deletion (DROP DATABASE)",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"TRUNCATE\s+TABLE\s+\w+",
        "description": "Table truncation (TRUNCATE)",
        "severity": "HIGH"
    },
    {
        "pattern": r"DELETE\s+FROM\s+\w+\s*$|DELETE\s+FROM\s+\w+\s+;\s*$",
        "description": "Mass deletion without WHERE clause",
        "severity": "HIGH"
    },
    {
        "pattern": r"git\s+push\s+.*(--force\s+|-f\s+|--force$|-f$)",
        "description": "Force push (git push --force)",
        "severity": "MEDIUM"
    },
    {
        "pattern": r"\>\s*\/\w+\.(db|sqlite|sql)",
        "description": "Database overwrite with redirection",
        "severity": "HIGH"
    },
    {
        "pattern": r"mkfs\.",
        "description": "Disk formatting",
        "severity": "CRITICAL"
    },
    {
        "pattern": r"dd\s+if=.*of=\/dev\/",
        "description": "Direct disk write (dd to /dev/)",
        "severity": "CRITICAL"
    }
]

SAFE_PATTERNS = [
    r"--dry-run",
    r"--force-with-lease",
]

def log_blocked_attempt(command: str, matched_pattern: dict, project_path: str):
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    
    timestamp = datetime.now().isoformat()
    log_entry = (
        f"[{timestamp}]\n"
        f"  SEVERITY: {matched_pattern['severity']}\n"
        f"  PATTERN: {matched_pattern['description']}\n"
        f"  COMMAND: {command}\n"
        f"  PROJECT: {project_path}\n"
        f"  ACTION: BLOCKED\n"
        f"{'='*60}\n"
    )
    
    with open(log_file, "a") as f:
        f.write(log_entry)
    
    return log_file

def is_safe_command(command: str) -> bool:
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def check_command(command: str, project_path: str = "unknown"):
    if is_safe_command(command):
        return True, None
    
    for blocked in BLOCKED_PATTERNS:
        if re.search(blocked["pattern"], command, re.IGNORECASE):
            log_blocked_attempt(command, blocked, project_path)
            return False, blocked
    
    return True, None

def main():
    try:
        tool_input = json.load(sys.stdin)
        command = tool_input.get("command", "")
        project_path = tool_input.get("working_directory", str(Path.cwd()))
        
        is_safe, blocked = check_command(command, project_path)
        
        if not is_safe:
            message = f"""
⚠️  SECURITY HOOK BLOCKED DANGEROUS COMMAND

Detected: {blocked['description']}
Severity: {blocked['severity']}

Command: {command}

This command has been blocked to prevent potential data loss or system damage.

If you believe this is a false positive:
1. Review the command carefully
2. Consider using a safer alternative
3. Contact your system administrator

Blocked attempt logged to: ~/.claude/hooks/blocked.log
"""
            print(message, file=sys.stderr)
            sys.exit(1)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        sys.exit(0)
    except Exception as e:
        print(f"Hook error (allowing command): {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
