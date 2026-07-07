import subprocess, os, sys, re
from collections import defaultdict

CATEGORIES = {
    'Added': [],
    'Fixed': [],
    'Changed': [],
    'Removed': [],
}

CATEGORY_KEYWORDS = {
    'Added': r'add|create|implement|feat|feature|new|introduce|support',
    'Fixed': r'fix|fixes|fixed|bug|patch|resolve|correct|hotfix',
    'Changed': r'refactor|update|upgrade|migrate|improve|change|bump|deprecat|bump|modify|revamp|redesign',
    'Removed': r'remove|delete|drop|deprecate|remov|cleanup',
}

CATEGORY_FALLBACK = 'Changed'

def get_last_tag():
    try:
        tags = subprocess.run(
            ['git', 'tag', '--sort=-creatordate'],
            capture_output=True, text=True, check=True
        )
        tags = [t.strip() for t in tags.stdout.split('\n') if t.strip()]
        if tags:
            slug = tags[0]
            try:
                subprocess.run(['git', 'rev-parse', slug + '^{}'], capture_output=True, check=True)
                return slug
            except subprocess.CalledProcessError:
                pass
        return None
    except subprocess.CalledProcessError:
        return None

def get_commits(since_ref):
    cmd = ['git', 'log', '--format=%H||%s||%an||%ai', '--no-merges']
    if since_ref:
        cmd.append(f'{since_ref}..HEAD')
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('||', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0][:8],
                'subject': parts[1],
                'author': parts[2],
                'date': parts[3],
            })
    return commits

def categorize(subject):
    subject_lower = subject.lower()
    for cat, pattern in CATEGORY_KEYWORDS.items():
        if re.search(pattern, subject_lower):
            return cat
    return CATEGORY_FALLBACK

def generate(commits):
    categorized = defaultdict(list)
    for c in commits:
        cat = categorize(c['subject'])
        categorized[cat].append(c)

    lines = ['# Changelog', '', f'Generated from {len(commits)} commit(s)', '']
    for cat in ['Added', 'Changed', 'Fixed', 'Removed']:
        items = categorized.get(cat, [])
        if not items:
            continue
        lines.append(f'## {cat}')
        for c in items:
            lines.append(f'- {c["subject"]} ({c["hash"]})')
        lines.append('')
    return '\n'.join(lines)

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'CHANGELOG.md'
    last_tag = get_last_tag()
    ref_desc = f' since {last_tag}' if last_tag else ' (all commits, no tags found)'
    print(f'Fetching commits{ref_desc}...')
    commits = get_commits(last_tag)
    if not commits:
        print('No commits found.')
        sys.exit(1)
    changelog = generate(commits)
    with open(target, 'w') as f:
        f.write(changelog)
    print(f'Written to {target}')
    print(f'Total commits: {len(commits)}')

if __name__ == '__main__':
    main()
