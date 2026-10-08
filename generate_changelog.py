#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.
Auto-categorizes commits into: Added / Fixed / Changed / Removed
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict


def run_git_command(args):
    """Run a git command and return output."""
    result = subprocess.run(
        ['git'] + args,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error running git {' '.join(args)}: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()


def get_last_tag():
    """Get the most recent git tag."""
    output = run_git_command(['describe', '--tags', '--abbrev=0'])
    if not output:
        # No tags found, get all commits
        return None
    return output


def get_commits_since(tag=None):
    """Get commits since the given tag (or all commits if no tag)."""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    
    # Format: hash|date|message
    output = run_git_command([
        'log', range_spec,
        '--pretty=format:%H|%ad|%s',
        '--date=short'
    ])
    
    if not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0][:7],
                    'date': parts[1],
                    'message': parts[2]
                })
    
    return commits


def categorize_commit(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    message_lower = message.lower()
    
    # Check for conventional commit prefixes first
    if message_lower.startswith(('feat:', 'feature:', 'add:', 'new:')):
        return 'Added'
    elif message_lower.startswith(('fix:', 'bugfix:', 'hotfix:')):
        return 'Fixed'
    elif message_lower.startswith(('remove:', 'delete:', 'drop:')):
        return 'Removed'
    elif message_lower.startswith(('change:', 'update:', 'refactor:', 'improve:', 'enhance:')):
        return 'Changed'
    
    # Check for keywords in message
    if any(word in message_lower for word in ['add', 'new', 'feature', 'introduce', 'implement', 'create']):
        return 'Added'
    elif any(word in message_lower for word in ['fix', 'bug', 'repair', 'resolve', 'correct', 'patch']):
        return 'Fixed'
    elif any(word in message_lower for word in ['remove', 'delete', 'drop', 'eliminate', 'deprecated']):
        return 'Removed'
    elif any(word in message_lower for word in ['update', 'change', 'modify', 'refactor', 'improve', 'enhance', 'upgrade']):
        return 'Changed'
    
    # Default to Changed if can't categorize
    return 'Changed'


def generate_changelog(commits, tag=None):
    """Generate formatted CHANGELOG content."""
    # Group commits by category
    categories = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit['message'])
        categories[category].append(commit)
    
    # Build changelog
    lines = []
    lines.append('# Changelog')
    lines.append('')
    lines.append(f'All notable changes to this project will be documented in this file.')
    lines.append('')
    
    # Get version and date
    version = tag if tag else 'Unreleased'
    today = datetime.now().strftime('%Y-%m-%d')
    
    lines.append(f'## [{version}] - {today}')
    lines.append('')
    
    # Output categories in order
    category_order = ['Added', 'Fixed', 'Changed', 'Removed']
    
    for category in category_order:
        if category in categories and categories[category]:
            lines.append(f'### {category}')
            lines.append('')
            for commit in categories[category]:
                # Clean up the message (remove conventional commit prefix if present)
                message = commit['message']
                message = re.sub(r'^(feat|feature|fix|bugfix|add|new|remove|delete|change|update|refactor|improve|enhance)(\([^)]*\))?:\s*', '', message, flags=re.IGNORECASE)
                lines.append(f'- {message} ({commit["hash"]})')
            lines.append('')
    
    return '\n'.join(lines)


def main():
    """Main function."""
    print('🔍 Checking git repository...')
    
    # Check if we're in a git repo
    if run_git_command(['rev-parse', '--git-dir']) is None:
        print('❌ Error: Not a git repository!', file=sys.stderr)
        sys.exit(1)
    
    print('📋 Fetching last tag...')
    last_tag = get_last_tag()
    if last_tag:
        print(f'   Found tag: {last_tag}')
    else:
        print('   No tags found, using all commits')
    
    print('📥 Fetching commits...')
    commits = get_commits_since(last_tag)
    print(f'   Found {len(commits)} commits')
    
    if not commits:
        print('⚠️  No commits found since last tag.')
        sys.exit(0)
    
    print('📝 Generating CHANGELOG...')
    changelog = generate_changelog(commits, last_tag)
    
    # Write to file
    output_file = 'CHANGELOG.md'
    with open(output_file, 'w') as f:
        f.write(changelog)
    
    print(f'✅ CHANGELOG generated: {output_file}')
    print(f'   Categories:')
    
    # Show summary
    categories = defaultdict(int)
    for commit in commits:
        categories[categorize_commit(commit['message'])] += 1
    
    for cat, count in sorted(categories.items()):
        print(f'     - {cat}: {count}')


if __name__ == '__main__':
    main()
