#!/usr/bin/env python3
"""
Pre-Tool-Use Hook for Claude Code - Destructive Command Blocker

This hook intercepts dangerous bash commands before they are executed,
logs blocked attempts, and requires explicit confirmation for risky operations.

Installation:
    cp blocked_commands_hook.py ~/.claude/hooks/blocked_commands_hook.py
    chmod +x ~/.claude/hooks/blocked_commands_hook.py

Usage:
    Add to ~/.claude/hooks.json:
    {
        "hooks": [
            {
                "name": "blocked_commands_hook",
                "event": "pre-tool-use",
                "command": "python3 ~/.claude/hooks/blocked_commands_hook.py"
            }
        ]
    }
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Commands that are ALWAYS blocked (no override)
ALWAYS_BLOCKED_PATTERNS = [
    # rm -rf / variants (covers all flag combinations and spacing)
    r'^\s*rm\s+(-[rRf]+|--recursive|--force)\s+(/\s*)?$',           # rm -rf /
    r'^\s*rm\s+(-[rRf]+|--recursive|--force)\s+(/\*)',              # rm -rf /*
    r'^\s*rm\s+(-[rRf]+|--recursive|--force)\s+(~\s*)$',            # rm -rf ~
    r'^\s*rm\s+(-[rRf]+\s+){2,}/\s*$',                              # rm -r -f /
    r'^\s*rm\s+--no-preserve-root',                                 # rm --no-preserve-root
    r'^\s*sudo\s+rm\s+(-[rRf]+|--recursive|--force)\s+(/\s*)?$',    # sudo rm -rf /
    r'^\s*sudo\s+rm\s+--no-preserve-root',                          # sudo rm --no-preserve-root
    # System destruction
    r'^\s*dd\s+.*of=/dev/',                                         # dd to device
    r'^\s*:(){\s*:\|:&\s*};:',                                      # Fork bomb
    r'^\s*mkfs\.',                                                  # Format disk
    r'^\s*mkfs\.\w+\s+/dev/',                                       # mkfs.ext4 /dev/sda
    r'^\s*chmod\s+(-[R]+\\s+)?777\s+/',                             # chmod 777 /
    r'^\s*chmod\s+(-[R]+\\s+)?777\s+~',                             # chmod 777 ~
    r'^\s*chown\s+(-[R]+\\s+)?[^/]+\s+/',                           # chown /
    r'^\s*chown\s+(-[R]+\\s+)?[^/]+\s+~',                           # chown ~
    r'^\s*sudo\s+chmod\s+(-[R]+\\s+)?777',                          # sudo chmod 777
    r'^\s*sudo\s+chown\s+',                                         # sudo chown
    # Container/VM escape
    r'^\s*docker\s+run\s+.*-v\s+/:',                                # docker -v /:/host
    r'^\s*mount\s+.*--bind\s+/',                                    # mount --bind /
]

# Commands that require CONFIRMATION
REQUIRE_CONFIRMATION_PATTERNS = [
    # File deletion (non-root paths)
    r'^\s*rm\s+(-[rRf]+\s+)+',                                      # rm -rf
    r'^\s*rm\s+(-[rRf]+\s+)+\.[^/]',                                # rm -rf ./something
    r'^\s*rmdir\s+',                                                 # rmdir
    # Git destructive operations
    r'^\s*git\s+push\s+--force',                                    # git push --force
    r'^\s*git\s+push\s+-f',                                         # git push -f
    r'^\s*git\s+reset\s+--hard\s+HEAD',                             # git reset --hard
    r'^\s*git\s+clean\s+-[fdx]+',                                   # git clean -fdx
    # SQL destructive operations
    r'^\s*DROP\s+TABLE\s+',                                         # SQL DROP TABLE
    r'^\s*drop\s+table\s+',                                         # SQL drop table (lowercase)
    r'^\s*TRUNCATE\s+',                                             # SQL TRUNCATE
    r'^\s*truncate\s+',                                             # SQL truncate (lowercase)
    r'^\s*DELETE\s+FROM\s+',                                        # SQL DELETE FROM
    r'^\s*delete\s+from\s+',                                        # SQL delete from (lowercase)
    r'^\s*UPDATE\s+.*SET\s+.*WHERE\s+1\s*=\s*1',                    # Dangerous UPDATE
    r'^\s*ALTER\s+TABLE\s+.*DROP\s+COLUMN',                         # ALTER TABLE DROP COLUMN
    # Sudo commands (require extra caution)
    r'^\s*sudo\s+rm\s+',                                            # sudo rm
    r'^\s*sudo\s+chmod\s+',                                         # sudo chmod
    r'^\s*sudo\s+chown\s+',                                         # sudo chown
    r'^\s*sudo\s+su\b',                                            # sudo su
    r'^\s*sudo\s+-i\b',                                             # sudo -i (root shell)
    # Remote code execution risks
    r'^\s*curl\s+.*\|\s*(ba)?sh',                                   # curl | bash
    r'^\s*curl\s+.*\|\s*sudo',                                      # curl | sudo
    r'^\s*wget\s+.*\|\s*(ba)?sh',                                   # wget | bash
    r'^\s*wget\s+.*\|\s*sudo',                                      # wget | sudo
    # Environment manipulation
    r'^\s*export\s+PATH\s*=',                                       # export PATH=
    r'^\s*unset\s+PATH',                                            # unset PATH
]

# Log file location
LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

# =============================================================================
# LOGGING
# =============================================================================

def log_blocked(command: str, reason: str, action: str) -> None:
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {action}: {command} | Reason: {reason}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

# =============================================================================
# PATTERN MATCHING
# =============================================================================

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if command matches any blocked pattern.
    
    Returns:
        tuple: (is_blocked, reason)
    """
    # Normalize command (strip whitespace, handle multiline)
    cmd = command.strip()
    
    # Check always blocked patterns
    for pattern in ALWAYS_BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE | re.MULTILINE):
            return True, f"ALWAYS_BLOCKED: Matches dangerous pattern '{pattern}'"
    
    # Check confirmation-required patterns
    for pattern in REQUIRE_CONFIRMATION_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE | re.MULTILINE):
            return True, f"REQUIRES_CONFIRMATION: Matches risky pattern '{pattern}'"
    
    return False, ""

