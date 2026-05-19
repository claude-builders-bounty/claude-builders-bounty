#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Install: ln -s $(pwd)/pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use
"""

import json
import sys
import re
import os
from datetime import datetime

# Destructive patterns to block
DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s+', 'rm -rf: recursive force delete'),
    (r'git\s+push\s+.*--force', 'git push --force: force overwrite remote history'),
    (r'DROP\s+TABLE', 'DROP TABLE: database table deletion'),
    (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE: table data wipe'),
    (r'DELETE\s+FROM\s+\w+\s*;?\s*$', 'DELETE FROM without WHERE: unconditional row deletion'),
    (r'DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1', 'DELETE FROM with tautology: effectively unconditional deletion'),
    (r'mkfs\.', 'mkfs: filesystem format'),
    (r'dd\s+if=.*of=/dev/', 'dd to block device: raw disk overwrite'),
    (r'>\s*/dev/[sh]d[a-z]', 'redirect to block device: disk corruption'),
    (r':\(\)\{\s*:\|:\s*\&\s*\};\s*:', 'fork bomb: resource exhaustion attack'),
]

BLOCKED_LOG = os.path.expanduser('~/.claude/hooks/blocked.log')


def log_blocked(command: str, reason: str, project_path: str):
    """Log blocked attempt with timestamp."""
    os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(BLOCKED_LOG, 'a') as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  Command: {command.strip()}\n")
        f.write(f"  Project: {project_path}\n")
        f.write(f"  {'='*60}\n")


def main():
    # Claude Code passes tool call as JSON via stdin
    try:
        tool_call = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not a JSON input, allow through
        print(json.dumps({"allowed": True}))
        return

    tool_name = tool_call.get('tool', '')
    
    # Only intercept bash tool
    if tool_name != 'bash':
        print(json.dumps({"allowed": True}))
        return

    command = tool_call.get('command', '')
    project_path = tool_call.get('project_path', os.getcwd())
    
    # Check against dangerous patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, project_path)
            
            # Return structured response for Claude
            print(json.dumps({
                "allowed": False,
                "message": f"\n🛡️  COMMAND BLOCKED by safety hook\n\n"
                          f"Reason: {reason}\n"
                          f"Pattern matched: {pattern}\n\n"
                          f"Attempted command:\n```\n{command.strip()}\n```\n\n"
                          f"If you believe this is safe, you can:\n"
                          f"1. Rephrase the command to avoid the dangerous pattern\n"
                          f"2. Or run it manually outside of Claude Code\n\n"
                          f"Blocked attempts are logged to: {BLOCKED_LOG}"
            }))
            return
    
    # Safe command, allow through
    print(json.dumps({"allowed": True}))


if __name__ == '__main__':
    main()
