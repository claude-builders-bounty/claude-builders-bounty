#!/usr/bin/env python3
"""Pre-tool-use hook: Blocks destructive bash commands before execution.

Claude Code fires this hook before ANY Bash tool use. Exit code 0 = allow,
exit code 2 = block (Claude-specific convention).

Reads tool input from $CLAUDE_TOOL_INPUT env var and/or stdin.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# ── Dangerous patterns ───────────────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    # rm -rf (any variant: rm -rf, rm -r -f, rm -fr, etc.)
    (r'\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*[rf]|-[a-zA-Z]*[rf]\s+-[a-zA-Z]*[rf])\b',
     "DESTRUCTIVE DELETE", "rm -rf or equivalent recursive-force removal detected"),

    # git push --force, git push -f, git push --force-with-lease
    (r'\bgit\s+push\b.*(?:--force|--force-with-lease|-f\b)',
     "FORCE PUSH", "git push --force detected — can overwrite remote history"),

    # DROP TABLE / DROP DATABASE
    (r'\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b',
     "DROP STATEMENT", "DROP TABLE/DATABASE/SCHEMA detected — irreversible schema destruction"),

    # TRUNCATE TABLE
    (r'\bTRUNCATE\s+(?:TABLE\s+)?',
     "TRUNCATE", "TRUNCATE detected — removes all rows without possibility of rollback in some engines"),

    # DELETE FROM without WHERE clause
    # Matches: DELETE FROM table; or DELETE FROM table WHERE (we ALLOW WHERE)
    # We match DELETE FROM and then check there's no WHERE
    (r'\bDELETE\s+FROM\s+\S+',
     "DELETE WITHOUT WHERE", None),  # Special: requires secondary check for WHERE absence
]


# ── Secondary checks ─────────────────────────────────────────────────────────

def has_no_where(command: str) -> bool:
    """Check if DELETE FROM lacks a WHERE clause."""
    upper = command.upper()
    # Find DELETE FROM and check if WHERE appears after it
    delete_pos = upper.find('DELETE FROM')
    if delete_pos == -1:
        return False
    after_delete = upper[delete_pos:]
    # Check if WHERE appears before a semicolon or end of string
    # Find the end of this statement (semicolon or EOS)
    semi_pos = after_delete.find(';')
    statement = after_delete[:semi_pos] if semi_pos != -1 else after_delete
    return 'WHERE' not in statement


# ── Main logic ────────────────────────────────────────────────────────────────

def get_tool_input() -> str:
    """Extract the bash command from Claude's tool input."""
    # Try env var first
    raw = os.environ.get('CLAUDE_TOOL_INPUT', '')
    if raw:
        try:
            data = json.loads(raw)
            # The bash command is typically in 'command' field
            if isinstance(data, dict):
                return data.get('command', raw)
            return raw
        except json.JSONDecodeError:
            return raw

    # Fallback: read from stdin
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data.get('command', raw)
                return raw
            except json.JSONDecodeError:
                return raw

    return ''


def block_command(pattern_name: str, message: str, command: str, project_dir: str):
    """Block a command: log it, print reason, exit 2."""
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Truncate command for clean logging
    truncated = command[:500] + '...' if len(command) > 500 else command

    # Log to file
    log_dir = os.path.expanduser('~/.claude/hooks')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'blocked.log')

    log_entry = (
        f"[{timestamp}] BLOCKED [{pattern_name}]\n"
        f"  Project: {project_dir}\n"
        f"  Command: {truncated}\n"
        f"  Reason:  {message}\n"
    )

    try:
        with open(log_path, 'a') as f:
            f.write(log_entry + '\n')
    except OSError:
        pass  # Don't fail hook because of logging failure

    # Print clear message for Claude
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  GUARDIAN: Destructive command BLOCKED", file=sys.stderr)
    print(f"  Type:    {pattern_name}", file=sys.stderr)
    print(f"  Reason:  {message}", file=sys.stderr)
    print(f"  Command: {truncated}", file=sys.stderr)
    print(f"  Logged:  {log_path}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    sys.exit(2)  # Claude Code convention: exit 2 = block the tool


def main():
    command = get_tool_input()
    if not command:
        sys.exit(0)  # Nothing to check, allow

    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

    for pattern, name, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Special handling for DELETE FROM: only block if no WHERE
            if name == 'DELETE WITHOUT WHERE':
                if has_no_where(command):
                    block_command(
                        name,
                        "DELETE FROM without WHERE clause — would delete ALL rows",
                        command,
                        project_dir,
                    )
                continue  # Has WHERE, allow it

            block_command(name, message, command, project_dir)

    sys.exit(0)  # All clear


if __name__ == '__main__':
    main()
