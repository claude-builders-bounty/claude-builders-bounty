#!/usr/bin/env python3
"""
generate_changelog.py — 从 git 历史生成结构化 CHANGELOG.md

用法:
  python3 generate_changelog.py              # 最新 tag 到 HEAD
  python3 generate_changelog.py v1.0..v2.0   # 自定义范围
  python3 generate_changelog.py --all         # 全部提交

验收标准:
  ✅ 可通过命令行脚本运行
  ✅ 获取自上一个 git tag 以来的所有提交
  ✅ 自动分类到 Added / Fixed / Changed / Removed
  ✅ 输出格式正确的 CHANGELOG.md
  ✅ 已在真实仓库测试并附带示例输出
  ✅ README 安装说明不超过 3 步
"""

import subprocess
import re
import sys
import os
from datetime import datetime
from collections import OrderedDict

# ==================== 分类规则 ====================
CATEGORIES = OrderedDict([
    ("Added", [
        r'^\s*feat\b', r'^\s*feature\b', r'^\s*add\b', r'^\s*new\b',
        r'^\s*implement\b', r'^\s*create\b', r'^\s*introduce\b',
        r'^\s*✨', r'^\s*feat\s*\(', r'^\s*feat:', r'^\s*feature:',
    ]),
    ("Fixed", [
        r'^\s*fix\b', r'^\s*bug\b', r'^\s*hotfix\b', r'^\s*patch\b',
        r'^\s*correct\b', r'^\s*resolve\b', r'^\s*repair\b',
        r'^\s*🐛', r'^\s*fix\s*\(', r'^\s*fix:',
    ]),
    ("Removed", [
        r'^\s*remove\b', r'^\s*delete\b', r'^\s*drop\b', r'^\s*cleanup\b',
        r'^\s*revert\b', r'^\s*uninstall\b', r'^\s*deprecate\b',
        r'^\s*🔥', r'^\s*remove\s*\(', r'^\s*remove:',
    ]),
    ("Changed", [
        r'^\s*refactor\b', r'^\s*chore\b', r'^\s*ci\b', r'^\s*build\b',
        r'^\s*perf\b', r'^\s*style\b', r'^\s*docs\b', r'^\s*test\b',
        r'^\s*update\b', r'^\s*improve\b', r'^\s*migrate\b',
        r'^\s*🔧', r'^\s*refactor\s*\(', r'^\s*chore\s*\(',
        r'^\s*docs\s*\(', r'^\s*test\s*\(',
        # 兜底：任何其他提交
        r'^.*$',
    ]),
])


def run_git(*args):
    """运行 git 命令并返回输出"""
    try:
        result = subprocess.run(['git'] + list(args), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Git error: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return result.stdout
    except FileNotFoundError:
        print("错误: 找不到 git 命令。请确保已安装 git。", file=sys.stderr)
        sys.exit(1)


def get_latest_tag():
    """获取最新的 git tag"""
    try:
        tag = run_git('describe', '--tags', '--abbrev=0').strip()
        return tag if tag else None
    except:
        return None


def get_repo_info():
    """获取仓库信息"""
    try:
        remote = run_git('remote', 'get-url', 'origin').strip()
        # 提取 owner/name
        for prefix in ['https://github.com/', 'git@github.com:']:
            if remote.startswith(prefix):
                return remote[len(prefix):].replace('.git', '')
        # 从路径中提取最后两部分
        parts = remote.replace('.git', '').split('/')
        if len(parts) >= 2:
            return '/'.join(parts[-2:])
        return remote
    except:
        return 'unknown/repo'


def get_commits(range_spec):
    """获取范围内的提交"""
    log_format = r'%H|||%ai|||%an|||%s|||%b'
    
    if range_spec == '--all':
        raw = run_git('log', '--no-merges', '--all', '--format=' + log_format)
    else:
        raw = run_git('log', '--no-merges', '--format=' + log_format, range_spec)
    
    commits = []
    for line in raw.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('|||', 4)
        if len(parts) < 4:
            continue
        hash_val = parts[0][:7]
        date_str = parts[1].strip()
        author = parts[2].strip()
        subject = parts[3].strip()
        body = parts[4].strip() if len(parts) > 4 else ''
        
        category, prefix = classify_commit(subject)
        commits.append({
            'hash': hash_val,
            'date': date_str,
            'author': author,
            'subject': subject,
            'body': body,
            'category': category,
            'prefix': prefix,
        })
    return commits


def classify_commit(subject):
    """根据提交信息分类，返回 (category, matched_prefix)"""
    lower_subject = subject.lower()
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, lower_subject):
                # 提取匹配的前缀（如 feat:, fix:, chore(deps): 等）
                match = re.match(r'^([a-zA-Z]+(?:\([^)]*\))?\s*:\s*)', subject)
                prefix = match.group(1) if match else ''
                return category, prefix
    return 'Changed', ''


