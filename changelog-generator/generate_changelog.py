#!/usr/bin/env python3
"""
CHANGELOG Generator
Automatically generates a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py [--output CHANGELOG.md] [--from-tag TAG]
"""

import subprocess
import argparse
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional


def run_git_command(cmd: list[str]) -> str:
    """Run a git command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {result.stderr}")
    return result.stdout.strip()


def get_last_tag() -> Optional[str]:
    """Get the most recent git tag."""
    try:
        return run_git_command(["git", "describe", "--tags", "--abbrev=0"])
    except RuntimeError:
        return None


def get_commits_since_tag(tag: Optional[str] = None) -> list[dict]:
    """Get commits since the given tag (or all commits if no tag)."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%an|%ad", "--date=short"]
    else:
        cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ad", "--date=short"]
    
    output = run_git_command(cmd)
    if not output:
        return []
    
    commits = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:7],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })
    
    return commits


def categorize_commit(subject: str) -> str:
    """Categorize a commit based on conventional commit prefixes."""
    subject_lower = subject.lower()
    
    # Conventional commit prefixes
    if subject_lower.startswith(("feat:", "feat(", "feature:", "add:", "新增:", "添加:")):
        return "Added"
    elif subject_lower.startswith(("fix:", "fix(", "bugfix:", "bug:", "修复:", "fixes:")):
        return "Fixed"
    elif subject_lower.startswith(("refactor:", "refactor(", "improve:", "优化:", "update:", "change:", "修改:", "更改:")):
        return "Changed"
    elif subject_lower.startswith(("remove:", "delete:", "drop:", "删除:", "移除:")):
        return "Removed"
    elif subject_lower.startswith(("doc:", "docs:", "documentation:", "文档:")):
        return "Documentation"
    elif subject_lower.startswith(("test:", "tests:", "testing:")):
        return "Tests"
    elif subject_lower.startswith(("chore:", "build:", "ci:", "style:")):
        return "Maintenance"
    
    # Heuristic categorization based on keywords
    add_keywords = ["add", "新增", "添加", "implement", "实现", "create", "创建", "introduce", "support"]
    fix_keywords = ["fix", "修复", "bug", "resolve", "解决", "correct", "patch"]
    change_keywords = ["update", "更新", "change", "修改", "improve", "改进", "optimize", "优化", "refactor", "重构", "enhance"]
    remove_keywords = ["remove", "删除", "delete", "移除", "drop", "deprecate", "废弃"]
    
    for keyword in add_keywords:
        if keyword in subject_lower:
            return "Added"
    for keyword in fix_keywords:
        if keyword in subject_lower:
            return "Fixed"
    for keyword in change_keywords:
        if keyword in subject_lower:
            return "Changed"
    for keyword in remove_keywords:
        if keyword in subject_lower:
            return "Removed"
    
    return "Other"


def clean_subject(subject: str) -> str:
    """Clean up commit subject for changelog."""
    # Remove conventional commit prefix
    subject = re.sub(r"^(feat|fix|refactor|docs|test|chore|style|build|ci)(\([^)]+\))?:\s*", "", subject)
    subject = re.sub(r"^(add|remove|update|change|delete|improve|fix|bug|feature|bugfix):\s*", "", subject, flags=re.IGNORECASE)
    
    # Remove PR/issue references from the end (keep them for links later)
    # Clean up extra spaces
    subject = re.sub(r"\s+", " ", subject).strip()
    
    return subject


def extract_issue_refs(subject: str) -> list[str]:
    """Extract issue/PR references from commit subject."""
    refs = re.findall(r"#(\d+)", subject)
    return refs


def generate_changelog(commits: list[dict], version: str, previous_tag: Optional[str] = None) -> str:
    """Generate CHANGELOG.md content."""
    # Categorize commits
    categories = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit["subject"])
        categories[category].append(commit)
    
    # Build changelog
    lines = []
    lines.append(f"# Changelog")
    lines.append("")
    lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    
    # Order of categories
    category_order = ["Added", "Fixed", "Changed", "Removed", "Documentation", "Tests", "Maintenance", "Other"]
    
    for category in category_order:
        if category in categories and categories[category]:
            lines.append(f"### {category}")
            lines.append("")
            for commit in categories[category]:
                clean_msg = clean_subject(commit["subject"])
                refs = extract_issue_refs(commit["subject"])
                
                if refs:
                    ref_links = " ".join([f"[#{r}](https://github.com/OWNER/REPO/issues/{r})" for r in refs])
                    lines.append(f"- {clean_msg} ({ref_links})")
                else:
                    lines.append(f"- {clean_msg}")
            lines.append("")
    
    # Add compare link if there's a previous tag
    if previous_tag:
        lines.append(f"[{version}]: https://github.com/OWNER/REPO/compare/{previous_tag}...HEAD")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--from-tag", "-t", help="Start from this tag (default: last tag)")
    parser.add_argument("--version", "-v", default="Unreleased", help="Version number for this release")
    parser.add_argument("--append", "-a", action="store_true", help="Append to existing changelog")
    
    args = parser.parse_args()
    
    # Get the tag to start from
    if args.from_tag:
        start_tag = args.from_tag
    else:
        start_tag = get_last_tag()
    
    if start_tag:
        print(f"📝 Generating changelog from tag: {start_tag}")
    else:
        print("📝 Generating changelog from all commits (no tags found)")
    
    # Get commits
    commits = get_commits_since_tag(start_tag)
    
    if not commits:
        print("⚠️  No commits found since last tag")
        return
    
    print(f"📊 Found {len(commits)} commits")
    
    # Categorize for stats
    categories = defaultdict(list)
    for commit in commits:
        categories[categorize_commit(commit["subject"])].append(commit)
    
    print("\n📈 Categories:")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"   {cat}: {len(items)}")
    
    # Generate changelog
    changelog = generate_changelog(commits, args.version, start_tag)
    
    # Write output
    output_path = Path(args.output)
    
    if args.append and output_path.exists():
        existing = output_path.read_text()
        # Insert new content after the header
        if "\n## " in existing:
            header_end = existing.index("\n## ")
            new_content = existing[:header_end + 1] + "\n" + changelog.replace("# Changelog\n\n", "") + existing[header_end + 1:]
        else:
            new_content = changelog + "\n\n" + existing
        output_path.write_text(new_content)
        print(f"\n✅ Appended to {output_path}")
    else:
        output_path.write_text(changelog)
        print(f"\n✅ Written to {output_path}")
    
    # Preview
    print("\n" + "=" * 60)
    print("📖 Preview:")
    print("=" * 60)
    print(changelog[:1000])
    if len(changelog) > 1000:
        print("\n... (truncated)")


if __name__ == "__main__":
    main()