#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook - Dangerous Command Blocker

Blocks dangerous bash commands before execution:
- rm -rf (recursive force delete)
- DROP TABLE (SQL destruction)
- git push --force (force push)
- TRUNCATE (database truncation)
- DELETE FROM without WHERE clause

Logs blocked attempts to ~/.claude/hooks/blocked.log

Installation:
1. mkdir -p ~/.claude/hooks
2. cp claude-dangerous-command-hook.py ~/.claude/hooks/pre_tool_use.py
3. chmod +x ~/.claude/hooks/pre_tool_use.py

Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
"""

import sys
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    {
        "pattern": r"rm\s+(-[rf]+\s+)*(/|\*|~|\.\.?)",
        "name": "rm -rf (recursive force delete)",
        "severity": "CRITICAL",
        "message": "Blocked recursive force delete command"
    },
    {
        "pattern": r"rm\s+-rf",
        "name": "rm -rf",
        "severity": "CRITICAL",
        "message": "Blocked rm -rf command"
    },
    {
        "pattern": r"DROP\s+TABLE\s+(IF\s+EXISTS\s+)?\w+",
        "name": "DROP TABLE (SQL destruction)",
        "severity": "CRITICAL",
        "message": "Blocked SQL DROP TABLE command"
    },
    {
        "pattern": r"git\s+push\s+.*--force",
        "name": "git push --force",
        "severity": "HIGH",
        "message": "Blocked git force push"
    },
    {
        "pattern": r"TRUNCATE\s+(TABLE\s+)?\w+",
        "name": "TRUNCATE (database truncation)",
        "severity": "CRITICAL",
        "message": "Blocked TRUNCATE command"
    },
    {
        "pattern": r"DELETE\s+FROM\s+\w+(\s+WHERE\s+(?!1\s*=\s*1))?",
        "name": "DELETE FROM without WHERE",
        "severity": "CRITICAL",
        "message": "Blocked DELETE FROM without safe WHERE clause"
    },
    {
        "pattern": r"mkfs\.",
        "name": "mkfs (filesystem format)",
        "severity": "CRITICAL",
        "message": "Blocked filesystem format command"
    },
    {
        "pattern": r":\(\)\{\s*:\s*\|:\s*&\s*\}\s*;",
        "name": "Shell fork bomb",
        "severity": "CRITICAL",
        "message": "Blocked shell fork bomb"
    },
    {
        "pattern": r">\s*/dev/sd[a-z]",
        "name": "Direct disk write",
        "severity": "CRITICAL",
        "message": "Blocked direct disk write"
    },
    {
        "pattern": r"dd\s+.*of=/dev/",
        "name": "dd to device",
        "severity": "HIGH",
        "message": "Blocked dd to device command"
    },
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

def log_blocked(command: str, pattern_name: str, severity: str, message: str):
    """Log blocked command to blocked.log"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "pattern": pattern_name,
        "severity": severity,
        "message": message,
        "project_path": os.getcwd()
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def check_command(command: str) -> dict:
    """Check if command matches any dangerous pattern"""
    for pattern_info in DANGEROUS_PATTERNS:
        if re.search(pattern_info["pattern"], command, re.IGNORECASE):
            return {
                "blocked": True,
                "pattern": pattern_info["name"],
                "severity": pattern_info["severity"],
                "message": pattern_info["message"]
            }
    return {"blocked": False}

def main():
    """Main hook entry point"""
    # Read input from stdin (Claude Code hook protocol)
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not a valid JSON input, pass through
        print(json.dumps({"allow": True}))
        return
    
    # Extract command if this is a tool use
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Check bash/shell commands
    if tool_name in ["bash", "shell", "exec", "run_command"]:
        command = tool_input.get("command", "") or tool_input.get("cmd", "")
        
        if command:
            result = check_command(command)
            
            if result["blocked"]:
                # Log the blocked attempt
                log_blocked(
                    command,
                    result["pattern"],
                    result["severity"],
                    result["message"]
                )
                
                # Block the command
                print(json.dumps({
                    "allow": False,
                    "reason": f"🚫 {result['message']}\n"
                              f"Pattern: {result['pattern']}\n"
                              f"Severity: {result['severity']}\n"
                              f"Command: {command}\n\n"
                              f"This attempt has been logged to ~/.claude/hooks/blocked.log"
                }))
                return
    
    # Allow all other commands
    print(json.dumps({"allow": True}))

if __name__ == "__main__":
    main()
