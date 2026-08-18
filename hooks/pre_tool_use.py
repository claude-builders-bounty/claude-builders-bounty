#!/usr/bin/env python3
"""
pre_tool_use.py - Claude Code PreToolUse hook that blocks destructive bash commands.

Reads a hook event from stdin as JSON (Claude Code PreToolUse format).
If the event describes a Bash tool invocation whose command matches a
known-destructive pattern, the hook exits with code 2 and prints a JSON
block response to stdout.  Otherwise it exits with code 0 and prints a
JSON allow response.

Blocked attempts are appended to ~/.claude/hooks/blocked.log.

This is a safety hook, NOT a shell sandbox.  It only inspects the command
string and cannot prevent all forms of data loss.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Destructive patterns (simple regex-only checks)
# ---------------------------------------------------------------------------
DESTRUCTIVE_PATTERNS = [
    (
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        'DROP TABLE is blocked',
    ),
    (
        re.compile(r'\bgit\s+push\b.*--force\b(?!-with-lease)', re.IGNORECASE),
        'git push --force is blocked (use --force-with-lease instead)',
    ),
    (
        re.compile(r'\bgit\s+push\b.*\s-f\b(?!orce-with-lease)', re.IGNORECASE),
        'git push -f is blocked (use --force-with-lease instead)',
    ),
]

# ---------------------------------------------------------------------------
# TRUNCATE detection helpers
# ---------------------------------------------------------------------------
_TRUNCATE_BARE_RE = re.compile(
    r'(?:^|(?<=[\s;]))TRUNCATE\s+(?:TABLE\s+)?\w', re.IGNORECASE
)
_TRUNCATE_CLIENT_RE = re.compile(
    r'(?:psql|mysql|sqlite3|sqlplus)\s+.*?TRUNCATE\s+(?:TABLE\s+)?\w',
    re.IGNORECASE,
)
_TRUNCATE_ECHO_GUARD_RE = re.compile(
    r'^(echo|cat|printf)\b', re.IGNORECASE
)


def _check_truncate(command):
    """Block TRUNCATE SQL while avoiding false positives on echo/cat prose.

    Strategy:
    1. If the command starts with echo/cat/printf, skip TRUNCATE detection
       (these are text-output commands, not SQL executors).
    2. Match bare TRUNCATE at start of string or after whitespace/semicolon.
    3. Match TRUNCATE inside known SQL client invocations.
    """
    stripped = command.strip()
    if _TRUNCATE_ECHO_GUARD_RE.match(stripped):
        return False, None
    if _TRUNCATE_BARE_RE.search(command):
        return True, 'TRUNCATE is blocked'
    if _TRUNCATE_CLIENT_RE.search(command):
        return True, 'TRUNCATE is blocked'
    return False, None


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _get_log_dir():
    home = os.path.expanduser('~')
    return os.path.join(home, '.claude', 'hooks')


def _get_log_path():
    return os.path.join(_get_log_dir(), 'blocked.log')


def log_blocked(command, project_path=None):
    log_dir = _get_log_dir()
    log_path = _get_log_path()
    try:
        os.makedirs(log_dir, mode=0o700, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = '[{}] BLOCKED command={!r}'.format(timestamp, command)
        if project_path:
            entry += ' project={!r}'.format(project_path)
        entry += '\n'
        with open(log_path, 'a', encoding='utf-8') as fh:
            fh.write(entry)
    except OSError as exc:
        print(json.dumps({'error': 'blocked-log write failed: {}'.format(exc)}),
              file=sys.stderr)


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

def _is_bash_event(event):
    tool_name = event.get('tool_name', '')
    return tool_name.lower() == 'bash'


def _get_command(event):
    tool_input = event.get('tool_input')
    if isinstance(tool_input, dict):
        cmd = tool_input.get('command', '')
        if cmd:
            return str(cmd)
    args = event.get('arguments', {})
    if isinstance(args, dict):
        cmd = args.get('command', '')
        if cmd:
            return str(cmd)
    if isinstance(args, (list, tuple)) and args:
        return str(args[0])
    return ''


def _get_project_path(event):
    cwd = event.get('cwd')
    if cwd:
        return str(cwd)
    pp = event.get('project_path')
    if pp:
        return str(pp)
    return os.getcwd()


# ---------------------------------------------------------------------------
# rm -rf detection
# ---------------------------------------------------------------------------
_RM_CMD_RE = re.compile(r'\brm\b', re.IGNORECASE)
_RM_FLAG_RE = re.compile(r'\brm\s+((?:-[a-zA-Z]+\s*)+(?:\S+\s*)*)', re.IGNORECASE)


def _check_rm_rf(command):
    if not _RM_CMD_RE.search(command):
        return False, None
    m = _RM_FLAG_RE.search(command)
    if not m:
        return False, None
    flag_segment = m.group(1)
    flags = re.findall(r'-([a-zA-Z]+)', flag_segment)
    if not flags:
        return False, None
    for flag in flags:
        if 'r' in flag and 'f' in flag:
            return True, 'rm with -rf (recursive force delete) is blocked'
    all_chars = set()
    for flag in flags:
        all_chars.update(flag)
    if 'r' in all_chars and 'f' in all_chars:
        return True, 'rm with -rf (recursive force delete) is blocked'
    return False, None


# ---------------------------------------------------------------------------
# DELETE FROM without WHERE detection
# ---------------------------------------------------------------------------
_DELETE_FROM_RE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
_WHERE_RE = re.compile(r'\bWHERE\b', re.IGNORECASE)


def _check_delete_no_where(command):
    if not _DELETE_FROM_RE.search(command):
        return False, None
    segments = re.split(r'[;\n]', command)
    for segment in segments:
        if _DELETE_FROM_RE.search(segment) and not _WHERE_RE.search(segment):
            return True, 'DELETE FROM without WHERE clause is blocked'
    return False, None


# ---------------------------------------------------------------------------
# Main check entry point
# ---------------------------------------------------------------------------

def check_command(command):
    blocked, reason = _check_rm_rf(command)
    if blocked:
        return True, reason
    blocked, reason = _check_delete_no_where(command)
    if blocked:
        return True, reason
    blocked, reason = _check_truncate(command)
    if blocked:
        return True, reason
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, None


# ---------------------------------------------------------------------------
# Event handler
# ---------------------------------------------------------------------------

def handle_event(event):
    if not _is_bash_event(event):
        return 0, {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'allow',
            }
        }
    command = _get_command(event)
    if not command:
        return 0, {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'allow',
            }
        }
    blocked, reason = check_command(command)
    if blocked:
        project_path = _get_project_path(event)
        log_blocked(command, project_path)
        return 2, {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': reason,
            }
        }
    return 0, {
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'allow',
        }
    }




# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'allow',
            }
        }))
        sys.exit(0)
    exit_code, response = handle_event(event)
    print(json.dumps(response))
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
