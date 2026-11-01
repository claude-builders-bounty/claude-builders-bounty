#!/usr/bin/env python3
"""Pattern-based Claude Code PreToolUse hook; not a shell sandbox."""
from __future__ import annotations
import json, os, re, shlex, sys
from datetime import datetime, timezone
from pathlib import Path

def sql_reason(text):
    # Remove quoted values and comments before checking each individual statement.
    clean = re.sub(r"'(?:''|[^'])*'|/\*[\s\S]*?\*/|--[^\n]*", ' ', text)
    for statement in clean.split(';'):
        if re.search(r'\bDROP\s+TABLE\b', statement, re.I): return 'DROP TABLE'
        if re.search(r'\bTRUNCATE\b', statement, re.I): return 'TRUNCATE'
        if re.search(r'\bDELETE\s+FROM\b', statement, re.I) and not re.search(r'\bWHERE\b', statement, re.I):
            return 'DELETE FROM without WHERE in that statement'
    return None

def evaluate(command: str, depth=0) -> tuple[bool, str | None]:
    if depth > 8: return True, 'Nested shell inspection depth exceeded'
    if re.match(r'^\s*(?:DELETE|DROP|TRUNCATE|SELECT|UPDATE|WITH|INSERT)\b', command, re.I):
        reason = sql_reason(command)
        return bool(reason), reason
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|\n')
        lexer.whitespace = ' \t\r'; lexer.whitespace_split = True
        words = list(lexer)
    except ValueError: return True, 'Unparseable shell command'
    segments, segment = [], []
    for word in words + [';']:
        if word and all(c in ';&|\n' for c in word):
            if segment: segments.append(segment)
            segment = []
        else: segment.append(word)
    for tokens in segments:
        if not tokens: continue
        # Inspect plain display commands as data, not executable code.
        first = Path(tokens[0]).name
        if first in {'echo','printf'}: continue
        for i, token in enumerate(tokens):
            name = Path(token).name
            if name in {'sh','bash','zsh'} and '-c' in tokens[i+1:]:
                index = tokens.index('-c',i+1)
                if index+1 < len(tokens):
                    denied,reason = evaluate(tokens[index+1],depth+1)
                    if denied:return denied,reason
            if name == 'rm':
                flags=[]
                for value in tokens[i+1:]:
                    if value == '--': break
                    if value.startswith('-'): flags.append(value)
                recursive = '--recursive' in flags or any(not v.startswith('--') and ('r' in v[1:] or 'R' in v[1:]) for v in flags)
                force = '--force' in flags or any(not v.startswith('--') and 'f' in v[1:] for v in flags)
                if recursive and force:return True,'rm recursive + force'
            if name == 'git' and 'push' in tokens[i+1:]:
                after=tokens[tokens.index('push',i+1)+1:]
                for flag in after:
                    if flag == '--':break
                    if flag in {'-f','--force'} or flag.startswith('--force-with-lease'):
                        return True,'git push force'
            if name in {'sqlite3','mysql','mariadb','psql'}:
                for arg in tokens[i+1:]:
                    reason=sql_reason(arg)
                    if reason:return True,reason
    return False,None

def main() -> int:
    try:
        payload=json.load(sys.stdin)
        if not isinstance(payload,dict):raise ValueError('object required')
        if payload.get('tool_name','Bash') != 'Bash':return 0
        tool_input=payload.get('tool_input',{})
        command=tool_input.get('command')
        if not isinstance(command,str):raise ValueError('command string required')
    except (ValueError,AttributeError,TypeError):
        print('Invalid hook input; refusing this tool call.',file=sys.stderr);return 2
    denied,reason=evaluate(command)
    if not denied:return 0  # Do not auto-approve; defer to normal Claude permissions.
    record={'timestamp':datetime.now(timezone.utc).isoformat(),'attempted_command':command,
            'project_path':payload.get('cwd',os.getcwd()),'reason':reason}
    try:
        target=Path.home()/'.claude/hooks/blocked.log'
        target.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(target,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
        with os.fdopen(fd,'a',encoding='utf-8') as stream:
            stream.write(json.dumps(record,ensure_ascii=False)+'\n')
    except OSError:
        print('Blocked command; could not append audit log.',file=sys.stderr)
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny',
          'permissionDecisionReason':'Destructive command blocked: '+str(reason)}}))
    return 0
if __name__=='__main__':raise SystemExit(main())
