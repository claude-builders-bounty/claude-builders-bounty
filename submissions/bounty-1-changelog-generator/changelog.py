#!/usr/bin/env python3
"""
📜 CHANGELOG Generator
自动生成结构化的CHANGELOG.md from git history
支持分类：Added / Fixed / Changed / Removed
"""

import subprocess
import re
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple

# 关键词映射到分类
CATEGORY_KEYWORDS = {
    'Added': ['add', 'feat', 'feature', 'new', 'implement', 'introduce', 'create'],
    'Fixed': ['fix', 'bugfix', 'bug', 'repair', 'resolve', 'patch', 'hotfix'],
    'Changed': ['update', 'change', 'modify', 'refactor', 'improve', 'enhance', 'upgrade', 'optimize'],
    'Removed': ['remove', 'delete', 'drop', 'cleanup', 'clean', 'deprecate', 'eliminate']
}

def run_git_command(cmd: List[str]) -> str:
    """执行git命令并返回输出"""
    try:
        result = subprocess.run(
            ['git'] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git命令失败: {' '.join(cmd)}")
        print(f"错误: {e.stderr}")
        return ""

def get_last_tag() -> str:
    """获取最新的git tag"""
    tags = run_git_command(['tag', '--sort=-creatordate'])
    if tags:
        return tags.split('\n')[0]
    return ""

def get_commits_since_tag(tag: str = "") -> List[Dict]:
    """获取自指定tag以来的commits"""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        # 如果没有tag，获取最近30个commits
        range_spec = "-30"
    
    # 格式: hash|date|author|subject
    log_format = "%H|%ad|%an|%s"
    output = run_git_command([
        'log', range_spec,
        f'--format={log_format}',
        '--date=short'
    ])
    
    commits = []
    if output:
        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commits.append({
                        'hash': parts[0][:7],
                        'date': parts[1],
                        'author': parts[2],
                        'subject': parts[3]
                    })
    return commits

def categorize_commit(subject: str) -> str:
    """根据commit message分类"""
    subject_lower = subject.lower()
    
    # 检查是否包含conventional commits前缀
    conventional_pattern = r'^(\w+)(\(.+\))?!?:\s*(.+)$'
    match = re.match(conventional_pattern, subject)
    
    if match:
        prefix = match.group(1).lower()
        if prefix in ['feat', 'feature']:
            return 'Added'
        elif prefix in ['fix']:
            return 'Fixed'
        elif prefix in ['refactor', 'perf', 'chore', 'docs', 'style', 'test']:
            return 'Changed'
        elif prefix in ['remove', 'delete', 'drop']:
            return 'Removed'
    
    # 根据关键词分类
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in subject_lower:
                return category
    
    # 默认分类
    return 'Changed'

def generate_changelog(commits: List[Dict], version: str = "") -> str:
    """生成CHANGELOG内容"""
    if not version:
        version = f"v{datetime.now().strftime('%Y.%m.%d')}"
    
    # 按分类组织commits
    categorized = {
        'Added': [],
        'Changed': [],
        'Fixed': [],
        'Removed': []
    }
    
    for commit in commits:
        category = categorize_commit(commit['subject'])
        categorized[category].append(commit)
    
    # 生成markdown
    lines = [
        "# Changelog",
        "",
        f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}",
        ""
    ]
    
    for category in ['Added', 'Changed', 'Fixed', 'Removed']:
        items = categorized[category]
        if items:
            lines.append(f"### {category}")
            lines.append("")
            for commit in items:
                lines.append(f"- {commit['subject']} ({commit['hash']})")
            lines.append("")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    print("📜 CHANGELOG Generator")
    print("=" * 50)
    
    # 检查是否在git仓库中
    if not os.path.exists('.git'):
        print("❌ 错误：当前目录不是git仓库")
        print("请在一个git仓库中运行此脚本")
        sys.exit(1)
    
    # 获取最新tag
    last_tag = get_last_tag()
    if last_tag:
        print(f"📌 最新tag: {last_tag}")
        print(f"📋 获取自 {last_tag} 以来的commits...")
    else:
        print("⚠️  未找到git tag，获取最近30个commits...")
    
    # 获取commits
    commits = get_commits_since_tag(last_tag)
    print(f"✅ 找到 {len(commits)} 个commits")
    
    if not commits:
        print("⚠️  没有找到新的commits")
        sys.exit(0)
    
    # 生成版本号
    version = ""
    if last_tag:
        # 尝试递增版本号
        match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', last_tag)
        if match:
            major, minor, patch = map(int, match.groups())
            version = f"v{major}.{minor}.{patch + 1}"
        else:
            version = f"{last_tag}-update"
    else:
        version = "v0.1.0"
    
    # 生成changelog
    changelog = generate_changelog(commits, version)
    
    # 写入文件
    output_file = 'CHANGELOG.md'
    
    # 如果文件已存在，保留旧内容并在顶部添加新版本
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            old_content = f.read()
        
        # 找到第一个版本标题的位置
        lines = old_content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('## ['):
                insert_index = i
                break
        
        # 插入新内容
        new_lines = lines[:insert_index] + changelog.split('\n')[2:] + [''] + lines[insert_index:]
        changelog = '\n'.join(new_lines)
    
    with open(output_file, 'w') as f:
        f.write(changelog)
    
    print(f"\n✅ CHANGELOG已生成: {output_file}")
    print(f"📄 版本: {version}")
    print(f"📝 包含 {len(commits)} 个commits")
    print("\n预览:")
    print("-" * 50)
    print(changelog[:500] + "..." if len(changelog) > 500 else changelog)

if __name__ == '__main__':
    main()
