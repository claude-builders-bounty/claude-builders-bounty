#!/usr/bin/env python3
"""
Generate CHANGELOG.md from git history — improved version

Usage:
    python3 generate_changelog.py                          # Default: CHANGELOG.md
    python3 generate_changelog.py --output RELEASE.md      # Custom output file
    python3 generate_changelog.py --since v1.0.0           # Commits since tag
    python3 generate_changelog.py --until v2.0.0           # Commits up to tag
    python3 generate_changelog.py --format json            # JSON output
    python3 generate_changelog.py --from-ref main..feature # Explicit ref range
    python3 generate_changelog.py --include-deploy         # Add deployment instructions
    python3 generate_changelog.py --verbose | -v           # Show matched/unmatched counts
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    'added': re.compile(r'^(feat|add|feature|new)', re.I),
    'fixed': re.compile(r'^(fix|bug|patch|hotfix)', re.I),
    'changed': re.compile(r'^(change|refactor|update|upgrade|improve|migrate)', re.I),
    'removed': re.compile(r'^(remove|delete|deprecate|drop)', re.I),
    'docs': re.compile(r'^(doc|docs|readme|comment|README)', re.I),
    'tests': re.compile(r'^(test|spec|coverage)', re.I),
    'ci': re.compile(r'^(ci|cd|deploy|pipeline)', re.I),
    'security': re.compile(r'^(security|cve|vuln|auth)', re.I),
    'perf': re.compile(r'^(perf|performance|optimize|speed)', re.I),
    'chore': re.compile(r'^(chore|bump|deps|config|setup)', re.I),
}

CATEGORY_LABELS = {
    'added': 'Added',
    'fixed': 'Fixed',
    'changed': 'Changed',
    'removed': 'Removed',
    'docs': 'Documentation',
    'tests': 'Tests',
    'ci': 'CI/CD',
    'security': 'Security',
    'perf': 'Performance',
    'chore': 'Chores',
}

DEPLOYMENT_TEMPLATE = """
## Automated Deployment

This release is ready for automated deployment.

### Deploy Instructions

```bash
# 1. Build the application
npm run build

# 2. Run database migrations
npm run db:migrate

# 3. Deploy to production
# Fly.io:
flyctl deploy --remote-only

# Railway:
# Push to main branch triggers auto-deploy

# 4. Verify deployment
curl -f https://your-app.com/api/health
```

### Environment Variables Required

| Variable | Description | Required |
|----------|-------------|----------|
| `SESSION_SECRET` | JWT signing secret (32+ random bytes) | ✅ |
| `DATABASE_PATH` | Path to SQLite database file | ❌ (default: data/app.db) |
| `NEXT_PUBLIC_APP_URL` | Public URL of the app | ✅ |

### Database Migration Checklist

