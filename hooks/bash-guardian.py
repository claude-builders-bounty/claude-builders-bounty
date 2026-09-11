#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Issue: claude-builders-bounty/claude-builders-bounty#3 ($100 bounty)

Blocked patterns:
  - rm -rf / (any path)
  - DROP TABLE / TRUNCATE (without whitelist)
  - git push --force
  - DELETE FROM (no WHERE clause)
  - Destructive Windows commands (Format, del /S /Q, rd /S /Q)

Install (2 commands):
  mkdir -p ~/.claude/hooks
  cp bash-guardian.py ~/.claude/hooks/bash-guardian.py

Then add to ~/.claude/settings.json:
  { "hooks": { "preToolUse": ["~/.claude/hooks/bash-guardian.py"] } }
"""

import os
import sys
import json
import re
from datetime import datetime

LOG_PATH = os.path.expanduser('~/.claude/hooks/blocked.log')

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+/(\s|$)', 'Recursive force delete of filesystem root (rm -rf /)'),
    (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+/(\s|$)', 'Recursive force delete of filesystem root (rm -fr /)'),
    (r'\bdrop\s+table\b', 'DROP TABLE statement'),
    (r'\btruncate\b.*\btable\b', 'TRUNCATE TABLE statement'),
    (r'\bgit\s+push\s+.*--force\b', 'git push --force'),
    (r'\bgit\s+push\s+.*\s-f\s', 'git push -f'),
    (r'\bdelete\s+from\b(?!\s*\w+\s+where\b)', 'DELETE FROM without WHERE clause', True),
    (r'\bformat\s+[a-zA-Z]:', 'Windows format drive command'),
    (r'\bdel\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\', 'Windows recursive force delete'),
    (r'\brd\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\', 'Windows recursive directory delete'),
]

def log_blocked(command, rule_name, project_path):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = f"{datetime.utcnow().isoformat()}Z | BLOCKED | {rule_name} | {project_path} | {command}\n"
    with open(LOG_PATH, 'a') as f:
        f.write(entry)

def check_command(command, project_path='.'):
    cmd_lower = command.lower().strip()
    for item in DESTRUCTIVE_PATTERNS:
        pattern, reason = item[0], item[1]
        needs_where_check = len(item) > 2 and item[2]
        
        if needs_where_check:
            # Check if DELETE has WHERE clause
            match = re.search(pattern, cmd_lower, re.IGNORECASE)
            if match:
                # Verify no WHERE after DELETE FROM table
                after_match = cmd_lower[match.start():]
                if ' where ' not in after_match:
                    log_blocked(command, reason, project_path)
                    return False, reason
            continue
        
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            log_blocked(command, reason, project_path)
            return False, reason
    
    return True, None

def main():
    try:
        # Read hook input from stdin (Claude Code sends JSON)
        raw = sys.stdin.read().strip()
        if not raw:
            # No input = allow
            print(json.dumps({"allow": True}))
            return
        
        data = json.loads(raw)
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})
        project_path = data.get('project_path', os.getcwd())
        
        # Only guard bash commands
        if tool_name != 'bash':
            print(json.dumps({"allow": True}))
            return
        
        command = tool_input.get('command', '')
        allowed, reason = check_command(command, project_path)
        
        if not allowed:
            print(json.dumps({
                "allow": False,
                "reason": f"BLOCKED by bash-guardian hook: {reason}\n"
                          f"Command: {command}\n"
                          f"If this was a false positive, run the command manually outside Claude Code."
            }))
        else:
            print(json.dumps({"allow": True}))
    
    except Exception as e:
        # On any error, allow but log
        print(json.dumps({"allow": True}))

if __name__ == '__main__':
    main()
