#!/usr/bin/env bash
# pre-tool-use hook for Claude Code
# Blocks destructive bash commands before execution
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

set -euo pipefail

# Read the tool use event from stdin
INPUT=$(cat)

# Extract the command from the input JSON
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'tool_input' in data:
        cmd = data['tool_input'].get('command', '') or data['tool_input'].get('content', '')
        print(cmd)
    elif 'command' in data:
        print(data['command'])
    else:
        print(json.dumps(data))
except:
    print('')
" 2>/dev/null)

# Check dangerous patterns using python for reliable regex
BLOCKED=false
MATCHED_PATTERN=""
LOG_DIR="$HOME/.claude/hooks"
mkdir -p "$LOG_DIR"

RESULT=$(echo "$COMMAND" | python3 -c "
import re, sys, json, os, datetime

command = sys.stdin.read().strip()
if not command:
    sys.exit(0)

patterns = {
    'rm -rf': r'rm\s+-[a-zA-Z]*f[a-zA-Z]*\s+/',
    'rm -rf (variant)': r'rm\s+--recursive\s+--force',
    'DROP TABLE': r'DROP\s+TABLE',
    'TRUNCATE': r'TRUNCATE\s+(TABLE\s+)?\w+',
    'DELETE without WHERE': r'DELETE\s+FROM\s+\S+(?!\s+WHERE\s+)',
    'git push --force': r'git\s+push\s+(-f\b|--force\b)',
    'dd to device': r'dd\s+.*of=/dev/',
    'mkfs': r'mkfs\.',
    'fork bomb': r':\(\)\s*\{\s*:\|\s*&\s*\}',
    'chmod 777 root': r'chmod\s+-R\s+777\s+/',
    'chown root': r'chown\s+-R\s+\S+\s+/',
    'wipefs': r'wipefs\s+-a\s+/dev/',
    '> /dev/sda': r'>\s*/dev/[sh]d[a-z]',
}

blocked = False
matched = ''

for name, pattern in patterns.items():
    if re.search(pattern, command, re.IGNORECASE):
        blocked = True
        matched = name
        break

if blocked:
    # Log the blocked attempt
    log_dir = os.path.expanduser('~/.claude/hooks')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    project_path = os.getcwd()
    log_entry = json.dumps({
        'timestamp': timestamp,
        'command': command,
        'project_path': project_path,
        'matched_pattern': matched
    })
    with open(os.path.join(log_dir, 'blocked.log'), 'a') as f:
        f.write(log_entry + '\n')
    
    # Output block decision
    response = {
        'decision': 'block',
        'reason': f'🚫 BLOCKED by pre-tool-use safety hook: command matched dangerous pattern \"{matched}\". Destructive commands (rm -rf, DROP TABLE, TRUNCATE, DELETE without WHERE, git push --force, dd to device, etc.) are not allowed. If you truly need to run this, ask for explicit approval.'
    }
    print(json.dumps(response))
else:
    print(json.dumps({'decision': 'allow'}))
" 2>/dev/null)

if [ -n "$RESULT" ]; then
    echo "$RESULT"
fi