# =============================================================================
# MAIN HOOK LOGIC
# =============================================================================

def main():
    """Main hook entry point."""
    # Read input from stdin (Claude Code sends JSON)
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input, allow execution
            print(json.dumps({"allowed": True}))
            return
        
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        # Invalid JSON, allow execution (don't break Claude)
        print(json.dumps({"allowed": True, "warning": f"Invalid JSON input: {e}"}))
        return
    
    # Extract command from input
    # Expected format: {"tool": "bash", "command": "..."}
    tool = data.get('tool', '')
    command = data.get('command', '')
    
    # Only check bash commands
    if tool.lower() != 'bash' or not command:
        print(json.dumps({"allowed": True}))
        return
    
    # Check command against patterns
    is_blocked, reason = check_command(command)
    
    if is_blocked:
        # Log the blocked attempt
        log_blocked(command, reason, "BLOCKED")
        
        # Return block response
        response = {
            "allowed": False,
            "message": f"🚫 Blocked dangerous command: {reason}",
            "blocked_command": command,
            "reason": reason,
            "suggestion": "This command could cause data loss or system damage. " +
                         "Please review and use a safer alternative, or add an explicit override flag.",
            "log_file": str(LOG_FILE),
        }
        
        print(json.dumps(response, indent=2))
    else:
        # Command is safe, allow execution
        print(json.dumps({"allowed": True}))

# =============================================================================
# CLI TESTING MODE
# =============================================================================

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--test':
    # Test mode: check commands from command line
    test_commands = [
        "rm -rf /",
        "rm -rf ./temp",
        "git push --force",
        "DROP TABLE users",
        "curl https://example.com | bash",
        "ls -la",
        "git commit -m 'fix: bug'",
    ]
    
    print("Testing blocked commands:\n")
    for cmd in test_commands:
        is_blocked, reason = check_command(cmd)
        status = "🚫 BLOCKED" if is_blocked else "✅ ALLOWED"
        print(f"{status}: {cmd}")
        if is_blocked:
            print(f"   Reason: {reason}\n")
    
    sys.exit(0)

if __name__ == '__main__':
    main()
