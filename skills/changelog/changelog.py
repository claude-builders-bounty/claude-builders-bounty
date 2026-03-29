#!/usr/bin/env python3
"""
changelog.py — Cross-platform CHANGELOG generator
Part of the Claude Code SKILL: /generate-changelog

Usage:
    python3 changelog.py                           # auto-detect tag
    python3 changelog.py --repo /path/to/repo      # specify repo
    python3 changelog.py --output CHANGELOG.md     # output file
    python3 changelog.py --since v1.0.0            # since tag
    python3 changelog.py --all                     # all commits

Requirements: Python 3.6+
"""

import subprocess
import argparse
import sys
import re
from datetime import datetime
from pathlib import Path


def run_git(cmd: str, cwd: str) -> tuple[str, bool]:
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Git command timed out", False
    except Exception as e:
        return str(e), False


def get_last_tag(repo_path: str) -> str | None:
    output, ok = run_git("git describe --tags --abbrev=0", repo_path)
    return output if ok and output else None


def get_commit_range_since(tag: str | None, repo_path: str) -> list[str]:
    if tag:
        cmd = f'git log {tag}..HEAD --format="%s"'
    else:
        cmd = 'git log --format="%s" -50'
    output, ok = run_git(cmd, repo_path)
    if not ok or not output:
        return []
    return [line.strip() for line in output.split('\n') if line.strip()]


def categorize(subject: str) -> str:
    s = subject.lower()
    if s.startswith(('feat', 'add')):
        return 'Added'
    elif s.startswith('fix'):
        return 'Fixed'
    elif any(s.startswith(p) for p in ('refactor!', 'breaking')):
        return 'Removed'
    elif any(s.startswith(p) for p in ('chore', 'ci', 'build', 'deps', 'test', 'docs', 'style', 'perf')):
        return 'Changed'
    return 'Changed'


def generate(repo_path: str, since_tag: str | None, output_file: str, all_commits: bool = False):
    commits = get_commit_range_since(None if all_commits else since_tag, repo_path)
    
    categories: dict[str, list[str]] = {
        'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []
    }
    
    for commit in commits:
        if not commit or commit.startswith('Merge '):
            continue
        cat = categorize(commit)
        categories[cat].append(f"- {commit}")
    
    today = datetime.now().strftime('%Y-%m-%d')
    version = f"[{since_tag}]" if since_tag else "[Unreleased]"
    
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        f"## {version} - {today}",
        "",
    ]
    
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            lines.append(f"### {cat}")
            lines.extend(categories[cat])
            lines.append("")
    
    # Remove trailing blank
    while lines and not lines[-1]:
        lines.pop()
    
    output_path = Path(repo_path) / output_file
    existing_lines: list[str] = []
    
    if output_path.exists():
        content = output_path.read_text(encoding='utf-8')
        # Find where the existing content starts (after first ## [version])
        parts = re.split(r'^## \[', content, flags=re.MULTILINE)
        if len(parts) > 1:
            existing_lines = [f"## [" + p for p in parts[1:] if p.strip()]
    
    final_lines = lines
    if existing_lines:
        final_lines.extend(["", ""] + existing_lines)
    
    output_path.write_text('\n'.join(final_lines) + '\n', encoding='utf-8')
    
    print(f"[OK] Generated: {output_path}")
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        count = len(categories[cat])
        if count:
            print(f"  * {cat}: {count} entries")
    
    return output_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a structured CHANGELOG.md from git history'
    )
    parser.add_argument('--repo', default='.', help='Repository path')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output file')
    parser.add_argument('--since', dest='since_tag', default=None, help='Tag to start from')
    parser.add_argument('--all', dest='all_commits', action='store_true', help='All commits (no tag)')
    args = parser.parse_args()
    
    repo = Path(args.repo).resolve()
    if not (repo / '.git').exists():
        print(f"Error: Not a git repository: {repo}")
        sys.exit(1)
    
    if not args.since_tag and not args.all_commits:
        args.since_tag = get_last_tag(str(repo))
        if args.since_tag:
            print(f"Detected tag: {args.since_tag}")
        else:
            print("No tags found — using --all (last 50 commits)")
            args.all_commits = True
    
    generate(str(repo), args.since_tag, args.output, args.all_commits)
