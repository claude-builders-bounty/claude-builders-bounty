#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
Blocks destructive bash commands before execution

Install: Copy to ~/.claude/hooks/pre-tool-use.py
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Configuration
BLOCKED_PATTERNS = [
    r'rm\s+-rf\s+',           # Delete recursively
    r'DROP\s+TABLE',          # Drop database table
    r'git\s+push\s+--force',  # Force push
    r'TRUNCATE',              # Truncate table
    r'DELETE\s+FROM\s+(?!\w+\s+WHERE)',  # Delete without WHERE
    r'--all\s+--force',       # Git force all
    r'rm\s+-\s*[rf]',        # rm -rf variations
    r'>\s*/dev/sd',           # Direct device write
    r':\(\)\{',               # Fork bomb
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command: str, project_path: str):
    """Log blocked command to file"""
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {command}\n")
        f.write(f"  Project: {project_path}\n\n")

def is_dangerous(command: str) -> bool:
    """Check if command matches any blocked pattern"""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def get_project_path() -> str:
    """Get current project path"""
    # Try to get from git repo
    try:
        result = os.popen("git rev-parse --show-toplevel 2>/dev/null").read().strip()
        if result:
            return result
    except:
        pass
    
    # Fallback to cwd
    return os.getcwd()

def main():
    # Read input from Claude Code
    input_data = sys.stdin.read()
    
    # Parse the command from input
    # Claude Code sends JSON with tool_name and tool_input
    
    if not input_data:
        sys.exit(0)  # No input, allow
    
    # Check if this is a bash command
    if '"bash"' in input_data or '"shell"' in input_data:
        # Extract command from input
        import json
        try:
            data = json.loads(input_data)
            command = data.get("command", "")
            
            if is_dangerous(command):
                project = get_project_path()
                log_blocked(command, project)
                
                # Block the command
                print("\n⚠️  BLOCKED: Destructive command detected!")
                print(f"   Command: {command[:80]}...")
                print(f"   Project: {project}")
                print(f"\n   This command matches a blocked pattern.")
                print(f"   See blocked.log for details.")
                
                # Exit with error to block
                sys.exit(1)
        except json.JSONDecodeError:
            pass
    
    sys.exit(0)

if __name__ == "__main__":
    main()