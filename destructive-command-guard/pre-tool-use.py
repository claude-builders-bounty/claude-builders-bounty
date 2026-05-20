#!/usr/bin/env python3
"""
PreToolUse hook: blocks destructive bash commands.

Reads JSON input from stdin (Claude Code PreToolUse event), checks if the
command matches dangerous patterns, and either allows (exit 0) or denies
(prints JSON decision to stdout and exits 0).

Blocked patterns:
  - rm -rf / --no-preserve-root variants
  - DROP TABLE / DROP DATABASE
  - git push --force / --force-with-lease (to main/master)
  - TRUNCATE TABLE
  - DELETE FROM without WHERE
  - chmod 777
  - :(){ :|:& };: (fork bomb)
  - > /dev/sda, dd if= of=/dev/
  - format C:, del /f /s (Windows destructive)

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import re
import sys
import os
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# ═════════════════════════════════════════════════════════════════════════════
# Pattern definitions
#
# Each pattern is (compiled_regex, category_name)
# We compile them once at module level for performance.
# ═════════════════════════════════════════════════════════════════════════════

def _compile(patterns):
    return [(re.compile(p, re.IGNORECASE), name) for p, name in patterns]

DANGEROUS_PATTERNS = _compile([
    # ─── rm -rf variants ───
    # rm with -r and -f flags (attached or space-separated)
    (r'\brm\b\s+.*(-r\S*f\S*|-f\S*r\S*|-r\s+-f\b|-f\s+-r\b|--recursive.*--force|--force.*--recursive)', 'rm -rf'),
    # rm -rf /  (root deletion — space + slash)
    (r'\brm\b\s+-[a-z-]*r[a-z-]*f[a-z-]*\s+/', 'rm -rf /'),
    # rm with --no-preserve-root
    (r'\brm\b\s+--no-preserve-root', 'rm -rf /'),

    # ─── Database destructive ───
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'DROP statement'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE'),
    (r'\bDELETE\s+FROM\s+\w+\s*[;$]?\s*$', 'DELETE without WHERE'),

    # ─── Git force push ───
    (r'\bgit\s+push\b.*(--force|--force-with-lease)', 'git push --force'),
    (r'\bgit\s+push\b(?!.*(--force|--force-with-lease)).*-f\b', 'git push -f'),

    # ─── Permissions ───
    (r'\bchmod\b.*\b777\b', 'chmod 777'),

    # ─── Fork bomb ───
    (r':\(\)\s*\{', 'fork bomb'),
    (r'\)\s*\{\s*:\|:&\s*\}', 'fork bomb'),

    # ─── Direct device write ───
    (r'\bdd\s+if=.*\bof=/dev/(sd|hd|nvme)', 'dd to block device'),
    (r'>\s*/dev/(sd|hd|nvme)', 'write to block device'),
    (r'\bmkfs\.', 'mkfs (filesystem format)'),

    # ─── Windows destructive ───
    (r'\bformat\s+[A-Z]:', 'format drive'),
    (r'\bdel\s+/[fF].*/[sS]', 'del /f /s (Windows recursive delete)'),
    (r'\brmdir\s+/[sS]', 'rmdir /s (Windows recursive remove)'),
])

# Commands often used in build/CI scripts that match patterns
# but are safe in those contexts
SAFE_OVERLAPS = [
    re.compile(r'\brm\b.*\bnode_modules\b', re.IGNORECASE),
    re.compile(r'\brm\b.*\b__pycache__\b', re.IGNORECASE),
    re.compile(r'\brm\b.*(?:^|\s)\.(next|cache|turbo|eslintcache)\b', re.IGNORECASE),
    re.compile(r'\brm\b.*\bdist\b', re.IGNORECASE),
    re.compile(r'\brm\b.*\bbuild\b', re.IGNORECASE),
    re.compile(r'\brm\b.*\b\.(o|obj|exe|dll)\b', re.IGNORECASE),
]


def is_safe_overlap(command):
    """Check if a matched command is actually a safe build/CI cleanup."""
    return any(p.search(command) for p in SAFE_OVERLAPS)


def check_command(command):
    """
    Check command against dangerous patterns.
    Returns list of (pattern_name, matched_text) tuples.
    """
    hits = []
    for pattern, name in DANGEROUS_PATTERNS:
        match = pattern.search(command)
        if match:
            hits.append((name, match.group(0)))

    if hits and is_safe_overlap(command):
        return []
    return hits


def log_blocked(command, patterns_found, project_path):
    """Log a blocked command attempt."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    pattern_list = ', '.join(p[0] for p in patterns_found)

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] BLOCKED | project={project_path} | '
                f'patterns=[{pattern_list}] | command="{command}"\n')


def allow():
    """Exit 0: command is allowed (no stdout needed)."""
    sys.exit(0)


def deny(command, patterns_found, project_path):
    """Print deny decision and exit 0 per Claude Code hooks spec."""
    pattern_list = ', '.join(p[0] for p in patterns_found)
    reason = (f"Destructive command blocked. Matched: {pattern_list}. "
              f"For details, check {LOG_FILE}")

    log_blocked(command, patterns_found, project_path)

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }
    print(json.dumps(decision), flush=True)
    sys.exit(0)


def main():
    # Read from stdin as raw bytes for cross-platform robustness
    # (avoids Windows GBK encoding issues)
    raw = sys.stdin.buffer.read()
    if not raw:
        allow()

    try:
        input_data = json.loads(raw.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        allow()

    command = input_data.get('tool_input', {}).get('command', '')
    project_path = input_data.get('project_path', '')

    if not command:
        allow()

    patterns_found = check_command(command)

    if patterns_found:
        deny(command, patterns_found, project_path)
    else:
        allow()


if __name__ == '__main__':
    main()
