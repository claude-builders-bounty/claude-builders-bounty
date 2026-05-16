#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py              # Current directory
    python3 changelog.py /path/to/repo  # Specific repo
"""

import subprocess
import os
import sys
from datetime import datetime
from collections import OrderedDict

def run_git(cmd, cwd):
    """Run a git command and return stdout"""
    try:
        r = subprocess.run(
            ["git"] + cmd,
            capture_output=True, text=True, timeout=15,
            cwd=cwd
        )
        if r.returncode != 0:
            return None, r.stderr.strip()
        return r.stdout.strip(), None
    except Exception as e:
        return None, str(e)

def get_last_tag(repo_path):
    """Get the latest git tag"""
    out, err = run_git(["describe", "--tags", "--abbrev=0"], repo_path)
    if out:
        return out
    # Try lightweight tags
    out, err = run_git(["tag", "--sort=-version:refname", "--list"], repo_path)
    if out:
        tags = out.split('\n')
        if tags:
            return tags[0]
    return None

def get_commits_since(repo_path, ref):
    """Get commit messages since ref"""
    if ref:
        range_spec = f"{ref}..HEAD"
    else:
        # No tags - get all commits
        range_spec = "HEAD"

    out, err = run_git(
        ["log", range_spec, "--pretty=format:%s|||%b", "--no-merges"],
        repo_path
    )
    if not out:
        return []
    return out.split('\n')

def categorize_commit(msg):
    """Categorize a commit message into Added/Fixed/Changed/Removed"""
    msg_lower = msg.lower().strip()
    
    # Check for breaking changes first
    if msg_lower.startswith('breaking:') or '!' in msg[:20]:
        return 'Changed', msg
    
    # feat: new features
    if msg_lower.startswith('feat') or msg_lower.startswith('feature'):
        clean = msg.split(':', 1)[-1].strip() if ':' in msg else msg
        return 'Added', clean
    
    # fix: bug fixes  
    if msg_lower.startswith('fix') or msg_lower.startswith('bugfix'):
        clean = msg.split(':', 1)[-1].strip() if ':' in msg else msg
        return 'Fixed', clean
    
    # perf/refactor/style
    if any(msg_lower.startswith(p) for p in ['perf', 'refactor', 'style', 'optimize']):
        clean = msg.split(':', 1)[-1].strip() if ':' in msg else msg
        return 'Changed', clean
    
    # remove/deprecate
    if any(msg_lower.startswith(p) for p in ['remove', 'deprecat', 'delete', 'drop']):
        clean = msg.split(':', 1)[-1].strip() if ':' in msg else msg
        return 'Removed', clean
    
    # docs/test/chore - skip
    if any(msg_lower.startswith(p) for p in ['docs', 'test', 'chore', 'ci(', 'build(']):
        return None, None
    
    # Uncategorized
    return 'Changed', msg

def generate_changelog(repo_path="."):
    """Generate CHANGELOG.md"""
    repo_path = os.path.abspath(repo_path)
    
    # Verify it's a git repo
    out, err = run_git(["rev-parse", "--show-toplevel"], repo_path)
    if err:
        return f"❌ 不是 Git 仓库: {err}"
    repo_root = out
    
    # Get repo name
    repo_name = os.path.basename(repo_root)
    
    # Get last tag
    last_tag = get_last_tag(repo_root)
    tag_info = f" since tag `{last_tag}`" if last_tag else " (no tags found - full history)"
    print(f"📦 仓库: {repo_name}")
    print(f"🏷️  标签: {tag_info}")
    
    # Get commits
    commits = get_commits_since(repo_root, last_tag)
    print(f"📝 提交数: {len(commits)}")
    
    if not commits:
        return "没有新的提交"
    
    # Categorize
    categories = OrderedDict([
        ('Added', []),
        ('Fixed', []),
        ('Changed', []),
        ('Removed', []),
    ])
    
    for commit in commits:
        if not commit.strip():
            continue
        parts = commit.split('|||', 1)
        subject = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ''
        
        category, clean_msg = categorize_commit(subject)
        if category and clean_msg:
            entry = clean_msg.capitalize()
            categories[category].append(entry)
    
    # Generate markdown
    today = datetime.now().strftime('%Y-%m-%d')
    new_version = f"v{datetime.now().strftime('%Y%m%d')}"
    
    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append(f"## [{new_version}] - {today}")
    lines.append("")
    
    has_content = False
    for cat, items in categories.items():
        if items:
            has_content = True
            emoji = {'Added': '🚀', 'Fixed': '🐛', 'Changed': '🔧', 'Removed': '🗑️'}
            lines.append(f"### {emoji.get(cat, '')} {cat}")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
    
    if not has_content:
        lines.append("*No categorized changes in this release.*")
        lines.append("")
    
    # Add compare link
    if last_tag:
        lines.append(f"[{new_version}]: https://github.com/{repo_name}/compare/{last_tag}...HEAD")
        lines.append("")
    
    content = '\n'.join(lines)
    
    # Write file
    output_path = os.path.join(repo_root, 'CHANGELOG.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已生成: {output_path}")
    print(f"📄 {len(content)} bytes, {len(categories['Added'])+len(categories['Fixed'])+len(categories['Changed'])+len(categories['Removed'])} 条记录")
    
    # Show preview
    print("\n预览:")
    for line in content.split('\n')[:15]:
        print(f"  {line}")
    
    return content

if __name__ == '__main__':
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    generate_changelog(repo)
