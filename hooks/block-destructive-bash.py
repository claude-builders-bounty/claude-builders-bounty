#!/usr/bin/env python3
"""Claude Code PreToolUse (Bash) safety hook. Stdlib only."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import sys

SPLIT = {';', '&&', '||', '|', '&', '(', ')', '\n'}
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
SQL_DROP = re.compile(r'^\s*DROP\s+(?:TABLE|DATABASE|SCHEMA)\b', re.I | re.S)
SQL_TRUNCATE = re.compile(r'^\s*TRUNCATE\s+(?:TABLE\s+)?\b', re.I | re.S)
SQL_DELETE = re.compile(r'^\s*DELETE\s+FROM\s+[^;]+', re.I | re.S)
SQL_WHERE = re.compile(r'\bWHERE\b', re.I)

def sql_reason(statement):
    for sql in statement.split(';'):
        sql = re.sub(r'--[^\n]*', '', sql).strip()
        if SQL_DROP.match(sql):
            return 'destructive SQL DROP operation'
        if SQL_TRUNCATE.match(sql):
            return 'destructive SQL TRUNCATE operation'
        if SQL_DELETE.match(sql) and not SQL_WHERE.search(sql):
            return 'DELETE FROM without a WHERE clause'
    return None

def lex(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()')
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)

def segments(tokens):
    current = []
    for token in tokens:
        if token in SPLIT or (token and all(c in ';|&()' for c in token)):
            if current:
                yield current
                current = []
        else:
            current.append(token)
    if current:
        yield current

def strip_wrappers(words):
    words = list(words)
    for _ in range(10):
        if not words:
            return words
        w = words[0]
        if ASSIGNMENT.match(w):
            words.pop(0)
        elif w in ('sudo', 'env'):
            words.pop(0)
            if w == 'sudo':
                while words and words[0].startswith('-'):
                    opt = words.pop(0)
                    if opt in ('-u', '-g', '-h', '-p') and words:
                        words.pop(0)
        elif w in ('command', 'builtin', 'exec', 'nohup'):
            words.pop(0)
        else:
            return words
    return words

def rm_is_recursive_force(args):
    recursive, force = False, False
    for arg in args:
        if arg == '--':
            break
        if not arg.startswith('-') or arg == '-':
            break
        if arg == '--recursive':
            recursive = True
        elif arg == '--force':
            force = True
        elif arg.startswith('--'):
            continue
        else:
            opts = arg[1:]
            recursive |= 'r' in opts or 'R' in opts
            force |= 'f' in opts
    return recursive and force

def git_reason(args):
    index = 0
    while index < len(args) and args[index].startswith('-'):
        arg = args[index]
        index += 1
        if arg in ('-C', '-c', '--git-dir', '--work-tree'):
            index += 1
    if index >= len(args):
        return None
    subcommand, tail = args[index], args[index + 1:]
    if subcommand == 'push' and any(a == '--force' or a.startswith('--force=') or (a.startswith('-') and not a.startswith('--') and 'f' in a[1:]) for a in tail):
        return 'git push --force can overwrite remote history'
    if subcommand == 'reset' and '--hard' in tail:
        return 'git reset --hard discards local changes'
    if subcommand == 'checkout' and '--' in tail:
        return 'git checkout -- discards local changes'
    return None

def command_reason(command, depth=0):
    if depth > 4:
        return None
    try:
        parts = list(segments(lex(command)))
    except ValueError:
        return None
    for part in parts:
        p = strip_wrappers(part)
        if not p:
            continue
        exe = p[0].rsplit('/', 1)[-1]
        tail = p[1:]
        if exe == 'rm' and rm_is_recursive_force(tail):
            return 'recursive forced deletion (rm -rf)'
        if exe == 'git':
            reason = git_reason(tail)
            if reason:
                return reason
        if exe == 'chmod' and any(re.fullmatch(r'0?777', arg) for arg in tail):
            return 'world-writable chmod 777'
        if exe in ('bash', 'sh', 'zsh', 'dash'):
            for i, arg in enumerate(tail[:-1]):
                if arg in ('-c', '-lc', '-ec', '-xc'):
                    reason = command_reason(tail[i + 1], depth + 1)
                    if reason:
                        return reason
        if exe in ('psql', 'mysql', 'mariadb'):
            for i, arg in enumerate(tail[:-1]):
                if arg in ('-c', '-e', '--command', '--execute'):
                    reason = sql_reason(tail[i + 1])
                    if reason:
                        return reason
            for arg in tail:
                if arg.startswith('--command=') or arg.startswith('--execute='):
                    reason = sql_reason(arg.split('=', 1)[1])
                    if reason:
                        return reason
        if exe == 'sqlite3':
            for arg in tail:
                reason = sql_reason(arg)
                if reason:
                    return reason
        if exe.upper() in ('DROP', 'TRUNCATE', 'DELETE'):
            reason = sql_reason(' '.join(p))
            if reason:
                return reason
    return None

def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get('tool_name') not in ('Bash', 'functions.run_sync', None):
        return 0
    tool_input = payload.get('tool_input')
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get('command'), str):
        return 0
    command = tool_input['command']
    reason = command_reason(command)
    if not reason:
        return 0
    project = str(payload.get('cwd') or payload.get('project_dir') or os.getcwd())
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    log_path = Path(os.path.expanduser(os.environ.get('CLAUDE_HOOK_LOG', '~/.claude/hooks/blocked.log')))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('a', encoding='utf-8') as log:
            log.write(json.dumps({'timestamp': timestamp, 'command': command, 'project_path': project, 'reason': reason}, ensure_ascii=False) + '\n')
    except OSError as exc:
        print(f'WARNING: could not write hook audit log: {exc}', file=sys.stderr)
    print(f'BLOCKED by destructive-command safety hook: {reason}. Command: {command}', file=sys.stderr)
    return 2

if __name__ == '__main__':
    raise SystemExit(main())
