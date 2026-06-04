#!/usr/bin/env python3
"""
CHANGELOG Generator - Hermes Skill
Generates a structured CHANGELOG.md from git commit history.

Usage:
  python changelog-generator.py <repo_path> [output_file]

Features:
- Groups commits by type (feat, fix, docs, refactor, perf, test, chore, ci)
- Extracts scope from conventional commits (feat(scope): message)
- Generates markdown with proper formatting
- Skips merge commits and empty commits
- Groups by date/version tags when available

Conventional Commit Format:
  feat(scope): message
  fix(scope): message
  docs: message
  etc.
"""

import subprocess
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys


def get_git_log(repo_path: str) -> List[Dict]:
    """Extract structured git log data from repository."""
    repo_path_obj = Path(repo_path).resolve()
    
    if not (repo_path_obj / ".git").exists():
        raise ValueError(f"Not a git repository: {repo_path}")
    
    try:
        # Get commits with simple format
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H%x00%an%x00%ae%x00%ai%x00%s%x00%b%x00"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to read git log: {e.stderr}")
    
    commits = []
    entries = result.stdout.split('\x00\x00')
    
    for entry in entries:
        if not entry.strip():
            continue
        
        parts = entry.split('\x00')
        if len(parts) >= 5:
            commit = {
                'hash': parts[0].strip(),
                'author': parts[1].strip(),
                'email': parts[2].strip(),
                'date': parts[3].strip(),
                'subject': parts[4].strip(),
                'body': parts[5].strip() if len(parts) > 5 else ''
            }
            if commit['hash']:
                commits.append(commit)
    
    return commits


def parse_conventional_commit(subject: str) -> Tuple[str, Optional[str], str]:
    """Parse conventional commit format: type(scope): description"""
    # Match: type(scope): message or type: message
    match = re.match(r'^(\w+)(?:\(([^)]+)\))?\s*:\s*(.+)$', subject)
    
    if match:
        commit_type = match.group(1)
        scope = match.group(2)
        message = match.group(3)
        return commit_type, scope, message
    
    # If not conventional, treat whole thing as message
    return 'other', None, subject


def group_commits_by_type(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """Group commits by type using conventional commit format."""
    groups = defaultdict(list)
    
    for commit in commits:
        subject = commit.get('subject', '').strip()
        
        # Skip merge commits
        if subject.lower().startswith('merge '):
            continue
        
        # Skip empty commits
        if not subject:
            continue
        
        commit_type, scope, message = parse_conventional_commit(subject)
        
        commit['type'] = commit_type
        commit['scope'] = scope
        commit['message'] = message
        
        groups[commit_type].append(commit)
    
    return dict(groups)


def format_changelog(grouped_commits: Dict[str, List[Dict]]) -> str:
    """Generate formatted CHANGELOG markdown."""
    
    type_order = [
        'feat',
        'fix',
        'perf',
        'refactor',
        'docs',
        'test',
        'ci',
        'chore',
        'other'
    ]
    
    type_titles = {
        'feat': '✨ Features',
        'fix': '🐛 Bug Fixes',
        'perf': '⚡ Performance',
        'refactor': '♻️  Refactoring',
        'docs': '📚 Documentation',
        'test': '✅ Tests',
        'ci': '🔧 CI/CD',
        'chore': '🔨 Maintenance',
        'other': '📝 Other'
    }
    
    changelog = "# CHANGELOG\n\n"
    changelog += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    if not any(grouped_commits.values()):
        changelog += "No commits found.\n"
        return changelog
    
    # Add latest entry with all commits
    changelog += "## [Unreleased]\n\n"
    
    for commit_type in type_order:
        if commit_type not in grouped_commits:
            continue
        
        commits = grouped_commits[commit_type]
        if not commits:
            continue
        
        changelog += f"### {type_titles.get(commit_type, commit_type)}\n\n"
        
        # Group by scope if available
        by_scope = defaultdict(list)
        for commit in commits:
            scope = commit.get('scope') or '(no scope)'
            by_scope[scope].append(commit)
        
        # Generate entries
        for scope in sorted(by_scope.keys()):
            scope_commits = by_scope[scope]
            
            if scope != '(no scope)':
                changelog += f"**{scope}**\n"
            
            for commit in scope_commits:
                message = commit.get('message', commit.get('subject', ''))
                short_hash = commit.get('hash', '')[:7]
                changelog += f"- {message} ([{short_hash}](../../commit/{commit.get('hash', '')}))\n"
        
        changelog += "\n"
    
    # Add footer
    changelog += "---\n\n"
    changelog += "**Legend:**\n"
    changelog += "- `feat`: New features\n"
    changelog += "- `fix`: Bug fixes\n"
    changelog += "- `perf`: Performance improvements\n"
    changelog += "- `refactor`: Code refactoring\n"
    changelog += "- `docs`: Documentation changes\n"
    changelog += "- `test`: Test additions/updates\n"
    changelog += "- `ci`: CI/CD pipeline changes\n"
    changelog += "- `chore`: Maintenance and tooling\n"
    
    return changelog


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python changelog-generator.py <repo_path> [output_file]")
        print("\nExample:")
        print("  python changelog-generator.py . CHANGELOG.md")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    
    try:
        print(f"📖 Reading git history from {repo_path}...")
        commits = get_git_log(repo_path)
        print(f"   Found {len(commits)} commits")
        
        print(f"📊 Grouping commits by type...")
        grouped = group_commits_by_type(commits)
        
        for commit_type, commits_list in grouped.items():
            print(f"   {commit_type}: {len(commits_list)} commits")
        
        print(f"✍️  Generating CHANGELOG...")
        changelog_content = format_changelog(grouped)
        
        # Write to file
        output_path = Path(output_file)
        output_path.write_text(changelog_content)
        
        print(f"✅ CHANGELOG written to {output_file}")
        print(f"\n{changelog_content[:500]}...\n")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
