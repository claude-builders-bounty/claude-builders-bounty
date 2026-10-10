#!/usr/bin/env python3
"""Generate a categorized changelog from local Git history without dependencies."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')

def git(repo, *args):
    p = subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode:
        raise ValueError(p.stderr.strip() or 'Git command failed')
    return p.stdout.rstrip('\n')

def classify(subject):
    conventional = re.match(r'^([a-z]+)(?:\(([^)]*)\))?(!)?:\s*(.+)$',subject,re.I)
    breaking = False
    if conventional:
        kind,scope,bang,message = conventional.groups()
        breaking = bool(bang)
        category = {'feat':'Added','fix':'Fixed','remove':'Removed','revert':'Removed'}.get(kind.lower(),'Changed')
        if scope:
            message = scope + ': ' + message
    else:
        message = subject
        start = subject.lower().split(' ',1)[0].rstrip(':')
        category = 'Added' if start in {'add','adds','added','introduce','implement'} else 'Fixed' if start in {'fix','fixes','fixed','resolve','repair'} else 'Removed' if start in {'remove','removes','removed','delete','drop'} else 'Changed'
    return category,message,breaking

def escape(s):
    # Commit subjects are text, never Markdown links or executable content.
    s = re.sub(r'[\x00-\x1f\x7f]',' ',s)
    return re.sub(r'([\\`*_\[\]<>])',r'\\\1',s)

def generate(repo, version='Unreleased', since=None):
    git(repo,'rev-parse','--verify','HEAD')
    if since:
        # Resolve the supplied tag/ref to a SHA; never allow it to become a Git option.
        base=git(repo,'rev-parse','--verify','--end-of-options',since+'^{commit}')
        reference=since
    else:
        tags=subprocess.run(['git','-C',str(repo),'describe','--tags','--abbrev=0','HEAD'],capture_output=True,text=True)
        reference=tags.stdout.strip() if tags.returncode==0 else None
        base=git(repo,'rev-parse','--verify','--end-of-options',reference+'^{commit}') if reference else None
    revision=base+'..HEAD' if base else 'HEAD'
    log=git(repo,'log','--no-merges','--reverse','--format=%H%x09%s',revision,'--')
    groups={name:[] for name in CATEGORIES}
    for line in log.splitlines():
        commit,subject=line.split('\t',1)
        category,message,breaking=classify(subject)
        groups[category].append('- '+('**Breaking:** ' if breaking else '')+escape(message)+' (`'+commit[:12]+'`)')
    heading='# Changelog\n\n## '+escape(version)+' - '+datetime.now(timezone.utc).strftime('%Y-%m-%d')+'\n\n'
    shallow=git(repo,'rev-parse','--is-shallow-repository')=='true'
    heading+='Changes since '+('tag/ref `'+escape(reference)+'`' if reference else ('the start of available shallow history (no reachable tag)' if shallow else 'the first commit (no reachable tag)'))+'. Merge commits excluded.\n'
    if shallow:
        heading+='\nNote: this is a shallow clone; older commits and tags may be absent. Fetch full history for a complete release changelog.\n'
    for name in CATEGORIES:
        heading+='\n### '+name+'\n\n'+('\n'.join(groups[name]) if groups[name] else '- None.')+'\n'
    return heading

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path('.'))
    p.add_argument('--output',type=Path,default=Path('CHANGELOG.md'))
    p.add_argument('--since',help='Override last reachable tag with a tag/ref')
    p.add_argument('--version',default='Unreleased')
    p.add_argument('--force',action='store_true',help='Allow replacement of an existing output')
    p.add_argument('--stdout',action='store_true')
    args=p.parse_args()
    try:
        output=generate(args.repo,args.version,args.since)
        if args.stdout:
            sys.stdout.buffer.write(output.encode('utf-8'))
        else:
            # Exclusive creation prevents accidental overwrite of existing release history.
            with args.output.open('w' if args.force else 'x',encoding='utf-8',newline='\n') as f:
                f.write(output)
            print('Created '+str(args.output))
    except (ValueError,OSError) as ex:
        print('Error: '+str(ex),file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
