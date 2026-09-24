#!/usr/bin/env python3
"""Generate structured CHANGELOG.md from git history."""

import subprocess
import sys
from datetime import date


def get_commits_since_last_tag():
    """Fetch commits since last git tag, or all commits if no tags exist."""
    try:
        # Try to get last tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            last_tag = result.stdout.strip()
            cmd = ["git", "log", "--oneline", f"{last_tag}..HEAD"]
        else:
            # No tags, get all commits
            cmd = ["git", "log", "--oneline"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception as e:
        print(f"Error fetching commits: {e}", file=sys.stderr)
        return []


def categorize_commit(commit_line):
    """Categorize a commit line into Added/Fixed/Changed/Removed/Other."""
    if not commit_line:
        return "other", ""
    
    parts = commit_line.split(' ', 1)
    if len(parts) < 2:
        return "other", commit_line
    
    commit_hash = parts[0]
    message = parts[1]
    lower_msg = message.lower()
    
    if any(kw in lower_msg for kw in ['add', 'new', 'feature', 'implement']):
        return "added", f"- {commit_hash} {message}"
    elif any(kw in lower_msg for kw in ['fix', 'bug', 'patch', 'resolve']):
        return "fixed", f"- {commit_hash} {message}"
    elif any(kw in lower_msg for kw in ['update', 'change', 'modify', 'refactor', 'improve']):
        return "changed", f"- {commit_hash} {message}"
    elif any(kw in lower_msg for kw in ['remove', 'delete', 'drop', 'deprecate']):
        return "removed", f"- {commit_hash} {message}"
    else:
        return "other", f"- {commit_hash} {message}"


def generate_changelog(commits):
    """Generate formatted changelog content."""
    categories = {"added": [], "fixed": [], "changed": [], "removed": [], "other": []}
    
    for commit in commits:
        if commit:
            cat, entry = categorize_commit(commit)
            categories[cat].append(entry)
    
    lines = [
        "# Changelog",
        "",
        f"## [{date.today().isoformat()}]",
        ""
    ]
    
    section_order = ["added", "fixed", "changed", "removed", "other"]
    section_titles = {
        "added": "### Added",
        "fixed": "### Fixed",
        "changed": "### Changed",
        "removed": "### Removed",
        "other": "### Other Changes"
    }
    
    for cat in section_order:
        if categories[cat]:
            lines.append(section_titles[cat])
            lines.extend(categories[cat])
            lines.append("")
    
    return '\n'.join(lines)


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    
    commits = get_commits_since_last_tag()
    if not commits:
        print("No commits found.")
        sys.exit(0)
    
    changelog_content = generate_changelog(commits)
    
    with open(output_file, 'w') as f:
        f.write(changelog_content)
    
    print(f"CHANGELOG.md generated at {output_file}")
    print(f"Total commits processed: {len(commits)}")


if __name__ == "__main__":
    main()
