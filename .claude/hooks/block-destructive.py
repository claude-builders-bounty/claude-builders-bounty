#!/usr/bin/env python3
"""Best-effort destructive-command denylist, not a shell sandbox."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import sys

def sql_reason(text):
    # Remove SQL comments and quoted values before interpreting WHERE.
    # Preserve quoted identifiers as an identifier token, never as SQL keywords.
    cleaned = re.sub(r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`|\[[^\]]*\]",
                     lambda match: ' ' if match[0].startswith(('--', '/*')) else ' VALUE ', text)
    for statement in cleaned.split(';'):
        if re.search(r'\bDROP\s+TABLE\b', statement, re.I):
            return 'DROP TABLE can permanently remove a database table'
        if re.search(r'\bTRUNCATE\b', statement, re.I):
            return 'TRUNCATE can remove all rows from a table'
        if re.search(r'\bDELETE\s+FROM\b', statement, re.I) and not re.search(r'\bWHERE\b', statement, re.I):
            return 'DELETE FROM without a WHERE clause can remove every row'
    return None

def segments(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()\n')
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    groups, current = [], []
    for token in lexer:
        if token and all(c in ';&|()\n' for c in token):
            if current: groups.append(current)
            current = []
        else:
            current.append(token)
    if current: groups.append(current)
    return groups

def executable(token):
    return token.rsplit('/', 1)[-1].lower()

def blocked_reason(command, depth=0):
    if depth > 8:
        return 'nested shell command exceeds safe inspection depth'
    command = command or ''
    try:
        groups = segments(command)
    except ValueError:
        return 'shell command could not be parsed safely'
    # A literal SQL command can be supplied directly by a tool as well.
    if re.match(r'^\s*(?:DROP|TRUNCATE|DELETE)\b', command, re.I):
        return sql_reason(command)
    sql_clients = {'sqlite3', 'psql', 'mysql', 'mariadb'}
    pipeline_to_sql = bool(re.search(r'\|\s*(?:\S*/)?(?:sqlite3|psql|mysql|mariadb)\b', command))
    for original in groups:
        args = list(original)
        while args and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', args[0]): args.pop(0)
        if args and executable(args[0]) in {'sudo', 'command', 'builtin', 'env'}:
            args.pop(0)
            while args and (args[0].startswith('-') or re.match(r'^\w+=', args[0])): args.pop(0)
        if not args: continue
        name = executable(args[0])
        if name == 'rm':
            flags = set()
            for arg in args[1:]:
                if arg == '--': break
                if arg == '--recursive': flags.add('r')
                elif arg == '--force': flags.add('f')
                elif arg.startswith('-') and not arg.startswith('--'): flags.update(arg[1:].lower())
            if {'r', 'f'} <= flags:
                return 'recursive forced removal can delete data irreversibly'
        if name == 'git':
            index = 1
            while index < len(args) and args[index].startswith('-'):
                index += 2 if args[index] in {'-C', '-c', '--git-dir', '--work-tree'} else 1
            if index < len(args) and args[index] == 'push':
                for arg in args[index + 1:]:
                    if arg == '--force' or re.match(r'^-[^-]*f', arg) or arg.startswith('--force-with-lease') or arg.startswith('+'):
                        return 'forced git push can rewrite shared history'
        if name in {'bash', 'sh', 'zsh', 'dash', 'ksh'}:
            for index, arg in enumerate(args[1:], 1):
                if arg.startswith('-') and 'c' in arg[1:] and index + 1 < len(args):
                    reason = blocked_reason(args[index + 1], depth + 1)
                    if reason: return reason
        if name in sql_clients or (pipeline_to_sql and name in {'echo', 'printf'}):
            for arg in args[1:]:
                reason = sql_reason(arg)
                if reason: return reason
    return None

def log_block(command, project_path, reason):
    directory = Path.home() / '.claude' / 'hooks'
    directory.mkdir(parents=True, exist_ok=True)
    record = {'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
              'command': command, 'project_path': project_path, 'reason': reason}
    # JSON prevents newlines or tabs in input from forging separate log records.
    fd = os.open(directory / 'blocked.log', os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + '\n')

def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny', 'permissionDecisionReason': 'Destructive command blocked: ' + reason}}))

def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict): raise ValueError('hook input must be an object')
        if payload.get('tool_name') != 'Bash': return 0
        tool_input = payload.get('tool_input')
        if not isinstance(tool_input, dict) or not isinstance(tool_input.get('command'), str):
            raise ValueError('Bash command must be a string')
        command = tool_input['command']
        reason = blocked_reason(command)
        if not reason: return 0
        project = str(payload.get('cwd') or os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())
        try:
            log_block(command, project, reason)
        except OSError:
            # Failure to log must never turn a denial into permission to execute.
            print('Hook could not write blocked.log; command remains denied.', file=sys.stderr)
        deny(reason)
        return 0
    except (ValueError, TypeError) as error:
        deny('invalid hook input: ' + str(error))
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
