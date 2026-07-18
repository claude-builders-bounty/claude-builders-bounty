#!/usr/bin/env python3
"""changelog-generator — Generate structured CHANGELOG.md from git history"""
import subprocess, os, sys, re
from datetime import date
from collections import defaultdict

def git(*args, cwd=None):
    """Run git command and return stdout."""
    try:
        r = subprocess.run(['git'] + list(args), capture_output=True, text=True, cwd=cwd, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ''
    except:
        return ''

def parse_conventional(msg):
    """Parse conventional commit message: type(scope)!: description (#123)"""
    # Extract PR number
    pr = ''
    m = re.search(r'\(#(\d+)\)\s*$', msg)
    if m:
        pr = m.group(1)
        msg = msg[:m.start()].strip()

    # Check for breaking change
    is_breaking = 'BREAKING CHANGE' in msg.upper()

    # Parse type(scope)!: description
    m = re.match(r'^([a-zA-Z_-]+)(\([^)]*\))?(!)?\s*:\s*(.*)', msg)
    if m:
        ctype = m.group(1).lower()
        description = m.group(4)
        if m.group(3) == '!':  # "feat!: ..."
            is_breaking = True
    else:
        return None, None, None

    return ctype, description, pr

def categorize(ctype, is_breaking):
    """Map conventional commit type to changelog category."""
    if is_breaking:
        return 'Changed'

    added = {'feat', 'feature', 'add'}
    fixed = {'fix', 'bugfix', 'hotfix', 'bug'}
    changed = {'refactor', 'perf', 'performance', 'style', 'change', 'update', 'upgrade', 'migrate'}
    removed = {'remove', 'deprecat', 'revert', 'delete', 'deprecated'}

    for prefix, cat in [(added, 'Added'), (fixed, 'Fixed'), (changed, 'Changed'), (removed, 'Removed')]:
        if any(ctype.startswith(p) for p in prefix):
            return cat

    return None  # Skip: docs, chore, test, ci, build, etc.

def generate_changelog(since=None, to='HEAD', repo_dir='.', output='CHANGELOG.md'):
    """Main changelog generation function."""
    os.chdir(repo_dir)

    # Auto-detect last tag if no since
    if not since:
        since = git('describe', '--tags', '--abbrev=0')
        if not since:
            since = git('rev-list', '--max-parents=0', 'HEAD')

    # Get date
    today = date.today().isoformat()

    # Get log
    log = git('log', f'{since}..{to}', '--oneline', '--format=%H|%s')
    if not log:
        print(f'⚠️  No commits found between {since} and {to}')
        return False

    categories = defaultdict(list)

    for line in log.split('\n'):
        if '|' not in line:
            continue
        hash_id, msg = line.split('|', 1)

        ctype, description, pr = parse_conventional(msg)
        if not ctype:
            continue

        is_breaking = '+BREAKING+' in msg.replace(' ', '').upper()
        cat = categorize(ctype, is_breaking)
        if not cat:
            continue

        entry = description[0].upper() + description[1:] if description else ''
        if pr:
            entry = f'{entry} (#{pr})'

        categories[cat].append(entry)

    # Write CHANGELOG
    with open(output, 'w', encoding='utf-8') as f:
        f.write(f'# Changelog\n\n')
        f.write(f'## [Unreleased] — {today}\n\n')

        for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
            items = categories.get(cat, [])
            if not items:
                continue
            f.write(f'### {cat}\n\n')
            for item in items:
                f.write(f'- {item}\n')
            f.write('\n')

    # Summary
    total = sum(len(v) for v in categories.values())
    print(f'✅ Changelog written to {output}')
    print(f'\nSummary:')
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        print(f'  {cat:10s}: {len(categories.get(cat, []))}')
    print(f'  {"─"*20}')
    print(f'  {"Total":10s}: {total}')
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate CHANGELOG.md from git history')
    parser.add_argument('--since', help='Starting tag/ref (default: last tag)')
    parser.add_argument('--to', default='HEAD', help='Ending ref (default: HEAD)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', help='Output file')
    parser.add_argument('--dir', '-d', default='.', help='Git repo directory')
    args = parser.parse_args()

    generate_changelog(args.since, args.to, args.dir, args.output)

if __name__ == '__main__':
    main()
