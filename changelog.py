#!/usr/bin/env python3
import re, sys, subprocess
from datetime import datetime
from collections import defaultdict

def run_git(args, cwd=None):
    r = subprocess.run(['git'] + args, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip()

def get_last_tag(repo_path='.'):
    tags = run_git(['tag', '--sort=-creatordate'], cwd=repo_path)
    return tags.split(chr(10))[0] if tags else None

def get_commits(repo_path, tag):
    spec = f'{tag}..HEAD' if tag else 'HEAD'
    return run_git(['log', spec, '--pretty=format:%s'], cwd=repo_path).split(chr(10))

def categorize(msg):
    m = msg.lower().strip()
    for cat, pats in [('Added',[r'^add',r'feat',r'new',r'implement']),
                      ('Fixed',[r'^fix',r'bug',r'repair']),
                      ('Changed',[r'^change',r'^update',r'modif',r'rename']),
                      ('Removed',[r'^remove',r'^delete',r'drop'])]:
        for p in pats:
            if re.search(p, m): return cat
    return 'Changed'

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    out = sys.argv[2] if len(sys.argv) > 2 else 'CHANGELOG.md'
    tag = get_last_tag(repo)
    commits = [c for c in get_commits(repo, tag) if c.strip()]
    cats = defaultdict(list)
    today = datetime.now().strftime('%Y-%m-%d')
    for c in commits:
        cats[categorize(c)].append('- ' + c.strip().capitalize().rstrip('.'))
    lines = [f'# Changelog', f'## [{today}]']
    for cat in ['Added','Fixed','Changed','Removed']:
        if cats[cat]:
            lines.append(f'### {cat}')
            lines.extend(cats[cat])
    open(out,'w',encoding='utf-8').write(chr(10).join(lines) + chr(10))
    print(f'Generated {out} ({len(commits)} commits)')

if __name__ == '__main__':
    main()
