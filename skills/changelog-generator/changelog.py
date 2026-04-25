#!/usr/bin/env python3
"""
CHANGELOG Generator
自动生成结构化的 CHANGELOG.md 从 git history
支持 conventional commits 分类
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict


def run_git_command(args):
    """运行 git 命令并返回输出"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git 命令失败: {e}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("错误: 未找到 git 命令", file=sys.stderr)
        sys.exit(1)


def get_last_tag():
    """获取最新的 git tag"""
    tags = run_git_command(['tag', '--sort=-creatordate'])
    if tags:
        return tags.split('\n')[0]
    return None


def get_commits_since(tag=None):
    """获取指定 tag 之后的 commits"""
    if tag:
        log_range = f"{tag}..HEAD"
    else:
        log_range = "HEAD"
    
    # 格式: hash|subject|body|author|date
    format_str = '%H|%s|%b|%an|%ad'
    output = run_git_command([
        'log', log_range,
        f'--format={format_str}',
        '--date=short'
    ])
    
    if not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 4)
            if len(parts) == 5:
                commits.append({
                    'hash': parts[0][:7],
                    'subject': parts[1],
                    'body': parts[2],
                    'author': parts[3],
                    'date': parts[4]
                })
    
    return commits


def categorize_commit(subject):
    """根据 conventional commit 格式分类 commit"""
    subject_lower = subject.lower()
    
    # 匹配 conventional commit 前缀
    patterns = {
        'Added': [
            r'^feat\([^)]*\):',
            r'^feat:',
            r'^add\b',
            r'^implement\b',
            r'^introduce\b',
            r'^new\b',
        ],
        'Fixed': [
            r'^fix\([^)]*\):',
            r'^fix:',
            r'^bugfix\b',
            r'^hotfix\b',
            r'^patch\b',
            r'^resolve\b',
            r'^correct\b',
        ],
        'Changed': [
            r'^refactor\([^)]*\):',
            r'^refactor:',
            r'^update\b',
            r'^modify\b',
            r'^change\b',
            r'^improve\b',
            r'^enhance\b',
            r'^optimize\b',
            r'^perf\b',
            r'^style\b',
            r'^docs\b',
            r'^doc\b',
            r'^chore\b',
            r'^ci\b',
            r'^test\b',
        ],
        'Removed': [
            r'^remove\b',
            r'^delete\b',
            r'^drop\b',
            r'^deprecate\b',
            r'^clean\b',
            r'^revert\b',
        ],
    }
    
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, subject_lower):
                return category
    
    # 默认分类
    if any(kw in subject_lower for kw in ['fix', 'bug', 'error', 'crash', 'issue']):
        return 'Fixed'
    elif any(kw in subject_lower for kw in ['add', 'new', 'feature', 'support', 'implement']):
        return 'Added'
    elif any(kw in subject_lower for kw in ['remove', 'delete', 'drop', 'clean']):
        return 'Removed'
    else:
        return 'Changed'


def generate_changelog(commits, version=None, repo_url=None):
    """生成 CHANGELOG 内容"""
    if not commits:
        return "# Changelog\n\n没有新的变更。\n"
    
    # 按类别分组
    categories = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit['subject'])
        categories[category].append(commit)
    
    # 生成内容
    lines = []
    lines.append("# Changelog\n")
    
    # 版本标题
    if version:
        lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n")
    else:
        lines.append(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n")
    
    # 按顺序输出类别
    category_order = ['Added', 'Changed', 'Fixed', 'Removed']
    
    for category in category_order:
        if category in categories:
            lines.append(f"\n### {category}\n")
            for commit in categories[category]:
                subject = commit['subject']
                # 清理 conventional commit 前缀用于显示
                clean_subject = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|chore|ci)(\([^)]*\))?:\s*', '', subject, flags=re.IGNORECASE)
                
                if repo_url:
                    lines.append(f"- {clean_subject} ([{commit['hash']}]({repo_url}/commit/{commit['hash']}))")
                else:
                    lines.append(f"- {clean_subject} ({commit['hash']})")
            lines.append("")
    
    return '\n'.join(lines)


def write_changelog(content, filename='CHANGELOG.md'):
    """写入 CHANGELOG 文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ CHANGELOG 已生成: {filename}")
        return True
    except IOError as e:
        print(f"❌ 写入文件失败: {e}", file=sys.stderr)
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='从 git history 生成结构化的 CHANGELOG'
    )
    parser.add_argument(
        '-o', '--output',
        default='CHANGELOG.md',
        help='输出文件名 (默认: CHANGELOG.md)'
    )
    parser.add_argument(
        '-v', '--version',
        help='版本号 (例如: 1.2.3)'
    )
    parser.add_argument(
        '--since',
        help='从指定 tag 开始 (默认: 最新 tag)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='包含所有 commits (不仅限于最新 tag 之后)'
    )
    parser.add_argument(
        '--repo-url',
        help='仓库 URL (用于生成 commit 链接)'
    )
    
    args = parser.parse_args()
    
    # 获取起始点
    if args.all:
        tag = None
    elif args.since:
        tag = args.since
    else:
        tag = get_last_tag()
        if tag:
            print(f"📌 从最新 tag '{tag}' 之后的 commits 生成")
        else:
            print("📌 没有找到 tag，使用所有 commits")
    
    # 获取 commits
    commits = get_commits_since(tag)
    
    if not commits:
        print("⚠️ 没有找到新的 commits")
        return
    
    print(f"📝 找到 {len(commits)} 个 commits")
    
    # 生成 CHANGELOG
    changelog_content = generate_changelog(
        commits,
        version=args.version,
        repo_url=args.repo_url
    )
    
    # 写入文件
    if write_changelog(changelog_content, args.output):
        print(f"\n预览:")
        print("-" * 50)
        print(changelog_content[:500] + "..." if len(changelog_content) > 500 else changelog_content)


if __name__ == '__main__':
    main()
