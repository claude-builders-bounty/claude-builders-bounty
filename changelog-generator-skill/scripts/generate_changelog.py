#!/usr/bin/env python3
"""
CHANGELOG Generator - Generate structured CHANGELOG.md from git history
Author: BetsyMalthus
Version: 1.0.0
"""

import subprocess
import re
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class ChangelogGenerator:
    """Generate structured CHANGELOG from git history"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
        self.categories = {
            'added': ['feat', 'add', 'new', 'implement', 'create'],
            'fixed': ['fix', 'bug', 'patch', 'resolve', 'correct'],
            'changed': ['change', 'update', 'modify', 'refactor', 'improve', 'optimize'],
            'removed': ['remove', 'delete', 'deprecate', 'drop', 'obsolete']
        }
        self.ignore_patterns = [r'^Merge', r'^Revert', r'^WIP', r'^Initial commit']
        
    def run_git_command(self, args: List[str]) -> str:
        """Run git command and return output"""
        try:
            cmd = ['git', '-C', self.repo_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(cmd)}", file=sys.stderr)
            print(f"Error: {e.stderr}", file=sys.stderr)
            return ""
    
    def get_last_tag(self) -> Optional[str]:
        """Get the most recent git tag"""
        tags = self.run_git_command(['tag', '--sort=-v:refname'])
        if tags:
            # Get the first tag (most recent)
            return tags.split('\n')[0]
        return None
    
    def get_commits_since_tag(self, tag: Optional[str] = None) -> List[Dict]:
        """Get commits since a specific tag (or all commits if no tag)"""
        if tag:
            cmd = ['log', f'{tag}..HEAD', '--oneline', '--no-merges']
        else:
            cmd = ['log', '--oneline', '--no-merges']
            
        output = self.run_git_command(cmd)
        commits = []
        
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            # Parse commit hash and message
            match = re.match(r'^([a-f0-9]{7,})\s+(.+)$', line)
            if match:
                commit_hash = match.group(1)
                message = match.group(2)
                
                # Get full commit details
                details = self.run_git_command(['show', '--quiet', '--format=%H|%an|%ae|%ad|%s', commit_hash])
                if details:
                    parts = details.split('|')
                    if len(parts) >= 5:
                        full_hash = parts[0]
                        author = parts[1]
                        email = parts[2]
                        date = parts[3]
                        full_message = parts[4]
                        
                        commits.append({
                            'hash': commit_hash,
                            'full_hash': full_hash,
                            'message': message,
                            'full_message': full_message,
                            'author': author,
                            'email': email,
                            'date': date,
                            'category': self.categorize_commit(full_message)
                        })
        
        return commits
    
    def categorize_commit(self, message: str) -> str:
        """Categorize commit message into Added/Fixed/Changed/Removed"""
        message_lower = message.lower()
        
        # Check ignore patterns first
        for pattern in self.ignore_patterns:
            if re.match(pattern, message, re.IGNORECASE):
                return 'ignored'
        
        # Check each category
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return category
        
        # Default to 'changed' if no match
        return 'changed'
    
    def generate_changelog(self, tag: Optional[str] = None, include_all: bool = False) -> Dict:
        """Generate structured changelog data"""
        commits = self.get_commits_since_tag(tag)
        
        # Group by category
        categorized = {cat: [] for cat in self.categories.keys()}
        categorized['other'] = []
        
        for commit in commits:
            category = commit['category']
            if category in categorized:
                categorized[category].append(commit)
            else:
                categorized['other'].append(commit)
        
        # Get current tag info
        current_tag = self.get_last_tag()
        tag_date = None
        if current_tag:
            tag_info = self.run_git_command(['log', '-1', '--format=%ad', '--date=short', current_tag])
            if tag_info:
                tag_date = tag_info
        
        return {
            'generated_at': datetime.now().isoformat(),
            'repository': self.repo_path,
            'current_tag': current_tag,
            'tag_date': tag_date,
            'since_tag': tag,
            'commit_count': len(commits),
            'commits': categorized
        }
    
    def format_markdown(self, data: Dict) -> str:
        """Format changelog data as Markdown"""
        lines = [
            "# Changelog",
            "",
            "All notable changes to this project will be documented in this file.",
            "",
            "## [Unreleased]",
            ""
        ]
        
        # Add commits by category
        for category in ['added', 'fixed', 'changed', 'removed']:
            commits = data['commits'][category]
            if commits:
                lines.append(f"### {category.capitalize()}")
                for commit in commits:
                    # Clean up message for display
                    message = commit['message']
                    # Remove category prefixes if present
                    for prefix in ['feat:', 'fix:', 'chore:', 'docs:', 'style:', 'refactor:', 'test:', 'build:']:
                        if message.lower().startswith(prefix):
                            message = message[len(prefix):].strip()
                    lines.append(f"- {message} ({commit['hash']})")
                lines.append("")
        
        # Add previous release section if we have a tag
        if data['current_tag'] and data['tag_date']:
            lines.append(f"## [{data['current_tag']}] - {data['tag_date']}")
            lines.append("")
            lines.append("*Previous release*")
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_json(self, data: Dict) -> str:
        """Format changelog data as JSON"""
        return json.dumps(data, indent=2)
    
    def format_text(self, data: Dict) -> str:
        """Format changelog data as plain text"""
        lines = []
        lines.append(f"CHANGELOG for {data['repository']}")
        lines.append(f"Generated: {data['generated_at']}")
        lines.append(f"Commits since {data['since_tag'] or 'beginning'}: {data['commit_count']}")
        lines.append("")
        
        for category in ['added', 'fixed', 'changed', 'removed']:
            commits = data['commits'][category]
            if commits:
                lines.append(f"{category.upper()}:")
                for commit in commits:
                    lines.append(f"  - {commit['message']} ({commit['hash']})")
                lines.append("")
        
        return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate structured CHANGELOG from git history')
    parser.add_argument('repo_path', nargs='?', default='.', help='Path to git repository')
    parser.add_argument('--since-tag', help='Generate from specific tag (default: last tag)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', help='Output file path')
    parser.add_argument('--format', choices=['markdown', 'json', 'text'], default='markdown', 
                       help='Output format')
    parser.add_argument('--all', action='store_true', help='Include all commits (not just since last tag)')
    
    args = parser.parse_args()
    
    # Validate repository
    if not os.path.exists(os.path.join(args.repo_path, '.git')):
        print(f"Error: {args.repo_path} is not a git repository", file=sys.stderr)
        sys.exit(1)
    
    # Create generator
    generator = ChangelogGenerator(args.repo_path)
    
    # Get tag to use
    tag = None
    if not args.all:
        if args.since_tag:
            tag = args.since_tag
        else:
            tag = generator.get_last_tag()
    
    # Generate changelog
    print(f"Generating changelog for {args.repo_path}...")
    print(f"Since tag: {tag or 'beginning'}")
    
    data = generator.generate_changelog(tag, args.all)
    
    # Format output
    if args.format == 'markdown':
        output = generator.format_markdown(data)
    elif args.format == 'json':
        output = generator.format_json(data)
    else:  # text
        output = generator.format_text(data)
    
    # Write to file or stdout
    if args.output == '-':
        print(output)
    else:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Changelog written to {args.output}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total commits: {data['commit_count']}")
    for category in ['added', 'fixed', 'changed', 'removed']:
        count = len(data['commits'][category])
        if count > 0:
            print(f"  {category.capitalize()}: {count}")

if __name__ == '__main__':
    main()