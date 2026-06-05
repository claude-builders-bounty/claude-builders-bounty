#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Install: copy to ~/.claude/hooks/block-destructive.py
"""
import sys, json, os, re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

PATTERNS = [
    # rm -rf variations
    (re.compile(r'\brm\s+.*-r[^a-zA-Z0-9]*f\b'), "rm -rf"),
    (re.compile(r'\brm\s+.*-rf\b'), "rm -rf"),
    (re.compile(r'\brm\s+-rf\b'), "rm -rf"),
    # Force push
    (re.compile(r'\bgit\s+push\s+.*(--force|-f)\b'), "git push --force"),
    (re.compile(r'\bgit\s+push\s+--force-with-lease\b.*'), "git push --force-with-lease"),
    # SQL destructive
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE"),
    (re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), "TRUNCATE"),
    (re.compile(r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', re.IGNORECASE), "DELETE FROM without WHERE"),
    # Dangerous redirects
    (re.compile(r'>\s*/dev/sda\b'), "redirect to block device"),
    (re.compile(r'\bchmod\s+777\b'), "chmod 777"),
    # Fork bomb
    (re.compile(r':\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:'), "fork bomb"),
]

INTERVENTION_MSG = """
⚠️ DESTRUCTIVE COMMAND BLOCKED
This command was intercepted by the safety hook because it matches a destructive pattern.
The command was NOT executed. Please use a safer alternative.
"""

def log_block(command, cwd, pattern_name):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        f.write(f"[{ts}] BLOCKED '{pattern_name}' | cwd={cwd} | cmd={command}\n")

def main():
    try:
        data = json.load(sys.stdin)
    except:
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    cwd = tool_input.get('cwd', os.getcwd()) if isinstance(tool_input, dict) else ''

    if tool_name != 'Bash':
        sys.exit(0)

    command = ''
    if isinstance(tool_input, dict):
        command = tool_input.get('command', '')
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        sys.exit(0)

    for pattern, name in PATTERNS:
        if pattern.search(command):
            log_block(command, cwd, name)
            print(INTERVENTION_MSG.strip(), file=sys.stderr)
            print(f"Blocked pattern: {name}", file=sys.stderr)
            print(f"Log: {LOG_FILE}", file=sys.stderr)
            sys.exit(2)  # Block execution

    sys.exit(0)

if __name__ == '__main__':
    main()
