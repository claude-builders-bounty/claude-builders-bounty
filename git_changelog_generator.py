#!/usr/bin/env python3
"""
Automatic Git Changelog Generator
Bounty: Issue #1021 - implement automatic git changelog generator skill
"""

import subprocess
import re
from collections import defaultdict
from datetime import datetime

class GitChangelogGenerator:
    """Generate structured CHANGELOG from git history."""
    
    CATEGORIES = {
        'feat': '✨ Features',
        'fix': '🐛 Bug Fixes',
        'docs': '📝 Documentation',
        'style': '💎 Styles',
        'refactor': '♻️ Refactors',
        'test': '✅ Tests',
        'chore': '📦 Chores',
        'perf': '⚡ Performance',
    }
    
    def __init__(self, repo_path='.'):
        self.repo_path = repo_path
    
    def get_commits(self, max_commits=100):
        """Get git commit history."""
        try:
            result = subprocess.run(
                ['git', 'log', f'-n{max_commits}', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commits = []
            for line in result.stdout.strip().split('
'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0][:8],
                            'author': parts[1],
                            'email': parts[2],
                            'date': parts[3],
                            'subject': '|'.join(parts[4:])
                        })
            return commits
        except subprocess.CalledProcessError as e:
            print(f'Error getting commits: {e}')
            return []
    
    def categorize_commit(self, subject):
        """Categorize commit based on conventional commit prefix."""
        for prefix in self.CATEGORIES:
            if subject.lower().startswith(prefix):
                return prefix
        return 'chore'  # Default category
    
    def generate_changelog(self, commits):
        """Generate structured changelog content."""
        categories = defaultdict(list)
        
        for commit in commits:
            category = self.categorize_commit(commit['subject'])
            categories[category].append(commit)
        
        # Generate markdown
        lines = [
            '# Changelog
',
            f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
',
            f'Total commits analyzed: {len(commits)}
',
            '---
'
        ]
        
        for cat_prefix, cat_name in self.CATEGORIES.items():
            if cat_prefix in categories:
                lines.append(f'
## {cat_name}
')
                for commit in categories[cat_prefix]:
                    lines.append(f'- `{commit["hash"]}` {commit["subject"]}
')
                    lines.append(f'  - Author: {commit["author"]} <{commit["email"]}>
')
                    lines.append(f'  - Date: {commit["date"]}
')
        
        return ''.join(lines)
    
    def save_changelog(self, output_path='CHANGELOG.md'):
        """Generate and save changelog to file."""
        commits = self.get_commits()
        if not commits:
            print('No commits found.')
            return False
        
        changelog = self.generate_changelog(commits)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(changelog)
        
        print(f'✅ Changelog saved to {output_path}')
        print(f'   Total commits: {len(commits)}')
        return True

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Git Changelog')
    parser.add_argument('--repo', default='.', help='Repository path')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output file path')
    parser.add_argument('--max', type=int, default=100, help='Max commits to analyze')
    
    args = parser.parse_args()
    
    generator = GitChangelogGenerator(args.repo)
    generator.save_changelog(args.output)

if __name__ == '__main__':
    main()
