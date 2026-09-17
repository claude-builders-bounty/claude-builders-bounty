#!/usr/bin/env python3
"""Opt-in Claude Code PreToolUse check for the destructive patterns in bounty #3.
This is a conservative static check, not a shell sandbox or complete SQL parser.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import sys

SQL_CLIENTS={'psql','sqlite3','mysql','mariadb','sqlcmd','duckdb'}
SEPARATORS={';','&&','||','|','&','\n','(',')'}

class ParseError(Exception):pass

def sql_tokens(sql:str)->list[str]:
    """Remove literals/comments before keyword and outer WHERE classification."""
    pattern=r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`|\[[^\]]*\]|\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$[\s\S]*?\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$|[A-Za-z_][A-Za-z0-9_]*|[();]"
    result=[]
    for m in re.finditer(pattern,sql):
        s=m.group()
        if s.startswith(('--','/*',"'",'"','`','[','$')):continue
        result.append(s.upper())
    return result

def sql_reasons(sql:str)->list[str]:
    tokens=sql_tokens(sql);reasons=[];depths=[];depth=0
    for token in tokens:
        depths.append(depth)
        if token=='(':depth+=1
        elif token==')':depth=max(0,depth-1)
        elif token==';':depth=0
    for i,token in enumerate(tokens):
        if token=='DROP' and i+1<len(tokens) and tokens[i+1]=='TABLE':reasons.append('DROP TABLE removes a table and its contents.')
        elif token=='TRUNCATE':reasons.append('TRUNCATE removes all rows without a row predicate.')
        elif token=='DELETE' and i+1<len(tokens) and tokens[i+1]=='FROM':
            outer=depths[i];has_where=False
            for j in range(i+2,len(tokens)):
                if tokens[j]==';' or depths[j]<outer:break
                if tokens[j]=='WHERE' and depths[j]==outer:has_where=True;break
            if not has_where:reasons.append('DELETE FROM has no outer WHERE clause in this statement.')
    return reasons

def shell_parts(command:str)->list[list[str]]:
    lexer=shlex.shlex(command,posix=True,punctuation_chars=';&|()\n')
    lexer.whitespace=' \t\r';lexer.whitespace_split=True;lexer.commenters='#'
    try:tokens=list(lexer)
    except ValueError as exc:raise ParseError(str(exc)) from exc
    result=[];current=[]
    for token in tokens:
        if token in SEPARATORS or token and set(token)<=set(';&|()\n'):
            if current:result.append(current);current=[]
        else:current.append(token)
    if current:result.append(current)
    return result

def executable(tokens:list[str])->list[str]:
    tokens=list(tokens)
    while tokens and (re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*',tokens[0]) or tokens[0] in {'then','do','if','!'}):tokens.pop(0)
    if tokens and Path(tokens[0]).name in {'command','exec','nohup'}:
        tokens=tokens[1:]
        if tokens[:1]==['--']:tokens=tokens[1:]
    if tokens and Path(tokens[0]).name=='env':
        tokens=tokens[1:]
        while tokens and (tokens[0].startswith('-') or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*',tokens[0])):
            if tokens[0] in {'-u','--unset','-C','--chdir'} and len(tokens)>1:tokens=tokens[2:]
            else:tokens=tokens[1:]
    if tokens and Path(tokens[0]).name=='sudo':
        tokens=tokens[1:]
        while tokens and tokens[0].startswith('-'):
            option=tokens.pop(0)
            if option in {'-u','-g','-h','-p','-C','-T','--user','--group','--host','--prompt'} and tokens:tokens.pop(0)
            if option=='--':break
    return tokens

def inspect(command:str,depth:int=0)->list[str]:
    if depth>6:return ['Nested shell depth exceeds this hook\'s static inspection limit.']
    parts=shell_parts(command);reasons=[];database_context=False
    for raw in parts:
        tokens=executable(raw)
        if not tokens:continue
        program=Path(tokens[0]).name;args=tokens[1:]
        if program=='rm':
            recursive=False;force=False
            for arg in args:
                if arg=='--':break
                if arg in {'--recursive'}:recursive=True
                elif arg=='--force':force=True
                elif arg.startswith('-') and not arg.startswith('--'):
                    recursive=recursive or 'r' in arg[1:] or 'R' in arg[1:]
                    force=force or 'f' in arg[1:]
            if recursive and force:reasons.append('rm combines recursive and force flags; review the deletion target explicitly.')
        elif program=='git':
            i=0
            while i<len(args) and args[i].startswith('-'):
                option=args[i];i+=1
                if option in {'-C','-c','--git-dir','--work-tree','--namespace'}:i+=1
            if i<len(args) and args[i]=='push':
                push=args[i+1:]
                for arg in push:
                    if arg=='--':break
                    if arg in {'--force','-f'} or arg.startswith('--force=') or (arg.startswith('-') and not arg.startswith('--') and 'f' in arg[1:]):
                        reasons.append('git push requests unconditional force and can replace remote history.');break
                if any(arg.startswith('+') for arg in push):reasons.append('git push contains a force-prefixed refspec.')
        elif program in {'bash','sh','dash','zsh'}:
            for i,arg in enumerate(args):
                if arg in {'-c','-lc','-ic','-lic'} and i+1<len(args):reasons.extend(inspect(args[i+1],depth+1));break
        elif program in {'find','xargs'}:
            for i,arg in enumerate(args):
                if Path(arg).name in {'rm','git','bash','sh'}:
                    reasons.extend(inspect(shlex.join(args[i:]),depth+1));break
        if program in SQL_CLIENTS:database_context=True
        if program.upper() in {'DROP','TRUNCATE','DELETE'}:reasons.extend(sql_reasons(' '.join(tokens)))
    if database_context:
        # Includes SQL carried in -c/-e arguments or an echo/printf pipeline.
        for tokens in parts:
            for token in tokens:reasons.extend(sql_reasons(token))
        reasons.extend(sql_reasons(' '.join(' '.join(tokens) for tokens in parts)))
    return list(dict.fromkeys(reasons))

def append_log(path:Path,command:str,project:str,reasons:list[str])->None:
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.is_symlink():raise OSError('Refusing to append through a log symlink')
    flags=os.O_WRONLY|os.O_CREAT|os.O_APPEND|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags,0o600)
    try:
        os.fchmod(fd,0o600)
        record={'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'command':command,'project_path':project,'reasons':reasons}
        raw=(json.dumps(record,ensure_ascii=False)+'\n').encode()
        offset=0
        while offset<len(raw):offset+=os.write(fd,raw[offset:])
    finally:os.close(fd)

def deny(reason:str)->None:
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':reason}}))

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-file',type=Path,default=Path.home()/'.claude/hooks/blocked.log')
    args=parser.parse_args(argv)
    try:
        raw=sys.stdin.read(1048577)
        if len(raw)>1048576:raise ParseError('Hook input exceeds 1 MiB')
        event=json.loads(raw)
        if not isinstance(event,dict):raise ParseError('Hook input must be a JSON object')
        if event.get('tool_name')!='Bash':print('{}');return 0
        command=event.get('tool_input',{}).get('command')
        if not isinstance(command,str):raise ParseError('Bash command must be a string')
        project=event.get('cwd','')
        if not isinstance(project,str):project='[invalid project path]'
        reasons=inspect(command)
        if not reasons:print('{}');return 0
        try:append_log(args.log_file,command,project,reasons)
        except OSError as exc:
            deny('Blocked: '+' '.join(reasons)+' The audit log could not be written ('+type(exc).__name__+'); correct log access before retrying.')
            return 0
        deny('Blocked: '+' '.join(reasons)+' No command was executed by this hook. Choose a scoped non-destructive operation or have the owner review this operation outside the hook.');return 0
    except (json.JSONDecodeError,ParseError,ValueError,TypeError,AttributeError) as exc:
        deny('Cannot inspect this Bash tool request: '+str(exc)[:200]+'. Repair the input rather than executing an uninspected request.');return 0

if __name__=='__main__':raise SystemExit(main())
