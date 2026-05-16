#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Install: cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
"""

import json, sys, os, re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Dangerous patterns ──────────────────────────────────
DANGEROUS = [
    # Filesystem destruction
    (r'\brm\s+.*-r.*f\b',           'rm -rf (recursive force delete)'),
    (r'\brm\s+.*--recursive.*--force\b', 'rm --recursive --force'),
    (r'\brm\s+-rf\b',               'rm -rf (recursive force delete)'),
    (r'>\s*/dev/sd[a-z]',           'direct write to block device'),
    (r'\bdd\s+if=.*of=/dev/',       'dd to block device'),

    # Database destruction
    (r'\bDROP\s+TABLE\b',           'DROP TABLE (database table deletion)'),
    (r'\bTRUNCATE\s+(TABLE\s+)?',   'TRUNCATE (table data wipe)'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM without WHERE clause'),

    # Git force push
    (r'\bgit\s+push\s+.*(--force|-f)\b', 'git push --force'),
    (r'\bgit\s+push\s+.*--force-with-lease\b', 'git push --force-with-lease'),
    (r'\bgit\s+push\s+.*--delete\b', 'git push --delete (branch deletion)'),

    # Privilege escalation / system danger
    (r'\bchmod\s+777\b',            'chmod 777 (world-writable)'),
    (r'\bchmod\s+-R\s+777\b',       'chmod -R 777 (recursive world-writable)'),
    (r'\bchown\s+-R\b',             'chown -R (recursive ownership change)'),

    # Shell injection
    (r'curl\s+.*\|\s*(ba)?sh\b',   'curl piped to shell (potential malware)'),
    (r'wget\s+.*-O\s*-\s*\|\s*(ba)?sh\b', 'wget piped to shell'),
    (r'\beval\s+',                  'eval (arbitrary code execution)'),

    # Fork bombs / DoS
    (r':\(\)\s*\{',                 'fork bomb pattern'),
    (r'\b>\(\)\s*\{',               'fork bomb variant'),
]

def log_block(command, tool_input, cwd):
    """Log blocked attempt to file."""
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    project = cwd or os.getcwd()
    entry = {
        'timestamp': ts,
        'command': command,
        'project': project,
        'tool_input': tool_input,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_command(command):
    """Check command against dangerous patterns. Returns (blocked, reason)."""
    for pattern, reason in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, None

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No stdin? Allow by default
        print(json.dumps({"continue": True}))
        return

    tool_name = hook_input.get('tool_name', '')
    tool_input = hook_input.get('tool_input', {})
    cwd = hook_input.get('cwd', '')

    # Only intercept bash/terminal commands
    if tool_name not in ('bash', 'Bash', 'terminal'):
        print(json.dumps({"continue": True}))
        return

    command = tool_input.get('command', '') if isinstance(tool_input, dict) else str(tool_input)

    if not command:
        print(json.dumps({"continue": True}))
        return

    blocked, reason = check_command(command)

    if blocked:
        log_block(command, tool_input, cwd)
        result = {
            "continue": False,
            "decision": "block",
            "reason": f"🚫 Blocked dangerous command: {reason}\n\n"
                      f"Command: {command}\n"
                      f"This command matches a destructive pattern and was blocked "
                      f"by the pre-tool-use security hook.\n"
                      f"Logged to: {LOG_FILE}\n\n"
                      f"⚠️  If you genuinely need to run this command, "
                      f"temporarily disable the hook."
        }
    else:
        result = {"continue": True}

    print(json.dumps(result))

if __name__ == '__main__':
    main()
