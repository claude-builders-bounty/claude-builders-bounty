#!/usr/bin/env python3
"""Claude Code PreToolUse guard for Bash commands."""
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
def _split_shell_segments(command):
    """Split on unquoted shell control operators without executing anything."""
    parts, buf = [], []
    quote = None
    escaped = False
    i = 0
    while i < len(command):
        ch = command[i]
        if escaped:
            buf.append(ch)
            escaped = False
            i += 1
            continue
        if ch == "\\" and quote != "'":
            buf.append(ch)
            escaped = True
            i += 1
            continue
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch in (';', '\n'):
            part = ''.join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            i += 1
            continue
        if ch in ('&', '|'):
            step = 2 if i + 1 < len(command) and command[i + 1] == ch else 1
            part = ''.join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            i += step
            continue
        buf.append(ch)
        i += 1
    part = ''.join(buf).strip()
    if part:
        parts.append(part)
    return parts
def _command_view(tokens):
    """Return executable basename and its arguments for one simple command."""
    if not tokens:
        return None, []
    i = 0
    while i < len(tokens) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', tokens[i]):
        i += 1
    while i < len(tokens):
        base = os.path.basename(tokens[i])
        if base in ('command', 'builtin', 'exec', 'nohup'):
            i += 1
            continue
        if base == 'sudo':
            i += 1
            while i < len(tokens) and tokens[i].startswith('-'):
                if tokens[i] in ('-u', '-g', '-h', '-p', '-C', '-T', '-R', '-D') and i + 1 < len(tokens):
                    i += 2
                else:
                    i += 1
            continue
        if base == 'env':
            i += 1
            while i < len(tokens) and (tokens[i].startswith('-') or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', tokens[i])):
                i += 1
            continue
        break
    if i >= len(tokens):
        return None, []
    return os.path.basename(tokens[i]), tokens[i + 1:]
def _check_rm(tokens):
    base, args = _command_view(tokens)
    if base != 'rm':
        return None
    recursive = force = False
    for arg in args:
        if arg == '--':
            break
        if arg in ('-r', '-R', '--recursive'):
            recursive = True
        elif arg in ('-f', '--force'):
            force = True
        elif len(arg) > 2 and arg.startswith('-') and not arg.startswith('--'):
            flags = arg[1:]
            recursive |= ('r' in flags or 'R' in flags)
            force |= 'f' in flags
    return 'rm with recursive+force flags' if recursive and force else None
def _check_git_push(tokens):
    base, args = _command_view(tokens)
    if base != 'git':
        return None
    try:
        p = args.index('push')
    except ValueError:
        return None
    for arg in args[p + 1:]:
        if arg in ('--force', '-f') or arg.startswith('--force='):
            return 'git push with --force'
    return None
def _check_sql(tokens):
    base, args = _command_view(tokens)
    if base not in ('mysql', 'psql', 'sqlite3'):
        return None
    for i, arg in enumerate(args):
        if arg not in ('-c', '-e') or i + 1 >= len(args):
            continue
        norm = re.sub(r'\s+', ' ', args[i + 1]).upper()
        if re.search(r'\bDROP\s+TABLE\b', norm):
            return 'SQL DROP TABLE'
        if re.search(r'\bTRUNCATE\b', norm):
            return 'SQL TRUNCATE'
        m = re.search(r'\bDELETE\s+FROM\b(.*?)(?:;|$)', norm)
        if m and not re.search(r'\bWHERE\b', m.group(1)):
            return 'SQL DELETE FROM without WHERE'
    return None
def _check_exec_context(tokens):
    base, args = _command_view(tokens)
    if base not in ('sh', 'bash'):
        return None
    for i, arg in enumerate(args):
        if arg == '-c' and i + 1 < len(args):
            reason = check_command(args[i + 1])
            if reason:
                return f'{base} -c: {reason}'
    return None
def _subcommands(command):
    """Extract unquoted command substitutions/backticks for recursive inspection."""
    out = []
    i = 0
    single = double = escaped = False
    while i < len(command):
        ch = command[i]
        if escaped:
            escaped = False; i += 1; continue
        if ch == '\\' and not single:
            escaped = True; i += 1; continue
        if ch == "'" and not double:
            single = not single; i += 1; continue
        if ch == '"' and not single:
            double = not double; i += 1; continue
        if single:
            i += 1; continue
        if ch == '`':
            j, buf, esc = i + 1, [], False
            while j < len(command):
                c = command[j]
                if esc:
                    buf.append(c); esc = False
                elif c == '\\':
                    buf.append(c); esc = True
                elif c == '`':
                    break
                else:
                    buf.append(c)
                j += 1
            if j < len(command):
                out.append(''.join(buf)); i = j + 1; continue
        if ch == '$' and i + 1 < len(command) and command[i + 1] == '(' and not (i + 2 < len(command) and command[i + 2] == '('):
            j, depth, buf, q, esc = i + 2, 1, [], None, False
            while j < len(command):
                c = command[j]
                if esc:
                    buf.append(c); esc = False; j += 1; continue
                if c == '\\' and q != "'":
                    buf.append(c); esc = True; j += 1; continue
                if q:
                    buf.append(c)
                    if c == q: q = None
                elif c in ("'", '"'):
                    q = c; buf.append(c)
                elif c == '(':
                    depth += 1; buf.append(c)
                elif c == ')':
                    depth -= 1
                    if depth == 0: break
                    buf.append(c)
                else:
                    buf.append(c)
                j += 1
            if depth == 0:
                out.append(''.join(buf)); i = j + 1; continue
        i += 1
    return out
def check_command(command):
    for sub in _subcommands(command):
        reason = check_command(sub)
        if reason:
            return f'command substitution: {reason}'
    for segment in _split_shell_segments(command):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            return None
        for checker in (_check_rm, _check_git_push, _check_sql, _check_exec_context):
            reason = checker(tokens)
            if reason:
                return reason
    return None
def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        return 0
    tool_name = payload.get('tool_name', '')
    if not isinstance(tool_name, str) or tool_name.lower() != 'bash':
        return 0
    tool_input = payload.get('tool_input')
    command = tool_input.get('command') if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return 0
    reason = check_command(command)
    if not reason:
        return 0
    cwd = payload.get('cwd', os.getcwd())
    log_dir = os.path.join(os.environ.get('HOME', ''), '.claude', 'hooks')
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, 'blocked.log'), 'a') as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} | {command} | {cwd}\n")
    except Exception:
        pass
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    return 0
if __name__ == '__main__':
    sys.exit(main())
