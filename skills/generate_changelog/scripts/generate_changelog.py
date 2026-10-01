#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git commit history.
Supports Conventional Commits specification, tag filtering, semver grouping,
and custom commit range parsing.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?: "
    r"(?P<subject>.+)$"
)

SECTION_MAPPING = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance Improvements",
    "refactor": "Code Refactoring",
    "docs": "Documentation",
    "style": "Styles",
    "test": "Tests",
    "build": "Build System",
    "ci": "Continuous Integration",
    "chore": "Maintenance",
    "revert": "Reverts",
}


class GitChangelogGenerator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> str:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: git {' '.join(args)}\nError: {e.stderr}")

    def get_tags(self) -> List[Tuple[str, str]]:
        """Return list of (tag_name, tag_commit_date) sorted by commit date descending."""
        raw = self._run_git(
            ["tag", "-l", "--sort=-creatordate", "--format=%(refname:short)|%(creatordate:iso-strict)"]
        )
        if not raw:
            return []
        tags = []
        for line in raw.splitlines():
            if "|" in line:
                name, date_str = line.split("|", 1)
                tags.append((name.strip(), date_str.strip()))
        return tags

    def parse_commits(self, commit_range: Optional[str] = None) -> List[Dict[str, str]]:
        """Parse commits in given range into structured commit dictionaries."""
        cmd = ["log", "--format=%H|%an|%ad|%s", "--date=short"]
        if commit_range:
            cmd.append(commit_range)

        raw = self._run_git(cmd)
        if not raw:
            return []

        commits = []
        for line in raw.splitlines():
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            commit_hash, author, date_str, subject = parts
            parsed = self.parse_commit_message(subject)
            parsed.update(
                {
                    "hash": commit_hash[:7],
                    "full_hash": commit_hash,
                    "author": author,
                    "date": date_str,
                    "raw_subject": subject,
                }
            )
            commits.append(parsed)
        return commits

    @staticmethod
    def parse_commit_message(message: str) -> Dict[str, str]:
        """Parse commit message according to Conventional Commits standard."""
        match = CONVENTIONAL_COMMIT_REGEX.match(message)
        if match:
            gd = match.groupdict()
            return {
                "type": gd["type"],
                "scope": gd["scope"] or "",
                "is_breaking": bool(gd["breaking"]),
                "subject": gd["subject"],
                "is_conventional": True,
            }
        return {
            "type": "chore",
            "scope": "",
            "is_breaking": False,
            "subject": message,
            "is_conventional": False,
        }

    def generate_markdown(
        self,
        commits: List[Dict[str, str]],
        version: str = "Unreleased",
        date_str: Optional[str] = None,
    ) -> str:
        """Generate Keep a Changelog formatted Markdown string."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        grouped: Dict[str, List[Dict[str, str]]] = {}
        breaking_changes: List[Dict[str, str]] = []

        for commit in commits:
            if commit["is_breaking"]:
                breaking_changes.append(commit)
            commit_type = commit["type"]
            section = SECTION_MAPPING.get(commit_type, "Other Changes")
            grouped.setdefault(section, []).append(commit)

        lines = [f"## [{version}] - {date_str}"]

        if breaking_changes:
            lines.append("\n### ⚠️ BREAKING CHANGES")
            for bc in breaking_changes:
                scope_prefix = f"**{bc['scope']}**: " if bc['scope'] else ""
                lines.append(f"- {scope_prefix}{bc['subject']} ({bc['hash']})")

        # Preferred section ordering
        section_order = [
            "Features",
            "Bug Fixes",
            "Performance Improvements",
            "Code Refactoring",
            "Documentation",
            "Styles",
            "Tests",
            "Build System",
            "Continuous Integration",
            "Maintenance",
            "Reverts",
            "Other Changes",
        ]

        for section in section_order:
            if section in grouped:
                lines.append(f"\n### {section}")
                for item in grouped[section]:
                    scope_prefix = f"**{item['scope']}**: " if item['scope'] else ""
                    lines.append(f"- {scope_prefix}{item['subject']} ({item['hash']})")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--repo", default=".", help="Path to git repository")
    parser.add_argument("--range", help="Git commit range (e.g. v1.0.0..HEAD)")
    parser.add_argument("--version", default="Unreleased", help="Version name for header")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    generator = GitChangelogGenerator(repo_path=args.repo)
    commits = generator.parse_commits(commit_range=args.range)
    markdown = generator.generate_markdown(commits=commits, version=args.version)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown + "\n")
        print(f"CHANGELOG written to {args.output}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
