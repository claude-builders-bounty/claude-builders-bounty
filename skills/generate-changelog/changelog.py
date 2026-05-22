#!/usr/bin/env python3
"""
CHANGELOG 自动生成器
从 git 历史生成结构化的 CHANGELOG.md

用法:
    python changelog.py [--version VERSION] [--output FILE] [--repo-url URL]
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict


def run_git_command(args):
    """运行 git 命令并返回输出"""
    result = subprocess.run(
        ['git'] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_last_tag():
    """获取最新的 git tag"""
    try:
        tags = run_git_command(['tag', '--sort=-creatordate'])
        if tags:
            return tags.split('\n')[0]
    except subprocess.CalledProcessError:
        pass
    return None


def get_commits_since(tag=None):
    """获取自上次 tag 以来的 commits"""
    if tag:
        range_spec = f'{tag}..HEAD'
    else:
        # 获取所有 commits
        range_spec = 'HEAD'
    
    log_format = '%H|%s|%an|%ad'
    output = run_git_command([
        'log', range_spec,
        f'--format={log_format}',
        '--date=short'
    ])
    
    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0][:7],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                })
    return commits


def categorize_commit(message):
    """根据 commit message 分类"""
    msg_lower = message.lower()
    
    patterns = {
        'Added': [
            r'^feat\b', r'^add\b', r'^new\b', r'^introduce\b',
            r'^implement\b', r'^create\b'
        ],
        'Fixed': [
            r'^fix\b', r'^bugfix\b', r'^hotfix\b', r'^patch\b',
            r'^resolve\b', r'^correct\b'
        ],
        'Changed': [
            r'^update\b', r'^refactor\b', r'^improve\b', r'^enhance\b',
            r'^optimize\b', r'^rework\b', r'^modify\b'
        ],
        'Removed': [
            r'^remove\b', r'^delete\b', r'^drop\b', r'^clean\b',
            r'^deprecat\b', r'^revert\b'
        ],
        'Security': [
            r'^security\b', r'^vuln\b', r'^cve\b'
        ],
        'Docs': [
            r'^docs?\b', r'^doc\b', r'^readme\b', r'^comment\b'
        ]
    }
    
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, msg_lower):
                return category
    
    return 'Changed'


def generate_changelog(commits, version=None, repo_url=None):
    """生成 CHANGELOG 内容"""
    version = version or 'Unreleased'
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    lines = [
        '# Changelog',
        '',
        f'All notable changes to this project will be documented in this file.',
        '',
        f'## [{version}] - {date_str}',
        ''
    ]
    
    categorized = defaultdict(list)
    for commit in commits:
        cat = categorize_commit(commit['message'])
        categorized[cat].append(commit)
    
    category_order = ['Added', 'Changed', 'Fixed', 'Removed', 'Security', 'Docs']
    
    for category in category_order:
        if category in categorized:
            lines.append(f'### {category}')
            lines.append('')
            for commit in categorized[category]:
                msg = commit['message']
                hash_link = f"`{commit['hash']}`"
                if repo_url:
                    hash_link = f"[`{commit['hash']}`]({repo_url}/commit/{commit['hash']})"
                lines.append(f'- {msg} ({hash_link})')
            lines.append('')
    
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate CHANGELOG from git history')
    parser.add_argument('--version', '-v', help='Version tag (e.g., v1.2.0)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', help='Output file')
    parser.add_argument('--repo-url', '-r', help='Repository URL for commit links')
    parser.add_argument('--since', '-s', help='Get commits since this tag (overrides auto-detect)')
    args = parser.parse_args()
    
    since_tag = args.since
    if not since_tag:
        since_tag = get_last_tag()
    
    try:
        commits = get_commits_since(since_tag)
    except subprocess.CalledProcessError as e:
        print(f'❌ Git error: {e}', file=sys.stderr)
        sys.exit(1)
    
    if not commits:
        print('⚠️  No new commits found')
        sys.exit(0)
    
    print(f'📊 Found {len(commits)} commits (since {since_tag or "initial"})')
    
    changelog = generate_changelog(commits, args.version, args.repo_url)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(changelog)
    
    print(f'✅ CHANGELOG generated: {args.output}')


if __name__ == '__main__':
    main()
