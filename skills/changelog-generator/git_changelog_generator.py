#!/usr/bin/env python3
"""
Git CHANGELOG Generator
Generates a structured CHANGELOG from git history.
"""

import subprocess
import re
import sys
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path


class ChangelogGenerator:
    """Generate structured CHANGELOG from git history."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.commit_types = {
            "feat": "New Features",
            "feature": "New Features",
            "fix": "Bug Fixes",
            "bugfix": "Bug Fixes",
            "docs": "Documentation",
            "documentation": "Documentation",
            "style": "Style Changes",
            "refactor": "Refactoring",
            "perf": "Performance Improvements",
            "test": "Tests",
            "tests": "Tests",
            "chore": "Chores",
            "build": "Build System",
            "ci": "Continuous Integration",
            "security": "Security Fixes",
        }

    def get_git_log(self, max_commits: int = 100) -> List[Dict]:
        """Get git log history."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{max_commits}",
                    "--pretty=format:%H|%ad|%an|%s",
                    "--date=format:%Y-%m-%d",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "date": parts[1],
                            "author": parts[2],
                            "message": parts[3],
                        })

            return commits

        except subprocess.CalledProcessError as e:
            print(f"Error running git log: {e}")
            return []

    def parse_commit_message(self, message: str) -> Tuple[str, str, str]:
        """Parse conventional commit message.
        
        Format: type(scope): description
        Example: feat(auth): add login functionality
        """
        pattern = r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$'
        match = re.match(pattern, message)

        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2) or ""
            description = match.group(3)
            return commit_type, scope, description

        words = message.split()
        if words:
            first_word = words[0].lower().rstrip(":")
            if first_word in self.commit_types:
                return first_word, "", " ".join(words[1:]) if len(words) > 1 else message

        return "other", "", message

    def group_commits(self, commits: List[Dict]) -> Dict[str, List[Dict]]:
        """Group commits by type and date."""
        grouped = {}

        for commit in commits:
            commit_type, scope, description = self.parse_commit_message(commit["message"])
            commit_type = self.commit_types.get(commit_type, "Other Changes")

            date = commit["date"]
            if date not in grouped:
                grouped[date] = {}

            if commit_type not in grouped[date]:
                grouped[date][commit_type] = []

            grouped[date][commit_type].append({
                "hash": commit["hash"][:7],
                "author": commit["author"],
                "scope": scope,
                "description": description,
                "original": commit["message"],
            })

        return grouped

    def generate_markdown(self, grouped: Dict, title: str = "CHANGELOG") -> str:
        """Generate markdown formatted changelog."""
        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append("> All notable changes to this project will be documented in this file.")
        lines.append("")
        lines.append("---")
        lines.append("")

        sorted_dates = sorted(grouped.keys(), reverse=True)

        for date in sorted_dates:
            lines.append(f"## [{date}]")
            lines.append("")

            date_commits = grouped[date]
            section_order = [
                "New Features", "Bug Fixes", "Security Fixes",
                "Performance Improvements", "Documentation", "Refactoring",
                "Style Changes", "Tests", "Build System", "Continuous Integration",
                "Chores", "Other Changes",
            ]

            for section in section_order:
                if section in date_commits:
                    lines.append(f"### {section}")
                    lines.append("")

                    for commit in date_commits[section]:
                        scope = f"**{commit['scope']}:** " if commit["scope"] else ""
                        lines.append(f"- {scope}{commit['description']} ({commit['hash']})")

                    lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*This CHANGELOG was auto-generated by git-changelog-generator*")
        lines.append("")

        return "\n".join(lines)

    def generate(self, output_file: str = "CHANGELOG.md", max_commits: int = 100) -> bool:
        """Generate changelog and save to file."""
        print(f"Generating changelog for {self.repo_path}...")

        commits = self.get_git_log(max_commits)
        if not commits:
            print("No commits found.")
            return False

        print(f"Found {len(commits)} commits")

        grouped = self.group_commits(commits)
        markdown = self.generate_markdown(grouped)

        output_path = self.repo_path / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"Changelog saved to {output_path}")
        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate CHANGELOG from git history")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file name")
    parser.add_argument("-n", "--max-commits", type=int, default=100, help="Max commits to process")
    parser.add_argument("-r", "--repo", default=".", help="Repository path")

    args = parser.parse_args()

    generator = ChangelogGenerator(args.repo)
    success = generator.generate(args.output, args.max_commits)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
