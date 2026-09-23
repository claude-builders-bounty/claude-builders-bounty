#!/usr/bin/env python3
"""A bounded, non-executing Claude Code Bash command guard (stdlib only)."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys


SQL_CLIENTS = {'psql', 'mysql', 'mariadb', 'sqlite3', 'sqlcmd'}


def sql_reason(text):
    # Ignore comments and string literals. Keep quoted identifiers as placeholders.
    pattern = r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`|\[[^\]]*\]|[A-Za-z_][A-Za-z_0-9]*|[();]"
    statements, current, depth = [], [], 0
    for match in re.finditer(pattern, text):
        word = match.group()
        if word.startswith(('--', '/*', "'")):
            continue
        if word == ';':
            statements.append(current)
            current, depth = [], 0
            continue
        if word == '(':
            depth += 1
        elif word == ')':
            depth = max(0, depth - 1)
        else:
            current.append((word.upper(), depth))
    statements.append(current)
    for statement in statements:
        top = [word for word, level in statement if level == 0]
        for i, word in enumerate(top):
            if word == 'DROP' and top[i+1:i+2] == ['TABLE']:
                return 'DROP TABLE removes a database table'
            if word == 'TRUNCATE':
                return 'TRUNCATE removes all table rows'
            if word == 'DELETE' and top[i+1:i+2] == ['FROM'] and 'WHERE' not in top[i+2:]:
                return 'DELETE FROM without a top-level WHERE removes all rows'
    return None


def inspect(command, depth=0):
    if depth > 8:
        return 'shell wrapper nesting exceeds inspection limit'
    lexer = shlex.shlex(command.replace('\\\n', ''), posix=True, punctuation_chars=';&|()<>\n')
    lexer.whitespace = ' \t\r'
    try:
        words = list(lexer)
    except ValueError:
        return 'cannot inspect malformed shell quoting'
    segments, current = [], []
    # shlex consumes newlines; inspect each unquoted shell line separately as well.
    for word in words:
        if word and all(c in ';&|()<>\n' for c in word):
            if current:
                segments.append(current)
            current = []
        else:
            current.append(word)
    if current:
        segments.append(current)
    sql_present = any(Path(w).name in SQL_CLIENTS for s in segments for w in s)
    for segment in segments:
        # Inspect command positions, including wrappers and newline-separated commands.
        for i, token in enumerate(segment):
            name = token.rsplit('/', 1)[-1]
            if i and name not in {'rm', 'git'}:
                continue
            if i and segment[0] in {'echo', 'printf', 'cat', 'grep', 'rg'}:
                continue
            args = segment[i+1:]
            if name == 'rm':
                flags = []
                for arg in args:
                    if arg == '--':
                        break
                    if arg.startswith('-'):
                        flags.append(arg)
                recursive = '--recursive' in flags or any(not f.startswith('--') and ('r' in f or 'R' in f) for f in flags)
                force = '--force' in flags or any(not f.startswith('--') and 'f' in f for f in flags)
                if recursive and force:
                    return 'rm combines recursive deletion and force'
            if name == 'git':
                git_args = list(args)
                while git_args and git_args[0].startswith('-'):
                    option = git_args.pop(0)
                    if option in {'-C', '-c', '--git-dir', '--work-tree', '--namespace'} and git_args:
                        git_args.pop(0)
                if not git_args or git_args[0] != 'push':
                    continue
                push = git_args[1:]
                for arg in push:
                    if arg == '--':
                        break
                    if arg in {'--force', '--force-with-lease', '--force-if-includes'} or arg.startswith('--force-with-lease=') or (arg.startswith('-') and not arg.startswith('--') and 'f' in arg):
                        return 'git push requests a forced remote update'
                if any(a.startswith('+') for a in push):
                    return 'git push uses a forced (+) refspec'
        name = segment[0].rsplit('/', 1)[-1]
        if name in {'bash', 'sh', 'zsh', 'dash'}:
            for i, arg in enumerate(segment[1:], 1):
                if arg.startswith('-') and not arg.startswith('--') and 'c' in arg and i+1 < len(segment):
                    reason = inspect(segment[i+1], depth+1)
                    if reason:
                        return reason
        if name in SQL_CLIENTS or (sql_present and name in {'echo', 'printf', 'cat'}):
            for arg in segment[1:]:
                reason = sql_reason(arg)
                if reason:
                    return reason
        if name.upper() in {'DROP', 'TRUNCATE', 'DELETE'}:
            reason = sql_reason(' '.join(segment))
            if reason:
                return reason
    return None


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
          'permissionDecision': 'deny', 'permissionDecisionReason': 'Command guard: ' + reason}}))


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError('expected JSON object')
        if data.get('tool_name') != 'Bash':
            return 0
        command = data['tool_input']['command']
        cwd = data.get('cwd', '')
        if not isinstance(command, str) or not isinstance(cwd, str):
            raise ValueError('command and cwd must be strings')
    except (ValueError, KeyError, TypeError) as error:
        deny('invalid hook input; inspection failed: ' + str(error))
        return 0
    reason = inspect(command)
    if reason:
        try:
            log = Path.home() / '.claude' / 'hooks' / 'blocked.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                             'command': command, 'cwd': cwd, 'reason': reason}, ensure_ascii=True) + '\n')
        except OSError as error:
            reason += '; audit log failed: ' + str(error)
        deny(reason)
    return 0


if __name__ == '__main__':
    sys.exit(main())