- [ ] Run migrations on production before deploying new code
- [ ] Back up SQLite file before applying destructive migrations
- [ ] Verify rollback plan for reversible changes
"""


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ['git'] + args,
        capture_output=True, text=True
    )
    return result.stdout.strip()


def get_last_tag() -> str | None:
    tag = run_git(['describe', '--tags', '--abbrev=0'])
    return tag or None


def get_commits(since: str | None = None, until: str | None = None,
                from_ref: str | None = None, max_count: int = 200) -> list[dict]:
    """Get commits as structured list of dicts with hash, message, author, date."""
    if from_ref:
        range_spec = from_ref
    elif since and until:
        range_spec = f'{since}..{until}'
    elif since:
        range_spec = f'{since}..HEAD'
    elif until:
        range_spec = f'{run_git(["rev-list", "--max-parents=0", "HEAD"])}..{until}'
    else:
        range_spec = f'{get_last_tag() or run_git(["rev-list", "--max-parents=0", "HEAD"])}..HEAD'

    raw = run_git([
        'log', range_spec,
        f'--max-count={max_count}',
        '--reverse',
        '--format=%H||%s||%an||%ai'
    ])

    commits = []
    for line in raw.split('\n'):
        if not line:
            continue
        parts = line.split('||', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0],
                'message': parts[1],
                'author': parts[2],
                'date': parts[3],
            })
    return commits


def categorize(message: str) -> str:
    for key, pattern in CATEGORIES.items():
        if pattern.search(message):
            return CATEGORY_LABELS[key]
    return 'Changed'  # Uncategorized


def generate_changelog_text(commits: list[dict], version: str = None,
                             include_deploy: bool = False) -> str:
    if not version:
        version = get_last_tag() or 'Unreleased'

    date = datetime.now().strftime('%Y-%m-%d')
    categorized: dict[str, list[str]] = {
        label: [] for label in CATEGORY_LABELS.values()
    }
    categorized['Changed'] = []

    for commit in commits:
        cat = categorize(commit['message'])
        # Strip conventional commit prefix for cleaner output
        msg = re.sub(r'^(feat|fix|chore|docs|test|refactor|perf|ci|security)\(?[^)]*\)?:\s*',
                     '', commit['message'], flags=re.I)
        categorized[cat].append(f"  - {msg} ({commit['hash'][:7]})")

    lines = [
        '# Changelog',
        '',
        'All notable changes to this project will be documented in this file.',
        '',
        f'## [{version}] - {date}',
        '',
    ]

    for category in ['Added', 'Fixed', 'Changed', 'Removed', 'Security',
                      'Performance', 'CI/CD', 'Documentation', 'Tests', 'Chores']:
        items = categorized.get(category, [])
        if items:
            lines.append(f'### {category}')
            lines.append('')
            lines.extend(items)
            lines.append('')

    # Add remaining items
    if categorized.get('Changed'):
        lines.append('### Changed')
        lines.append('')
        lines.extend(categorized['Changed'])
        lines.append('')

    if include_deploy:
        lines.append(DEPLOYMENT_TEMPLATE.strip())
        lines.append('')

    return '\n'.join(lines)


def generate_changelog_json(commits: list[dict], version: str = None,
                             include_deploy: bool = False) -> str:
    if not version:
        version = get_last_tag() or 'Unreleased'

    date = datetime.now().strftime('%Y-%m-%d')
    categorized: dict[str, list[str]] = {
        label: [] for label in CATEGORY_LABELS.values()
    }
    categorized['Changed'] = []

    for commit in commits:
        cat = categorize(commit['message'])
        msg = re.sub(r'^(feat|fix|chore|docs|test|refactor|perf|ci|security)\(?[^)]*\)?:\s*',
                     '', commit['message'], flags=re.I)
        categorized[cat].append({
            'message': msg,
            'hash': commit['hash'][:7],
            'author': commit['author'],
            'date': commit['date'],
        })

    output = {
        'version': version,
        'date': date,
        'categories': {k: v for k, v in categorized.items() if v},
    }

    if include_deploy:
        output['deployment'] = {
            'instructions': [
                'npm run build',
                'npm run db:migrate',
                'flyctl deploy --remote-only',
            ],
            'env_vars': {
                'SESSION_SECRET': 'Required - JWT signing secret',
                'DATABASE_PATH': 'Optional - default: data/app.db',
                'NEXT_PUBLIC_APP_URL': 'Required - public URL',
            },
        }

    return json.dumps(output, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Generate CHANGELOG.md from git history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_changelog.py                              Default CHANGELOG.md
  python3 generate_changelog.py --output RELEASE.md          Custom output
  python3 generate_changelog.py --since v1.0.0               Since tag
  python3 generate_changelog.py --format json --since v1.0.0 JSON output
  python3 generate_changelog.py --from-ref main..feature     Custom ref range
  python3 generate_changelog.py --include-deploy             With deploy instructions
  python3 generate_changelog.py --verbose                    Verbose stats
        """
    )
    parser.add_argument('--output', '-o', default='CHANGELOG.md',
                        help='Output file path (default: CHANGELOG.md)')
    parser.add_argument('--since', help='Starting tag/ref (e.g., v1.0.0)')
    parser.add_argument('--until', help='Ending tag/ref (e.g., v2.0.0)')
    parser.add_argument('--from-ref', help='Explicit ref range (e.g., main..feature)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                        help='Output format (default: markdown)')
    parser.add_argument('--include-deploy', action='store_true',
                        help='Include automated deployment instructions')
    parser.add_argument('--max-count', type=int, default=200,
                        help='Maximum number of commits to process (default: 200)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose statistics')
    parser.add_argument('--version', action='store_true',
                        help='Show version and exit')

    args = parser.parse_args()

    if args.version:
        print('generate_changelog.py v2.0.0')
        sys.exit(0)

    try:
        commits = get_commits(
            since=args.since,
            until=args.until,
            from_ref=args.from_ref,
            max_count=args.max_count,
        )
    except Exception as e:
        print(f'❌ Error getting commits: {e}', file=sys.stderr)
        sys.exit(1)

    if not commits:
        print('⚠️  No commits found in the specified range.')
        sys.exit(0)

    # Determine version
    version = None
    if args.since and not args.until:
        version = args.since
    elif args.until:
        version = args.until

    # Generate content
    if args.format == 'json':
        content = generate_changelog_json(commits, version, args.include_deploy)
    else:
        content = generate_changelog_text(commits, version, args.include_deploy)

    # Write output
    output_path = Path(args.output)
    output_path.write_text(content)

    if args.verbose:
        categorized: dict[str, list] = {}
        for c in commits:
            cat = categorize(c['message'])
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(c['message'])

        print(f'✅ CHANGELOG generated to {args.output}')
        print(f'📊 Statistics:')
        print(f'   Total commits: {len(commits)}')
        for cat, items in sorted(categorized.items()):
            print(f'   {cat}: {len(items)}')
        print(f'   Format: {args.format}')
        print(f'   Include deploy: {args.include_deploy}')
    else:
        print(f'✅ CHANGELOG generated to {args.output}')


if __name__ == '__main__':
    main()
