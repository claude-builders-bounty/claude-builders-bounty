#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code that blocks destructive bash commands."""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r'rm\s+-rf', 'Blocked: rm -rf is destructive and can delete critical files'),
    (r'DROP\s+TABLE', 'Blocked: DROP TABLE permanently deletes database tables'),
    (r'git\s+push\s+--force', 'Blocked: git push --force can overwrite remote history'),
    (r'TRUNCATE', 'Blocked: TRUNCATE deletes all rows without logging'),
    (r'DELETE\s+FROM\s+.*(?!\s+WHERE\s+)', 'Blocked: DELETE FROM without WHERE deletes all rows'),
]

LOG_FILE = Path.home() / '.claude' / 'hooks' / 'blocked.log'

def log_blocked(command: str, reason: str, project_path: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f'{timestamp} | {project_path} | {command} | {reason}
')

def main():
    tool_call = json.load(sys.stdin)
    
    if tool_call.get('tool') != 'bash':
        print(json.dumps(tool_call))
        return
    
    command = tool_call.get('command', '')
    project_path = tool_call.get('project_path', str(Path.cwd()))
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, project_path)
            blocked_response = {
                'tool': 'bash',
                'command': f'echo "[BLOCKED] {reason}" && echo "Command was: {command}" && false',
                'project_path': project_path,
            }
            print(json.dumps(blocked_response))
            return
    
    print(json.dumps(tool_call))

if __name__ == '__main__':
    main()
