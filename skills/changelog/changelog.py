#!/usr/bin/env python3
"""
changelog.py - Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py                    # generates CHANGELOG.md in current dir
    python changelog.py --output CHANGELOG.md
    python changelog.py --repo /path/to/repo

Requirements: git (installed and accessible from command line)
"""

import subprocess
import os
import re
import sys
from datetime import datetime


# Conventional commit keywords mapped to categories
CATEGORY_RULES = {
    'Added': [
        r'^feat(\(.+\))?[!]?:', r'^feature(\(.+\))?[!]?:',
        r'^add', r'^new', r'^create', r'^implement',
    ],
    'Fixed': [
        r'^fix(\(.+\))?[!]?:', r'^hotfix', r'^bugfix', r'^patch',
    ],
    'Changed': [
        r'^refactor(\(.+\))?[!]?:', r'^perf(\(.+\))?[!]?:',
        r'^update', r'^change', r'^modify', r'^improve', r'^optimize',
        r'^chore(\(.+\))?[!]?:', r'^docs(\(.+\))?[!]?:', r'^style(\(.+\))?[!]?:',
        r'^test(\(.+\))?[!]?:', r'^ci(\(.+\))?[!]?:', r'^build(\(.+\))?[!]?:',
    ],
    'Removed': [
        r'^remove', r'^delete', r'^deprecate', r'^drop', r'^revert',
    ],
}


def _run_git(cmd, cwd=None):
    """Run a git command, return stdout or empty string on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=cwd or os.getcwd()
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[ERROR] git command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"       {e}", file=sys.stderr)
        sys.exit(1)


def get_last_tag(repo_path):
    """Return the most recent git tag, or None if no tags exist."""
    tag = _run_git(['git', 'describe', '--tags', '--abbrev=0', '--always'], cwd=repo_path)
    # '--always' returns the commit hash if no tags exist — we want None in that case
    if tag and len(tag) == 40:  # it's a commit hash, not a tag
        return None
    # Check if it's actually a tag vs a hash
    try:
        subprocess.run(
            ['git', 'rev-parse', '--verify', f'refs/tags/{tag}'],
            capture_output=True, check=True, cwd=repo_path
        )
        return tag
    except subprocess.CalledProcessError:
        return None


def get_commits_since(repo_path, since_tag=None):
    """Return list of commit dicts since *since_tag*, or all commits if None."""
    log_fmt = '%H||%s||%an||%ai'
    if since_tag:
        cmd = ['git', 'log', f'{since_tag}..HEAD', f'--format={log_fmt}', '--no-merges']
    else:
        cmd = ['git', 'log', f'--format={log_fmt}', '--no-merges']

    output = _run_git(cmd, cwd=repo_path)
    if not output:
        return []

    commits = []
    for line in output.split('\n'):
        parts = line.split('||', 3)
        if len(parts) == 4:
            hash_, subject, author, date = parts
            commits.append({
                'hash': hash_[:8],
                'subject': subject,
                'author': author,
                'date': date.split()[0],  # YYYY-MM-DD
            })
    return commits


def categorize(subject):
    """Return one of Added / Fixed / Changed / Removed."""
    for category, patterns in CATEGORY_RULES.items():
        for pat in patterns:
            if re.search(pat, subject, re.IGNORECASE):
                return category
    # Heuristic fallback
    low = subject.lower()
    if any(w in low for w in ['add', 'new', 'create', 'implement', 'feat']):
        return 'Added'
    if any(w in low for w in ['fix', 'bug', 'patch', 'hotfix']):
        return 'Fixed'
    if any(w in low for w in ['remove', 'delete', 'deprecate', 'drop', 'revert']):
        return 'Removed'
    return 'Changed'


def build_changelog(commits, repo_name=None):
    """Return formatted CHANGELOG.md string."""
    today = datetime.now().strftime('%Y-%m-%d')
    lines = []
    lines.append('# Changelog')
    if repo_name:
        lines.append(f'\n_Repository: {repo_name}_')
    lines.append('')
    if commits:
        lines.append(f'## [{today}]')
        lines.append('')

        categories = ['Added', 'Fixed', 'Changed', 'Removed']
        grouped = {c: [] for c in categories}
        for c in commits:
            grouped[categorize(c['subject'])].append(c)

        for cat in categories:
            if grouped[cat]:
                lines.append(f'### {cat}')
                lines.append('')
                for c in grouped[cat]:
                    lines.append(f'- {c["subject"]} ([{c["hash"]}]({c["hash"]}))')
                lines.append('')
    else:
        lines.append('_No new commits since last release._')
        lines.append('')
    return '\n'.join(lines)


def find_git_root(path):
    """Walk up from *path* to find a .git directory."""
    path = os.path.abspath(path)
    for _ in range(20):
        if os.path.isdir(os.path.join(path, '.git')):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate a structured CHANGELOG.md from git history.'
    )
    parser.add_argument(
        '--output', '-o', default='CHANGELOG.md',
        help='Output file path (default: CHANGELOG.md)'
    )
    parser.add_argument(
        '--repo', '-r', default=None,
        help='Path to git repository (default: auto-detect from CWD)'
    )
    args = parser.parse_args()

    # Resolve repo path
    if args.repo:
        repo_path = os.path.abspath(args.repo)
    else:
        repo_path = find_git_root(os.getcwd())

    if not repo_path or not os.path.isdir(os.path.join(repo_path, '.git')):
        print("Error: not inside a git repository. Use --repo to specify one.", file=sys.stderr)
        sys.exit(1)

    repo_name = os.path.basename(repo_path)

    # Gather data
    last_tag = get_last_tag(repo_path)
    commits = get_commits_since(repo_path, last_tag)

    if not commits:
        print("No commits found since last release. Nothing to generate.")
        sys.exit(0)

    # Generate & write
    changelog = build_changelog(commits, repo_name)
    output_path = os.path.abspath(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(changelog)

    tag_info = f"since tag '{last_tag}'" if last_tag else "from all commits"
    print(f"✓ Generated: {output_path}")
    print(f"  {len(commits)} commit(s) {tag_info}")
    print(f"  Categories: Added({sum(1 for c in commits if categorize(c['subject'])=='Added')}), "
          f"Fixed({sum(1 for c in commits if categorize(c['subject'])=='Fixed')}), "
          f"Changed({sum(1 for c in commits if categorize(c['subject'])=='Changed')}), "
          f"Removed({sum(1 for c in commits if categorize(c['subject'])=='Removed')})")


if __name__ == '__main__':
    main()