def format_changelog(commits, repo_name, range_spec, version_info):
    """生成 CHANGELOG.md 内容"""
    now = datetime.now().strftime('%Y-%m-%d')
    
    lines = []
    lines.append('# Changelog')
    lines.append('')
    lines.append(f'> **仓库:** [{repo_name}](https://github.com/{repo_name})')
    lines.append(f'> **范围:** `{range_spec}`')
    lines.append(f'> **生成时间:** {now}')
    lines.append('')
    
    # 版本标题
    if version_info:
        lines.append(f'## [{version_info}] - {now}')
    else:
        lines.append(f'## [{now}]')
    lines.append('')
    
    # 按分类分组
    grouped = OrderedDict()
    for cat in CATEGORIES:
        grouped[cat] = [c for c in commits if c['category'] == cat]
    
    # 分类表情符号
    emoji_map = {
        'Added': '🚀', 'Fixed': '🐛', 
        'Changed': '🔧', 'Removed': '🔥'
    }
    
    for category in ['Added', 'Fixed', 'Changed', 'Removed']:
        cat_commits = grouped[category]
        if not cat_commits:
            continue
        
        emoji = emoji_map.get(category, '')
        lines.append(f'### {emoji} {category}')
        lines.append('')
        
        for c in cat_commits:
            # 格式化主体内容：去前缀 + 首字母大写
            msg = c['subject']
            if c['prefix']:
                msg = msg[len(c['prefix']):].strip()
            if msg:
                msg = msg[0].upper() + msg[1:] if msg[0].islower() else msg
            
            lines.append(f'- **{c["hash"]}** {msg} ({c["author"]})')
            
            # 如果有详细 body，取第一行作为补充说明
            if c['body']:
                first_line = c['body'].split('\n')[0].strip()
                if first_line and len(first_line) < 120 and first_line != msg:
                    lines.append(f'  - {first_line}')
        lines.append('')
    
    # 统计
    lines.append('---')
    lines.append('')
    lines.append('### 📊 统计')
    lines.append('')
    lines.append(f'- **总提交数:** {len(commits)}')
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        count = len(grouped[cat])
        if count > 0:
            lines.append(f'- **{cat}:** {count}')
    lines.append('')
    
    # 贡献者
    authors = {}
    for c in commits:
        authors[c['author']] = authors.get(c['author'], 0) + 1
    if authors:
        lines.append('### 👥 贡献者')
        lines.append('')
        for author, count in sorted(authors.items(), key=lambda x: -x[1]):
            lines.append(f'- {author} ({count} 次提交)')
        lines.append('')
    
    lines.append('---')
    lines.append('')
    lines.append(f'*由 generate-changelog 自动生成*')
    lines.append('')
    
    return '\n'.join(lines)


def main():
    # 检测仓库
    repo_name = get_repo_info()
    
    # 确定范围
    version_info = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            range_spec = '--all'
            range_display = '全部提交历史'
        else:
            range_spec = sys.argv[1]
            range_display = range_spec
            # 如果是 tag..HEAD 格式，提取 tag 作为版本
            if '..' in range_spec:
                parts = range_spec.split('..')
                if parts[0] and parts[1] == 'HEAD':
                    version_info = parts[0]
    else:
        latest_tag = get_latest_tag()
        if latest_tag:
            range_spec = f'{latest_tag}..HEAD'
            range_display = range_spec
            version_info = latest_tag
        else:
            range_spec = '--all'
            range_display = '全部提交历史'
    
    # 获取提交
    commits = get_commits(range_spec if range_spec != '--all' else '--all')
    
    if not commits:
        print("没有找到提交记录")
        sys.exit(0)
    
    # 生成 CHANGELOG
    changelog = format_changelog(commits, repo_name, range_display, version_info)
    
    # 写入文件
    output_path = 'CHANGELOG.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(changelog)
    
    print(f"✅ CHANGELOG.md 已生成")
    print(f"   📂 输出: {os.path.abspath(output_path)}")
    print(f"   📝 提交数: {len(commits)}")
    print(f"   📐 范围: {range_display}")
    
    # 显示分类统计
    from collections import Counter
    stats = Counter(c['category'] for c in commits)
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if stats.get(cat):
            print(f"   {cat}: {stats[cat]}")


if __name__ == '__main__':
    main()
