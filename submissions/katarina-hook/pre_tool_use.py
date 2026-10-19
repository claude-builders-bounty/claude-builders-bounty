#!/usr/bin/env python3
"""Conservative destructive-command guard, not a shell security sandbox."""
import datetime
import json
import pathlib
import re
import shlex
import sys


def reason(command):
    # Keep statement boundaries: a WHERE in a later statement cannot protect DELETE.
    try:
        payloads = shlex.split(command)
    except ValueError:
        payloads = []
    sql_source = '\n'.join(t for t in payloads if re.search(r'\b(?:DELETE|DROP|TRUNCATE)\b', t, re.I) and ' ' in t) or command
    sql = re.sub(r"/\*.*?\*/|--[^\n]*", " ", sql_source, flags=re.S)
    sql = re.sub(r"'([^']|'')*'", "''", sql)
    for statement in sql.split(';'):
        if re.search(r'\bDROP\s+TABLE\b', statement, re.I):
            return 'DROP TABLE removes a table.'
        if re.search(r'\bTRUNCATE\b', statement, re.I):
            return 'TRUNCATE removes all rows.'
        for match in re.finditer(r'\bDELETE\s+FROM\b', statement, re.I):
            if not re.search(r'\bWHERE\b', statement[match.end():], re.I):
                return 'DELETE FROM requires a WHERE clause in the same statement.'
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()')
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return 'Cannot safely inspect malformed shell quoting.'
    for i, token in enumerate(tokens):
        name = pathlib.PurePosixPath(token).name
        if name == 'rm':
            flags = ''
            for arg in tokens[i + 1:]:
                if arg == '--' or arg in (';', '&&', '||', '|'):
                    break
                if arg.startswith('--'):
                    flags += {'--recursive': 'r', '--force': 'f'}.get(arg, '')
                elif arg.startswith('-'):
                    flags += arg[1:]
            if 'f' in flags and ('r' in flags or 'R' in flags):
                return 'Recursive forced deletion is blocked.'
        if name == 'git':
            segment = []
            for arg in tokens[i + 1:]:
                if arg in (';', '&&', '||', '|'):
                    break
                segment.append(arg)
            if 'push' in segment and any(a in ('--force', '-f') or a.startswith('--force=') or (a.startswith('-') and not a.startswith('--') and 'f' in a[1:]) for a in segment[segment.index('push') + 1:]):
                return 'Force push can overwrite remote history.'
        # Inspect nested shell commands rather than assuming quoted text is inert.
        if name in ('bash', 'sh', 'zsh') and i + 2 < len(tokens) and tokens[i + 1] == '-c':
            nested = reason(tokens[i + 2])
            if nested:
                return nested
    return None


def deny(message):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': message}}))


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError('Expected an object')
        if data.get('tool_name') != 'Bash':
            return 0
        command = data['tool_input']['command']
        if not isinstance(command, str):
            raise ValueError('Expected command text')
        message = reason(command)
    except (ValueError, KeyError, TypeError) as error:
        deny('Guard input is invalid: ' + str(error))
        return 0
    if message:
        record = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command, 'project_path': data.get('cwd', ''), 'reason': message}
        try:
            log = pathlib.Path.home() / '.claude/hooks/blocked.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + '\n')
        except OSError as error:
            message += ' Audit log could not be written: ' + str(error)
        deny(message)
    # No allow decision: leave normal permissions in force.
    return 0


if __name__ == '__main__':
    sys.exit(main())
