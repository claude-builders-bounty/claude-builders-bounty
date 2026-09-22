#!/usr/bin/env python3
"""Best-effort destructive-command guard, not a shell or SQL security sandbox."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys


def sql_reason(sql):
    # Literals and quoted identifiers cannot supply a WHERE keyword. Comments
    # are whitespace; semicolons inside strings do not end a statement.
    tokens = re.findall(
        r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|"
        r"`[^`]*`|\[[^\]]*\]|[A-Za-z_]+|[();]", sql
    )
    statement, depth = [], 0
    for token in tokens + [';']:
        if token.startswith(('--', '/*')):
            continue
        if token == ';':
            words = [word for word, level in statement if level == 0]
            if 'DROP' in words and 'TABLE' in words:
                return 'DROP TABLE removes a table.'
            if 'TRUNCATE' in words:
                return 'TRUNCATE removes all rows.'
            if 'DELETE' in words and 'FROM' in words and 'WHERE' not in words:
                return 'DELETE FROM requires a WHERE clause in the same statement.'
            statement, depth = [], 0
        elif token == '(':
            depth += 1
        elif token == ')':
            depth = max(0, depth - 1)
        else:
            statement.append((token.upper(), depth))
    return None


def shell_reason(command, depth=0):
    if depth > 8:
        return 'Nested shell inspection limit exceeded.'
    command = command.replace('\\\n', '')
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()<>\n')
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return 'Cannot inspect malformed shell quoting; rewrite the command.'
    sql_client = any(Path(t).name in ('psql', 'mysql', 'mariadb', 'sqlite3') for t in tokens)
    segments, segment = [], []
    for token in tokens + [';']:
        if token and all(c in ';&|()<>\n' for c in token):
            if segment:
                segments.append(segment)
            segment = []
        else:
            segment.append(token)
    for args in segments:
        # Inspect literal executable words, including common sudo/env prefixes.
        # Options after -- are operands and must not be mistaken for flags.
        for index, word in enumerate(args):
            name = Path(word).name
            prefix = args[:index]
            if index and not (prefix[0] in ('sudo', 'env', 'command', 'exec')
                              or all(re.match(r'^[A-Za-z_]\w*=', p) for p in prefix)):
                continue
            if prefix[:2] == ['command', '-v']:
                continue
            rest = args[index + 1:]
            flags = rest[:rest.index('--')] if '--' in rest else rest
            if name == 'rm':
                short = ''.join(t[1:] for t in flags if t.startswith('-') and not t.startswith('--'))
                recursive = 'r' in short or 'R' in short or '--recursive' in flags
                force = 'f' in short or '--force' in flags
                if recursive and force:
                    return 'Recursive forced removal (rm -rf) is blocked.'
            if name == 'git' and 'push' in flags:
                push_args = flags[flags.index('push') + 1:]
                if any(t in ('-f', '--force') or t.startswith('--force=')
                       or t.startswith('--force-with-lease') or t.startswith('+')
                       for t in push_args):
                    return 'Force pushing can overwrite remote history.'
            if name in ('bash', 'sh', 'dash', 'zsh'):
                for n, flag in enumerate(rest[:-1]):
                    if flag.startswith('-') and not flag.startswith('--') and 'c' in flag[1:]:
                        reason = shell_reason(rest[n + 1], depth + 1)
                        if reason:
                            return reason
        # Inspect SQL passed as a literal argument (or piped to a SQL client).
        # Plain echo/printf/grep text without a SQL client is not executed SQL.
        if sql_client or Path(args[0]).name not in ('echo', 'printf', 'grep', 'rg'):
            for arg in args:
                if re.search(r'\b(?:DROP|TRUNCATE|DELETE)\b', arg, re.I):
                    reason = sql_reason(arg)
                    if reason:
                        return reason
            if args[0].upper() in ('DROP', 'TRUNCATE', 'DELETE'):
                reason = sql_reason(' '.join(args))
                if reason:
                    return reason
    return None


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('Expected an event object')
        if event.get('tool_name') != 'Bash':
            return 0
        command = event['tool_input']['command']
        if not isinstance(command, str):
            raise ValueError('Expected a command string')
        reason = shell_reason(command)
        if not reason:
            return 0  # No allow decision: preserve Claude's normal permissions.
        record = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'command': command, 'project_path': event.get('cwd', ''), 'reason': reason}
        try:
            folder = Path.home() / '.claude' / 'hooks'
            folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(folder / 'blocked.log', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, 'a', encoding='utf-8') as log:
                log.write(json.dumps(record, ensure_ascii=True) + '\n')
        except OSError as error:
            reason += ' Audit log unavailable (' + type(error).__name__ + '); command remains blocked.'
        print('Blocked by destructive-command guard: ' + reason, file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError) as error:
        print('Blocked: invalid hook input (' + type(error).__name__ + ').', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
