#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOKS_DIR = Path.home() / '.claude' / 'hooks'
LOG_FILE = HOOKS_DIR / 'blocked.log'

BLOCK_PATTERNS = [
    (re.compile(r'(^|[;&|]\s*|&&\s*)rm\s+-rf(\s|$)', re.IGNORECASE), 'rm -rf'),
    (re.compile(r'(^|[;&|]\s*|&&\s*)git\s+push\b[^\n\r;|&]*\s(--force-with-lease|--force|-f)(\s|$)', re.IGNORECASE), 'git push --force'),
    (re.compile(r'\bdrop\s+table\b', re.IGNORECASE), 'DROP TABLE'),
    (re.compile(r'\btruncate\b', re.IGNORECASE), 'TRUNCATE'),
]
DELETE_FROM_RE = re.compile(r'\bdelete\s+from\b', re.IGNORECASE)
WHERE_RE = re.compile(r'\bwhere\b', re.IGNORECASE)


def load_event():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {'raw': raw}


def extract_command(event):
    candidates = []
    if isinstance(event, dict):
        tool_name = event.get('tool_name') or event.get('tool') or event.get('name') or ''
        tool_input = event.get('tool_input') or event.get('input') or event.get('payload') or {}
        if isinstance(tool_input, dict):
            candidates.extend([
                tool_input.get('command'),
                tool_input.get('cmd'),
                tool_input.get('bash_command'),
                tool_input.get('script'),
            ])
        candidates.extend([
            event.get('command'),
            event.get('cmd'),
            event.get('bash_command'),
        ])
        return tool_name, next((c for c in candidates if isinstance(c, str) and c.strip()), '')
    return '', ''


def extract_project_path(event):
    if not isinstance(event, dict):
        return os.getcwd()
    for key in ('project_path', 'cwd', 'working_directory', 'workdir'):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value
    tool_input = event.get('tool_input') or event.get('input') or {}
    if isinstance(tool_input, dict):
        for key in ('cwd', 'workdir', 'project_path', 'working_directory'):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return os.getcwd()


def blocked_reason(command):
    for regex, label in BLOCK_PATTERNS:
        if regex.search(command):
            return label
    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return 'DELETE FROM without WHERE'
    return None


def log_block(project_path, command, reason):
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace('\n', '\\n')[:2000]
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(f'{timestamp} | {project_path} | {reason} | {safe_command}\n')


def allow():
    print(json.dumps({'action': 'allow'}))


def deny(reason, project_path, command):
    try:
        log_block(project_path, command, reason)
    except Exception:
        pass
    message = (
        f'Blocked dangerous bash command ({reason}). '
        f'This hook prevents destructive operations and logged the attempt to {LOG_FILE}.'
    )
    print(json.dumps({'action': 'deny', 'message': message}))


def main():
    event = load_event()
    tool_name, command = extract_command(event)

    if not command:
        allow()
        return

    if tool_name and 'bash' not in str(tool_name).lower() and 'shell' not in str(tool_name).lower():
        allow()
        return

    project_path = extract_project_path(event)
    reason = blocked_reason(command)
    if reason:
        deny(reason, project_path, command)
    else:
        allow()


if __name__ == '__main__':
    main()
