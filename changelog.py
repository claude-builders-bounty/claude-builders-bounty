#!/usr/bin/env python3
"""
CHANGELOG Generator
Generates a structured CHANGELOG.md from git commit history.
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict


def get_last_tag():
    """Get the most recent git tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits_since_tag(tag=None):
    """Get all commits since the given tag (or all commits if no tag)."""
    if tag:
        range_spec = f'{tag}..HEAD'
    else:
        range_spec = 'HEAD'
    
    try:
        result = subprocess.run(
            ['git', 'log', range_spec, '--pretty=format:%H|%s|%ad', '--date=short'],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) == 3:
                    commits.append({
                        'hash': parts[0][:7],
                        'message': parts[1],
                        'date': parts[2]
                    })
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error fetching commits: {e}", file=sys.stderr)
        return []


def categorize_commit(message):
    """Categorize a commit message into standard categories."""
    message_lower = message.lower()
    
    # Conventional commit prefixes
    if message_lower.startswith(('feat:', 'feature:', 'add:', 'added:')):
        return 'Added'
    elif message_lower.startswith(('fix:', 'bugfix:', 'hotfix:')):
        return 'Fixed'
    elif message_lower.startswith(('change:', 'update:', 'modify:', 'refactor:')):
        return 'Changed'
    elif message_lower.startswith(('remove:', 'delete:', 'deprecate:', 'cleanup:')):
        return 'Removed'
    
    # Keyword-based categorization
    if any(word in message_lower for word in ['add', 'create', 'implement', 'introduce', 'new']):
        return 'Added'
    elif any(word in message_lower for word in ['fix', 'bug', 'resolve', 'correct', 'repair']):
        return 'Fixed'
    elif any(word in message_lower for word in ['update', 'change', 'modify', 'refactor', 'improve', 'enhance']):
        return 'Changed'
    elif any(word in message_lower for word in ['remove', 'delete', 'deprecate', 'drop', 'cleanup', 'clean']):
        return 'Removed'
    
    return 'Changed'  # Default category


def generate_changelog(commits, version=None):
    """Generate formatted CHANGELOG content."""
    if not commits:
        return "# Changelog\n\nNo changes found.\n"
    
    # Group commits by category
    categories = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit['message'])
        categories[category].append(commit)
    
    # Generate changelog
    today = datetime.now().strftime('%Y-%m-%d')
    version_str = version or f"Unreleased ({today})"
    
    lines = [
        "# Changelog",
        "",
        f"## [{version_str}]",
        ""
    ]
    
    # Order categories
    category_order = ['Added', 'Changed', 'Fixed', 'Removed']
    
    for category in category_order:
        if category in categories:
            lines.append(f"### {category}")
            lines.append("")
            for commit in categories[category]:
                # Clean up commit message (remove conventional commit prefix)
                msg = re.sub(r'^(feat|feature|fix|bugfix|add|update|change|remove|refactor|docs|test|chore)(\(.+\))?!?:\s*', '', commit['message'], flags=re.IGNORECASE)
                lines.append(f"- {msg} ({commit['hash']})")
            lines.append("")
    
    return '\n'.join(lines)


def save_changelog(content, filename='CHANGELOG.md'):
    """Save changelog to file."""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Changelog saved to {filename}")
        return True
    except IOError as e:
        print(f"❌ Error saving changelog: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    print("📝 Generating CHANGELOG...")
    
    # Get last tag
    last_tag = get_last_tag()
    if last_tag:
        print(f"📌 Found last tag: {last_tag}")
    else:
        print("📌 No tags found, using all commits")
    
    # Get commits
    commits = get_commits_since_tag(last_tag)
    print(f"🔍 Found {len(commits)} commits")
    
    if not commits:
        print("⚠️  No commits found since last tag")
        return 0
    
    # Generate changelog
    changelog_content = generate_changelog(commits, last_tag)
    
    # Save to file
    if save_changelog(changelog_content):
        print("\n📄 CHANGELOG Preview:")
        print("-" * 50)
        print(changelog_content[:500] + "..." if len(changelog_content) > 500 else changelog_content)
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())