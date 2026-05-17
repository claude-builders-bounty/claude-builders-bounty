#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands
Bounty: $100 - https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

This hook intercepts dangerous bash commands before execution and blocks them.
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
 r'rm\s+-rf', # rm -rf
 r'rm\s+-fr', # rm -fr (alternate)
 r'rm\s+.*-.*r.*-.*f', # rm with mixed flags
 r'DROP\s+TABLE', # SQL DROP TABLE
 r'DROP\s+DATABASE', # SQL DROP DATABASE
 r'TRUNCATE\s+TABLE', # SQL TRUNCATE
 r'TRUNCATE\s+\w+', # SQL TRUNCATE (short form)
 r'git\s+push\s+.*--force', # git push --force
 r'git\s+push\s+.*-f\b', # git push -f
 r'DELETE\s+FROM\s+\w+\s*;', # DELETE FROM without WHERE
 r'DELETE\s+FROM\s+\w+\s*$', # DELETE FROM at end of line
 r'shred\s+', # shred command
 r'dd\s+if=.*of=/dev/', # dd to device
 r':(){:|:&};:', # Fork bomb
 r'mkfs\s+', # Format filesystem
 r'fdisk\s+', # Disk partitioning
]

# Log file path
LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def log_blocked_command(command: str, reason: str, project_path: str = ""):
 """Log blocked command to file."""
 LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
 
 timestamp = datetime.now().isoformat()
 log_entry = {
 "timestamp": timestamp,
 "command": command,
 "reason": reason,
 "project_path": project_path or os.getcwd()
 }
 
 with open(LOG_FILE, 'a', encoding='utf-8') as f:
 f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def check_command(command: str) -> tuple[bool, str]:
 """
 Check if command contains dangerous patterns.
 Returns: (is_dangerous, reason)
 """
 # Normalize command for checking
 command_upper = command.upper()
 
 for pattern in DANGEROUS_PATTERNS:
 if re.search(pattern, command, re.IGNORECASE):
 # Determine reason based on pattern
 if 'rm' in pattern.lower():
 return True, "Blocked: rm -rf or similar destructive file deletion"
 elif 'DROP' in pattern.upper():
 return True, "Blocked: SQL DROP statement (database/table deletion)"
 elif 'TRUNCATE' in pattern.upper():
 return True, "Blocked: SQL TRUNCATE statement (data deletion)"
 elif 'git' in pattern.lower():
 return True, "Blocked: git push --force (dangerous force push)"
 elif 'DELETE' in pattern.upper():
 return True, "Blocked: DELETE FROM without WHERE clause"
 elif 'shred' in pattern.lower():
 return True, "Blocked: shred command (secure file deletion)"
 elif 'dd' in pattern.lower():
 return True, "Blocked: dd to device (disk overwrite)"
 elif 'mkfs' in pattern.lower():
 return True, "Blocked: mkfs (filesystem format)"
 elif 'fdisk' in pattern.lower():
 return True, "Blocked: fdisk (disk partitioning)"
 else:
 return True, f"Blocked: matches dangerous pattern: {pattern}"
 
 return False, ""

def main():
 """
 Main hook function.
 
 Claude Code hooks receive JSON on stdin with the following structure:
 {
 "tool_name": "bash",
 "tool_input": {
 "command": "the command to execute"
 },
 "project_path": "/path/to/project"
 }
 
 The hook should output JSON on stdout:
 {
 "action": "allow" | "block",
 "message": "Explanation for Claude (shown if blocked)"
 }
 """
 try:
 # Read input from Claude Code
 input_data = json.load(sys.stdin)
 
 # Extract command
 tool_name = input_data.get('tool_name', '')
 tool_input = input_data.get('tool_input', {})
 command = tool_input.get('command', '')
 project_path = input_data.get('project_path', '')
 
 # Only check bash commands
 if tool_name != 'bash':
 output = {"action": "allow"}
 print(json.dumps(output))
 return
 
 # Check if command is dangerous
 is_dangerous, reason = check_command(command)
 
 if is_dangerous:
 # Log the blocked command
 log_blocked_command(command, reason, project_path)
 
 # Return block response
 output = {
 "action": "block",
 "message": f"🚫 {reason}\n\nThe command '{command}' was blocked for safety.\nThis attempt has been logged to ~/.claude/hooks/blocked.log"
 }
 else:
 # Allow the command
 output = {"action": "allow"}
 
 print(json.dumps(output))
 
 except Exception as e:
 # On error, allow the command (fail-safe)
 # But log the error for debugging
 error_output = {
 "action": "allow",
 "error": str(e)
 }
 print(json.dumps(error_output))

if __name__ == '__main__':
 main()
