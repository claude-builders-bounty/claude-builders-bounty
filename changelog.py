#!/usr/bin/env python3
"""
CHANGELOG Generator
从 git 历史生成结构化 CHANGELOG.md
自动分类: Added / Fixed / Changed / Removed
用法: python3 changelog.py <目标仓库路径>
"""
import sys, os, re, subprocess
from datetime import datetime

def run_git(args, repo='.'):
    return subprocess.run(['git','-C',repo]+args, capture_output=True, text=True, timeout=30).stdout.strip()

def get_commits(repo):
    tags = run_git(['tag','--sort=-v:refname'],repo)
    rs = f'{tags.split(chr(10))[0]}..HEAD' if tags else 'HEAD~100..HEAD'
    out = run_git(['log',rs,'--pretty=format:%H||%s||%ai','--no-merges'],repo)
    return [{'hash':p[0],'msg':p[1],'date':p[2]} for line in out.split(chr(10)) if line.strip() for p in [line.split('||',2)] if len(p)==3]

def categorize(msg):
    m = msg.lower()
    rules = [('Added',    [r'\badd(ed|s|ition)?\b',r'^feat[:(]',r'\bnew\b']),
             ('Fixed',    [r'\bfix(ed|es)?\b',r'^fix[:(]',r'\bbug\w*\b',r'\bpatch\b']),
             ('Changed',  [r'\bchange\w*\b',r'\bupdate\w*\b',r'^refact[:(]',r'\boptimiz\w*\b']),
             ('Removed',  [r'\bremove\w*\b',r'\bdel\w*\b',r'^remove[:(]',r'\bbreak\w*\b'])]
    for cat,pats in rules:
        for p in pats:
            if re.search(p,m): return cat
    return 'Changed'

def generate(repo,out=None):
    if not out: out = os.path.join(repo,'CHANGELOG.md')
    cs = get_commits(repo)
    if not cs: return "# Changelog\n\nNo changes."
    cats={};
    for c in cs: cats.setdefault(categorize(c['msg']),[]).append(c)
    lines=[f'# Changelog',f'\nGenerated: {datetime.now().strftime("%Y-%m-%d")} | {len(cs)} commits','','## Unreleased','']
    for cat in ['Added','Fixed','Changed','Removed']:
        if cat in cats:
            lines.append(f'### {cat}')
            for c in cats[cat]: lines.append(f"- {c['msg']} (`{c['hash'][:7]}`)")
            lines.append('')
    with open(out,'w') as f: f.write(chr(10).join(lines))
    return chr(10).join(lines)

if __name__=='__main__':
    repo = sys.argv[1] if len(sys.argv)>1 else '.'
    out = sys.argv[2] if len(sys.argv)>2 else None
    print(generate(repo,out))
    print(f"\nCHANGELOG.md generated: {out or 'CHANGELOG.md'}")
