#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code - Blocks destructive bash commands

Bounty #3: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

Blocks dangerous patterns:
- rm -rf / rm -fr
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without WHERE clause

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # rm -rf patterns
    (r'\brm\s+-[rf]+\s+', "rm -rf: destructive file removal"),
    (r'\brm\s+--recursive\s+--force', "rm --recursive --force: destructive file removal"),
    
    # SQL destructive patterns
    (r'\bDROP\s+TABLE\b', "DROP TABLE: destructive SQL operation"),
    (r'\bTRUNCATE\s+TABLE?\b', "TRUNCATE: destructive SQL operation"),
    (r'\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE\b)', "DELETE FROM without WHERE: destructive SQL operation"),
    
    # Git force push
    (r'\bgit\s+push\b.*(--force|-f|\+force)', "git push --force: destructive git operation"),
]

def get_project_path():
    """Get current project directory if available"""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def log_blocked_command(command, reason, project_path):
    """Log blocked attempt to blocked.log"""
    log_dir = os.path.expanduser("~/.claude/hooks")
    log_file = os.path.join(log_dir, "blocked.log")
    
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    log_entry = f"{timestamp} | {command} | {project_path} | {reason}\n"
    
    with open(log_file, "a") as f:
        f.write(log_entry)

def check_command(command):
    """Check if command contains dangerous patterns"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, None

def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only check Bash tool
        if tool_name.lower() != "bash":
            # Allow all non-Bash tools
            output = {
                "decision": "approve",
                "reason": "Not a Bash command, no restrictions apply"
            }
            print(json.dumps(output))
            sys.exit(0)
        
        # Get the command
        command = tool_input.get("command", "")
        if not command:
            # Empty command, allow
            output = {
                "decision": "approve",
                "reason": "Empty command"
            }
            print(json.dumps(output))
            sys.exit(0)
        
        # Check for dangerous patterns
        is_dangerous, reason = check_command(command)
        
        if is_dangerous:
            # Log the blocked attempt
            project_path = get_project_path()
            log_blocked_command(command, reason, project_path)
            
            # Block the command
            output = {
                "decision": "reject",
                "reason": f"🚫 BLOCKED: {reason}. This command could cause irreversible damage. If you really need to run this, explain why and I can help you find a safer alternative."
            }
            print(json.dumps(output))
            sys.exit(2)  # Exit code 2 means reject
        else:
            # Allow safe commands
            output = {
                "decision": "approve",
                "reason": "Command appears safe"
            }
            print(json.dumps(output))
            sys.exit(0)
    
    except json.JSONDecodeError:
        # Invalid JSON input - fail-closed
        output = {
            "decision": "reject",
            "reason": "Invalid hook input format"
        }
        print(json.dumps(output))
        sys.exit(1)
    except Exception as e:
        # Unexpected error - fail-closed
        output = {
            "decision": "reject",
            "reason": f"Hook error: {str(e)}"
        }
        print(json.dumps(output))
        sys.exit(1)

if __name__ == "__main__":
    main()