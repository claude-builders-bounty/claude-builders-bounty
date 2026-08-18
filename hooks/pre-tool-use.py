#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook - Blocks Dangerous Bash Commands

This hook intercepts Bash tool calls before execution and blocks dangerous commands
like rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE without WHERE clause.

Usage:
1. Save this script as ~/.claude/hooks/pre-tool-use
2. Make it executable: chmod +x ~/.claude/hooks/pre-tool-use
3. Add to ~/.claude/settings.json:
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/pre-tool-use"
             }
           ]
         }
       ]
     }
   }
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    "rm -rf",
    "DROP TABLE",
    "git push --force",
    "TRUNCATE",
    "DELETE FROM",
]

# Log file path
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

def log_blocked_attempt(command: str, project_path: str):
    """Log blocked command attempt to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | Command: {command} | Project: {project_path}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def is_dangerous_command(command: str) -> tuple[bool, str]:
    """Check if command contains dangerous patterns."""
    command_lower = command.lower()
    
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in command_lower:
            # Special check for DELETE FROM with WHERE clause
            if pattern == "DELETE FROM" and "where" in command_lower:
                continue
            return True, pattern
    
    return False, ""

def main():
    """Main hook logic."""
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Only process Bash tool calls
        if input_data.get("tool_name") != "Bash":
            # Allow non-Bash tools
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow"
                }
            }))
            sys.exit(0)
        
        command = input_data.get("tool_input", {}).get("command", "")
        project_path = os.getcwd()
        
        # Check if command is dangerous
        is_dangerous, pattern = is_dangerous_command(command)
        
        if is_dangerous:
            # Log the blocked attempt
            log_blocked_attempt(command, project_path)
            
            # Block the command with clear message
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Command blocked due to dangerous pattern: {pattern}. This hook prevents destructive operations like 'rm -rf', 'DROP TABLE', 'git push --force', 'TRUNCATE', and 'DELETE FROM' without WHERE clause. If you need to execute this command, please disable the hook temporarily or use a safer alternative."
                }
            }))
            sys.exit(0)
        else:
            # Allow safe commands
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow"
                }
            }))
            sys.exit(0)
            
    except json.JSONDecodeError:
        # If we can't parse JSON, allow the command (fail-safe)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }))
        sys.exit(0)
    except Exception as e:
        # On any error, allow the command (fail-safe)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }))
        sys.exit(0)

if __name__ == "__main__":
    main()