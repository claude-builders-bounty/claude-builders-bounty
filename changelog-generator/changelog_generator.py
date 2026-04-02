#!/usr/bin/env python3
"""
Changelog Generator - Creates structured CHANGELOG.md from git history.

This script analyzes git commit history since the last tag and generates
a structured CHANGELOG.md file with commits categorized into:
- Added
- Fixed  
- Changed
- Removed

Usage:
    python changelog_generator.py [--output FILE] [--since TAG] [--all] [--format FORMAT]
"""

import subprocess
import re
import argparse
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class ChangelogGenerator:
    """Main class for generating changelogs from git history."""
    
    # Categorization patterns
    CATEGORY_PATTERNS = {
        'Added': [
            r'\badd(s|ed|ing)?\b',
            r'\bcreate(s|d)?\b', 
            r'\bnew\b',
            r'\bimplement(s|ed)?\b',
            r'\bfeat(ure)?\b',
            r'\bfeature\b'
        ],
        'Fixed': [
            r'\bfix(es|ed)?\b',
            r'\bbug\b',
            r'\bissue\b',
            r'\berror\b',
            r'\bresolve(s|d)?\b',
            r'\bpatch\b',
            r'\bhotfix\b'
        ],
        'Changed': [
            r'\bchange(s|d)?\b',
            r'\bupdate(s|d)?\b',
            r'\bmodif(y|ied)\b',
            r'\brefactor\b',
            r'\bimprove(s|d)?\b',
            r'\benhance(s|d)?\b',
            r'\boptimize(s|d)?\b'
        ],
        'Removed': [
            r'\bremove(s|d)?\b',
            r'\bdelete(s|d)?\b',
            r'\bdeprecate(s|d)?\b',
            r'\bdrop(s|ped)?\b',
            r'\bremove\b'
        ]
    }
    
    def __init__(self, repo_path: str = '.'):
        """Initialize generator with repository path."""
        self.repo_path = repo_path
        self.commits = []
        
    def run_git_command(self, args: List[str]) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {' '.join(['git'] + args)}\nError: {e.stderr}")
    
    def get_latest_tag(self) -> Optional[str]:
        """Get the latest git tag in the repository."""
        try:
            tags = self.run_git_command(['tag', '--sort=-creatordate'])
            if tags:
                return tags.split('\n')[0]
        except RuntimeError:
            pass
        return None
    
    def get_commits_since_tag(self, tag: Optional[str] = None) -> List[Dict]:
        """Get commits since a specific tag (or all commits if no tag)."""
        if tag:
            log_format = '--format=%H|%an|%ad|%s'
            date_format = '--date=short'
            cmd = ['log', f'{tag}..HEAD', log_format, date_format]
        else:
            log_format = '--format=%H|%an|%ad|%s'
            date_format = '--date=short'
            cmd = ['log', log_format, date_format]
        
        output = self.run_git_command(cmd)
        commits = []
        
        for line in output.split('\n'):
            if not line:
                continue
                
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commit_hash, author, date, message = parts[0], parts[1], parts[2], parts[3]
                commits.append({
                    'hash': commit_hash[:8],
                    'author': author,
                    'date': date,
                    'message': message,
                    'category': self.categorize_commit(message)
                })
        
        return commits
    
    def categorize_commit(self, message: str) -> str:
        """Categorize commit message into Added/Fixed/Changed/Removed."""
        message_lower = message.lower()
        
        # Check each category
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return category
        
        # Default category
        return 'Changed'
    
    def generate_markdown(self, commits: List[Dict], version: str = "Unreleased") -> str:
        """Generate markdown changelog from categorized commits."""
        # Group commits by category
        categorized = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}
        
        for commit in commits:
            category = commit['category']
            if category in categorized:
                categorized[category].append(commit)
        
        # Build markdown
        lines = []
        lines.append(f"# Changelog\n")
        lines.append(f"\n## {version}\n")
        lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n")
        
        for category in ['Added', 'Fixed', 'Changed', 'Removed']:
            category_commits = categorized[category]
            if category_commits:
                lines.append(f"\n### {category}\n")
                for commit in category_commits:
                    lines.append(f"- {commit['message']} ({commit['hash']}, {commit['date']})")
        
        # Add summary
        total_commits = len(commits)
        lines.append(f"\n### Summary\n")
        lines.append(f"- Total commits: {total_commits}")
        for category in categorized:
            count = len(categorized[category])
            if count > 0:
                lines.append(f"- {category}: {count}")
        
        return '\n'.join(lines)
    
    def generate(self, output_file: str = 'CHANGELOG.md', 
                 since_tag: Optional[str] = None,
                 all_commits: bool = False) -> None:
        """Main generation method."""
        print(f"Generating changelog for repository: {self.repo_path}")
        
        # Determine tag to use
        tag = since_tag
        if not tag and not all_commits:
            tag = self.get_latest_tag()
        
        version = tag if tag else "Unreleased"
        if tag:
            print(f"Using tag: {tag}")
        else:
            print("No tag specified, including all commits")
        
        # Get commits
        commits = self.get_commits_since_tag(tag)
        print(f"Found {len(commits)} commits")
        
        # Generate markdown
        markdown = self.generate_markdown(commits, version)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Changelog written to: {output_file}")
        
        # Print summary
        categorized = {'Added': 0, 'Fixed': 0, 'Changed': 0, 'Removed': 0}
        for commit in commits:
            categorized[commit['category']] += 1
        
        print("\nCategorization summary:")
        for category, count in categorized.items():
            if count > 0:
                print(f"  {category}: {count}")

def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate structured CHANGELOG.md from git history'
    )
    parser.add_argument('--output', '-o', default='CHANGELOG.md',
                       help='Output file (default: CHANGELOG.md)')
    parser.add_argument('--since', '-s', 
                       help='Start from specific tag')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Include all commits (ignore tags)')
    parser.add_argument('--repo', '-r', default='.',
                       help='Repository path (default: current directory)')
    parser.add_argument('--format', '-f', default='markdown',
                       choices=['markdown', 'json'],
                       help='Output format (default: markdown)')
    
    args = parser.parse_args()
    
    try:
        generator = ChangelogGenerator(args.repo)
        generator.generate(
            output_file=args.output,
            since_tag=args.since,
            all_commits=args.all
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()