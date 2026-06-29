#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime, timezone

# Blocked patterns with descriptive reasons
RULES = [
    {
        "name": "rm -rf",
        "patterns": [
            r'\brm\b.*\b-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b',
            r'\brm\b.*\b-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b',
            r'\brm\b.*\b-[a-zA-Z]*r\b.*\b-[a-zA-Z]*f\b',
            r'\brm\b.*\b-[a-zA-Z]*f\b.*\b-[a-zA-Z]*r\b',
            r'\brm\b.*\b--recursive\b.*\b--force\b',
            r'\brm\b.*\b--force\b.*\b--recursive\b'
        ],
        "reason": "Recursive force delete (rm -rf) is prohibited via Claude Code."
    },
    {
        "name": "DROP TABLE",
        "patterns": [
            r'\bDROP\s+TABLE\b',
            r'\bDROP\s+DATABASE\b'
        ],
        "reason": "DROP TABLE/DATABASE statements are prohibited via Claude Code."
    },
    {
        "name": "git push --force",
        "patterns": [
            r'\bgit\s+push\b.*\b--force(?![a-zA-Z0-9-])',
            r'\bgit\s+push\b.*\s+-f\b(?![a-zA-Z0-9-])'
        ],
        "reason": "Force push is prohibited via Claude Code. Use --force-with-lease instead."
    },
    {
        "name": "TRUNCATE",
        "patterns": [
            r'\bTRUNCATE\b'
        ],
        "reason": "TRUNCATE statements are prohibited via Claude Code."
    },
    {
        "name": "DELETE FROM without WHERE",
        "patterns": [
            r'\bDELETE\s+FROM\b'
        ],
        "reason": "DELETE FROM without a WHERE clause is prohibited via Claude Code."
    }
]

def check_command(command):
    # Check rm -rf variants
    # Only match if rm is the command name (following start of line or shell separators)
    if re.search(r'(?:^|[;&|])\s*(?:sudo\s+)?rm\b', command, re.IGNORECASE):
        # Check if the rm invocation contains both recursive and force flags
        # Find the portion of the command after rm until the next shell separator
        rm_part = re.split(r'[;&|]', command)[0] # simple split for first command, or let's search within the command
        # Better: find all rm command blocks and check them
        for part in re.split(r'[;&|]', command):
            if re.search(r'\b(?:sudo\s+)?rm\b', part, re.IGNORECASE):
                # Check for recursive and force
                has_recursive = re.search(r'(?:\s|^)-(?:[a-zA-Z]*r[a-zA-Z]*)(?![a-zA-Z0-9-])', part, re.IGNORECASE) or re.search(r'(?:\s|^)--recursive(?![a-zA-Z0-9-])', part, re.IGNORECASE)
                has_force = re.search(r'(?:\s|^)-(?:[a-zA-Z]*f[a-zA-Z]*)(?![a-zA-Z0-9-])', part, re.IGNORECASE) or re.search(r'(?:\s|^)--force(?![a-zA-Z0-9-])', part, re.IGNORECASE)
                if has_recursive and has_force:
                    return "Recursive force delete (rm -rf) is prohibited via Claude Code."

    # Check git push --force
    if re.search(r'(?:^|[;&|])\s*git\s+push\b', command, re.IGNORECASE):
        for part in re.split(r'[;&|]', command):
            if re.search(r'\bgit\s+push\b', part, re.IGNORECASE):
                # Check for --force or -f (avoiding --force-with-lease and --force-if-includes)
                if re.search(r'\s+--force(?![a-zA-Z0-9-])', part, re.IGNORECASE) or re.search(r'\s+-f(?![a-zA-Z0-9-])', part, re.IGNORECASE):
                    return "Force push is prohibited via Claude Code. Use --force-with-lease instead."

    # Check DROP TABLE / DROP DATABASE
    if re.search(r'\bDROP\s+(?:TABLE|DATABASE)\b', command, re.IGNORECASE):
        return "DROP TABLE/DATABASE statements are prohibited via Claude Code."

    # Check TRUNCATE
    if re.search(r'\bTRUNCATE\b', command, re.IGNORECASE):
        return "TRUNCATE statements are prohibited via Claude Code."

    # Check DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', command, re.IGNORECASE):
            return "DELETE FROM without a WHERE clause is prohibited via Claude Code."

    return None

def main():
    raw_input = ""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        data = {}

    tool_name = data.get('tool_name') or data.get('tool') or ''
    # If valid JSON was parsed but it's not bash/shell, let it pass
    if data and tool_name and tool_name.lower() not in ('bash', 'shell'):
        sys.exit(0)

    # Extract the command to check
    tool_input = data.get('tool_input') or data.get('input') or {}
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get('command') or ''
    elif isinstance(tool_input, str):
        command = tool_input

    if not command and not data:
        # Fallback to raw string input if JSON parsing failed
        command = raw_input.strip()

    if not command:
        sys.exit(0)

    reason = check_command(command)
    if reason:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        project_path = os.environ.get('CLAUDE_CWD') or os.getcwd()
        log_dir = os.path.expanduser('~/.claude/hooks')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'blocked.log')

        try:
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] BLOCKED | project={project_path} | cmd={command} | reason={reason}\n")
        except Exception as e:
            sys.stderr.write(f"Logging failed: {e}\n")

        # Output JSON response to stdout
        output = {
            "approved": False,
            "status": "error",
            "message": f"Blocked: {reason}",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }
        print(json.dumps(output, indent=2))

        # Output user message to stderr
        sys.stderr.write(f"\n⛔ Command blocked by pre-tool-use hook!\n")
        sys.stderr.write(f"Reason: {reason}\n")
        sys.stderr.write(f"Log: ~/.claude/hooks/blocked.log\n\n")

        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
