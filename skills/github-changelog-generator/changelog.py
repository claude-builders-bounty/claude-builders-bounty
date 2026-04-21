#!/usr/bin/env python3
"""
CHANGELOG Generator - Advanced version with tag support

Usage:
    python3 changelog.py [output_file] [max_commits]

Features:
    - Automatic categorization by commit type
    - Group by git tags (if available)
    - Support for conventional commits
    - Clean markdown output
"""

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Commit type mapping
TYPE_MAPPING = {
    'feat': 'Added',
    'feature': 'Added',
    'add': 'Added',
    'fix': 'Fixed',
    'bugfix': 'Fixed',
    'bug': 'Fixed',
    'refactor': 'Changed',
    'change': 'Changed',
    'update': 'Changed',
    'improve': 'Changed',
    'style': 'Changed',
    'docs': 'Changed',
    'test': 'Changed',
    'chore': 'Changed',
    'remove': 'Removed',
    'drop': 'Removed',
    'delete': 'Removed',
    'deprecate': 'Removed',
    'revert': 'Removed',
}


def run_command(cmd):
    """Run git command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}", file=sys.stderr)
        return None


def is_git_repo():
    """Check if current directory is a git repository"""
    result = run_command(['git', 'rev-parse', '--show-toplevel'])
    return result is not None


def get_git_log(range_spec='', max_commits=100):
    """Get git log with format: hash|message|date"""
    cmd = ['git', 'log', '--pretty=format:%h|%s|%ai', '--no-merges']
    if range_spec:
        cmd.append(range_spec)
    cmd.extend(['-n', str(max_commits)])
    
    output = run_command(cmd)
    if not output:
        return []
    
    return output.split('\n')


def get_tags():
    """Get all tags sorted by creation date (newest first)"""
    output = run_command(['git', 'tag', '--sort=-creatordate'])
    if not output:
        return []
    return [t for t in output.split('\n') if t]


def classify_commit(message):
    """Classify commit by type prefix"""
    msg_lower = message.lower()
    
    for prefix, category in TYPE_MAPPING.items():
        # Match both "feat:" and "feat(" patterns
        if msg_lower.startswith(f'{prefix}:') or msg_lower.startswith(f'{prefix}('):
            return category
    
    return 'Other'


def parse_commit_line(line):
    """Parse a git log line into components"""
    parts = line.split('|', 2)
    if len(parts) < 2:
        return None
    
    return {
        'hash': parts[0],
        'message': parts[1],
        'date': parts[2] if len(parts) > 2 else ''
    }


def generate_changelog(output_file='CHANGELOG.md', max_commits=100):
    """Generate CHANGELOG.md from git history"""
    
    print("🔍 Generating CHANGELOG from git history...")
    
    # Verify git repo
    if not is_git_repo():
        print("❌ Error: Not in a git repository")
        return False
    
    # Get tags
    tags = get_tags()
    print(f"   Found {len(tags)} tags")
    
    # Organize commits by version
    changelog_data = defaultdict(lambda: defaultdict(list))
    
    if tags:
        # Group commits by tags
        print(f"   Grouping by tags...")
        
        # Commits since latest tag
        latest_commits = get_git_log(f'{tags[0]}..HEAD', max_commits)
        for line in latest_commits:
            commit = parse_commit_line(line)
            if commit:
                category = classify_commit(commit['message'])
                changelog_data['Unreleased'][category].append(
                    f"- {commit['message']} ({commit['hash']})"
                )
        
        # Commits between tags
        for i in range(len(tags)):
            if i == len(tags) - 1:
                # Last tag, get all commits before it
                range_spec = tags[i]
            else:
                range_spec = f'{tags[i+1]}..{tags[i]}'
            
            commits = get_git_log(range_spec, max_commits)
            version = tags[i]
            
            for line in commits:
                commit = parse_commit_line(line)
                if commit:
                    category = classify_commit(commit['message'])
                    changelog_data[version][category].append(
                        f"- {commit['message']} ({commit['hash']})"
                    )
    else:
        # No tags, put everything in Unreleased
        print(f"   No tags found, grouping all as Unreleased...")
        commits = get_git_log('', max_commits)
        
        for line in commits:
            commit = parse_commit_line(line)
            if commit:
                category = classify_commit(commit['message'])
                changelog_data['Unreleased'][category].append(
                    f"- {commit['message']} ({commit['hash']})"
                )
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# Changelog\n\n')
        
        # Sort versions (Unreleased first, then tags)
        versions = sorted(
            changelog_data.keys(),
            key=lambda v: (v != 'Unreleased', v)
        )
        
        for version in versions:
            f.write(f'## [{version}]\n\n')
            
            categories = changelog_data[version]
            
            # Standard order: Added, Fixed, Changed, Removed, Other
            category_order = ['Added', 'Fixed', 'Changed', 'Removed', 'Other']
            
            for category in category_order:
                if category in categories and categories[category]:
                    f.write(f'### {category}\n')
                    for item in categories[category]:
                        f.write(f'{item}\n')
                    f.write('\n')
    
    # Summary
    total = sum(
        len(items)
        for version in changelog_data.values()
        for items in version.values()
    )
    
    print(f"✅ CHANGELOG generated: {output_file}")
    print(f"   Total commits processed: {total}")
    print(f"   Versions: {len(changelog_data)}")
    
    return True


def main():
    """Main entry point"""
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'CHANGELOG.md'
    max_commits = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    success = generate_changelog(output_file, max_commits)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
