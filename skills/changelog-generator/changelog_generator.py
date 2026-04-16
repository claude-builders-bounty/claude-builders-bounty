#!/usr/bin/env python3
"""
CHANGELOG Generator - 自动从 git 历史生成结构化 CHANGELOG.md

用法:
    python changelog_generator.py                    # 生成 CHANGELOG.md
    python changelog_generator.py --output NEWS.md   # 输出到指定文件
    python changelog_generator.py --from-tag v1.0.0  # 从指定 tag 开始
    python changelog_generator.py --dry-run          # 仅打印不写文件
    python changelog_generator.py --all              # 包含所有 commits (不过滤 docs/test/chore)
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 分类映射 (基于 Conventional Commits)
CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "style": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "revert": "Removed",
}

# 跳过的类型
SKIP_TYPES = {"docs", "doc", "test", "tests", "chore", "ci", "build"}


def run_git(args: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
    """运行 git 命令并返回结果"""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def get_latest_tag() -> Optional[str]:
    """获取最新的 git tag"""
    ok, output = run_git(["describe", "--tags", "--abbrev=0"])
    return output if ok else None


def get_previous_tag(current_tag: str) -> Optional[str]:
    """获取上一个 tag"""
    ok, output = run_git(["describe", "--tags", "--abbrev=0", f"{current_tag}^"])
    return output if ok else None


def get_commits_between(start: Optional[str], end: str = "HEAD") -> List[Dict]:
    """获取两个引用之间的 commits"""
    if start:
        ok, output = run_git([
            "log", f"{start}..{end}",
            "--pretty=format:%H|%s|%an|%ad",
            "--date=short"
        ])
    else:
        ok, output = run_git([
            "log", end,
            "--pretty=format:%H|%s|%an|%ad",
            "--date=short"
        ])
    
    if not ok or not output:
        return []
    
    commits = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0][:7],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
    return commits


def parse_commit(subject: str) -> Tuple[str, str, str]:
    """
    解析 commit subject, 返回 (type, scope, description)
    支持 Conventional Commits 格式: type(scope): description
    """
    # 匹配: type(scope): description 或 type: description
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$", subject)
    if match:
        return match.group(1).lower(), match.group(2) or "", match.group(3)
    
    # 尝试简单匹配
    parts = subject.split(":", 1)
    if len(parts) == 2:
        return parts[0].lower(), "", parts[1].strip()
    
    return "", "", subject


def categorize_commits(commits: List[Dict], include_all: bool = False) -> Dict[str, List[Dict]]:
    """将 commits 分类"""
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }
    
    for commit in commits:
        commit_type, scope, description = parse_commit(commit["subject"])
        
        # 跳过特定类型
        if commit_type in SKIP_TYPES and not include_all:
            continue
        
        # 确定分类
        category = CATEGORY_MAP.get(commit_type)
        if category:
            commit["scope"] = scope
            commit["description"] = description
            commit["type"] = commit_type
            categories[category].append(commit)
        elif include_all:
            categories["Changed"].append({
                **commit,
                "scope": scope,
                "description": description or commit["subject"],
                "type": commit_type or "other",
            })
    
    return categories


def format_changelog(
    categories: Dict[str, List[Dict]],
    version: str,
    date: str,
    previous_tag: Optional[str] = None,
) -> str:
    """格式化 CHANGELOG 内容"""
    lines = [
        f"# Changelog",
        "",
        f"## [{version}] - {date}",
        "",
    ]
    
    # 添加比较链接
    if previous_tag:
        lines.append(f"[{version}]: https://github.com/compare/{previous_tag}...{version}")
        lines.append("")
    
    for category in ["Added", "Changed", "Fixed", "Removed"]:
        commits = categories.get(category, [])
        if not commits:
            continue
        
        lines.append(f"### {category}")
        for commit in commits:
            scope = f"**{commit['scope']}**: " if commit.get("scope") else ""
            lines.append(f"- {scope}{commit['description']} ([{commit['hash']}])")
        lines.append("")
    
    return "\n".join(lines)


def prepend_to_changelog(new_content: str, changelog_path: Path) -> str:
    """将新内容插入到现有 CHANGELOG 开头"""
    if not changelog_path.exists():
        return new_content
    
    existing = changelog_path.read_text(encoding="utf-8")
    
    # 找到插入位置 (第一个 ## 标题之前)
    lines = existing.split("\n")
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            insert_pos = i
            break
    
    # 构建新内容
    header = "\n".join(lines[:insert_pos])
    rest = "\n".join(lines[insert_pos:])
    
    return f"{header}\n\n{new_content}\n{rest}".strip() + "\n"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CHANGELOG from git history")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--from-tag", help="Start from this tag")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--all", action="store_true", help="Include docs/test/chore commits")
    parser.add_argument("--version", help="Version number (default: latest tag or 'Unreleased')")
    args = parser.parse_args()
    
    # 检查是否在 git 仓库中
    ok, _ = run_git(["rev-parse", "--git-dir"])
    if not ok:
        print("错误: 当前目录不是 git 仓库", file=sys.stderr)
        sys.exit(1)
    
    # 获取版本信息
    latest_tag = get_latest_tag()
    version = args.version or latest_tag or "Unreleased"
    
    # 确定 commit 范围
    if args.from_tag:
        start_tag = args.from_tag
    elif latest_tag:
        start_tag = get_previous_tag(latest_tag)
    else:
        start_tag = None
    
    # 获取 commits
    print(f"获取 commits: {start_tag or '开始'} .. HEAD", file=sys.stderr)
    commits = get_commits_between(start_tag)
    
    if not commits:
        print("没有找到 commits", file=sys.stderr)
        sys.exit(0)
    
    print(f"找到 {len(commits)} 个 commits", file=sys.stderr)
    
    # 分类
    categories = categorize_commits(commits, include_all=args.all)
    
    # 统计
    total = sum(len(c) for c in categories.values())
    print(f"分类完成: {total} 个有效 commits", file=sys.stderr)
    
    # 生成内容
    date = datetime.now().strftime("%Y-%m-%d")
    content = format_changelog(categories, version, date, start_tag)
    
    # 输出
    if args.dry_run:
        print(content)
    else:
        output_path = Path(args.output)
        
        # 如果文件存在,插入到开头
        if output_path.exists():
            content = prepend_to_changelog(content, output_path)
        
        output_path.write_text(content, encoding="utf-8")
        print(f"已写入: {output_path}", file=sys.stderr)
        print(f"  Added: {len(categories['Added'])}", file=sys.stderr)
        print(f"  Fixed: {len(categories['Fixed'])}", file=sys.stderr)
        print(f"  Changed: {len(categories['Changed'])}", file=sys.stderr)
        print(f"  Removed: {len(categories['Removed'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
