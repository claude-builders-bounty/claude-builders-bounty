#!/usr/bin/env python3
"""
Changelog Generator
Generates structured CHANGELOG.md from git history
Usage: python changelog.py [--output CHANGELOG.md] [--since v1.0.0]
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional

class ChangelogGenerator:
    """Generate structured changelog from git commits."""
    
    def __init__(self, since_tag: Optional[str] = None):
        self.since_tag = since_tag
        self.categories = {
            'feat': ('Added', '✨'),
            'fix': ('Fixed', '🐛'),
            'docs': ('Changed', '📝'),
            'style': ('Changed', '💄'),
            'refactor': ('Changed', '♻️'),
            'perf': ('Changed', '⚡'),
            'test': ('Changed', '✅'),
            'chore': ('Changed', '🔧'),
            'build': ('Changed', '🏗️'),
            'ci': ('Changed', '👷'),
            'revert': ('Removed', '⏪'),
            'remove': ('Removed', '🗑️'),
            'delete': ('Removed', '🗑️'),
        }
    
    def run_git_command(self, cmd: List[str]) -> str:
        """Execute git command and return output."""
        result = subprocess.run(
            ['git'] + cmd,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def get_last_tag(self) -> Optional[str]:
        """Get the most recent git tag."""
        try:
            return self.run_git_command(['describe', '--tags', '--abbrev=0'])
        except:
            return None
    
    def get_commits_since(self, since: Optional[str] = None) -> List[Dict]:
        """Get commits since a tag or all commits."""
        format_str = '%H|%s|%an|%ad'
        date_format = '--date=short'
        
        if since:
            cmd = ['log', f'{since}..HEAD', f'--format={format_str}', date_format]
        else:
            cmd = ['log', f'--format={format_str}', date_format]
        
        output = self.run_git_command(cmd)
        
        commits = []
        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commits.append({
                        'hash': parts[0][:7],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
        
        return commits
    
    def parse_conventional_commit(self, message: str) -> Dict:
        """Parse conventional commit format."""
        # Pattern: type(scope): subject or type: subject
        pattern = r'^(\w+)(?:\(([^)]+)\))?!?:\s*(.+)$'
        match = re.match(pattern, message)
        
        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2)
            subject = match.group(3)
            
            # Check for breaking change
            is_breaking = '!' in message[:match.end()] or 'BREAKING CHANGE' in message
            
            return {
                'type': commit_type,
                'scope': scope,
                'subject': subject,
                'breaking': is_breaking,
                'raw': message
            }
        
        # Try to categorize non-conventional commits
        return self.categorize_non_conventional(message)
    
    def categorize_non_conventional(self, message: str) -> Dict:
        """Categorize non-conventional commits."""
        message_lower = message.lower()
        
        # Keywords for categorization
        if any(word in message_lower for word in ['add', 'new', 'feature', 'implement', 'introduce']):
            commit_type = 'feat'
        elif any(word in message_lower for word in ['fix', 'bugfix', 'hotfix', 'resolve', 'patch']):
            commit_type = 'fix'
        elif any(word in message_lower for word in ['doc', 'readme', 'comment', 'guide']):
            commit_type = 'docs'
        elif any(word in message_lower for word in ['refactor', 'rewrite', 'restructure', 'clean']):
            commit_type = 'refactor'
        elif any(word in message_lower for word in ['test', 'spec', 'coverage']):
            commit_type = 'test'
        elif any(word in message_lower for word in ['remove', 'delete', 'drop', 'cleanup']):
            commit_type = 'remove'
        elif any(word in message_lower for word in ['update', 'upgrade', 'bump', 'change']):
            commit_type = 'chore'
        else:
            commit_type = 'chore'
        
        return {
            'type': commit_type,
            'scope': None,
            'subject': message,
            'breaking': 'BREAKING' in message or 'breaking' in message_lower,
            'raw': message
        }
    
    def categorize_commits(self, commits: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize commits into changelog sections."""
        categorized = defaultdict(list)
        
        for commit in commits:
            parsed = self.parse_conventional_commit(commit['message'])
            commit_type = parsed['type']
            
            # Get category (Added, Fixed, Changed, Removed)
            category_info = self.categories.get(commit_type, ('Changed', '📝'))
            category = category_info[0]
            
            categorized[category].append({
                **commit,
                **parsed,
                'emoji': category_info[1]
            })
        
        return dict(categorized)
    
    def generate_changelog(self, output_file: str = 'CHANGELOG.md'):
        """Generate and write changelog."""
        # Determine starting point
        since = self.since_tag or self.get_last_tag()
        
        # Get commits
        commits = self.get_commits_since(since)
        
        if not commits:
            print("No commits found since", since or "beginning")
            return
        
        # Categorize
        categorized = self.categorize_commits(commits)
        
        # Get version info
        version = self.run_git_command(['describe', '--tags', '--abbrev=0']) or 'Unreleased'
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Generate markdown
        lines = [
            '# Changelog',
            '',
            'All notable changes to this project will be documented in this file.',
            '',
            f'## [{version}] - {date}',
            ''
        ]
        
        # Order: Added, Fixed, Changed, Removed
        section_order = ['Added', 'Fixed', 'Changed', 'Removed']
        
        for section in section_order:
            if section in categorized and categorized[section]:
                lines.append(f'### {section}')
                lines.append('')
                
                for commit in categorized[section]:
                    scope = f"**{commit['scope']}**: " if commit['scope'] else ''
                    breaking = ' [BREAKING]' if commit['breaking'] else ''
                    lines.append(f"- {commit['emoji']} {scope}{commit['subject']}{breaking}")
                
                lines.append('')
        
        # Add compare link if we have a previous tag
        if since and since != version:
            lines.append(f'')
            lines.append(f'[Full Changelog](https://github.com/owner/repo/compare/{since}...{version})')
            lines.append('')
        
        # Write to file
        changelog_content = '\n'.join(lines)
        
        # Check if file exists and prepend
        existing_content = ''
        try:
            with open(output_file, 'r') as f:
                existing_content = f.read()
        except FileNotFoundError:
            pass
        
        # Combine (new content first, then existing)
        if existing_content:
            # Skip the header from existing content
            existing_lines = existing_content.split('\n')
            if existing_lines[0] == '# Changelog':
                existing_lines = existing_lines[2:]  # Skip header and blank line
            final_content = changelog_content + '\n' + '\n'.join(existing_lines)
        else:
            final_content = changelog_content
        
        with open(output_file, 'w') as f:
            f.write(final_content)
        
        print(f"✅ Changelog generated: {output_file}")
        print(f"   Commits since {since or 'beginning'}: {len(commits)}")
        print(f"   Categories: {list(categorized.keys())}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate structured CHANGELOG.md from git history'
    )
    parser.add_argument(
        '--output', '-o',
        default='CHANGELOG.md',
        help='Output file path (default: CHANGELOG.md)'
    )
    parser.add_argument(
        '--since', '-s',
        help='Generate changelog since this tag (default: last tag)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Include all commits (ignore tags)'
    )
    
    args = parser.parse_args()
    
    since = None if args.all else args.since
    generator = ChangelogGenerator(since_tag=since)
    generator.generate_changelog(args.output)

if __name__ == '__main__':
    main()
