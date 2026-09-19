#!/usr/bin/env python3
"""
Structured Changelog Generator from Git History.
Complies with Keep a Changelog (https://keepachangelog.com/en/1.0.0/)
and Conventional Commits specifications.
"""

import sys
import os
import re
import subprocess
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

CATEGORY_MAPPING = {
    # Conventional commit prefixes -> Keep a Changelog categories
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "update": "Changed",
    
    "remove": "Removed",
    "removed": "Removed",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
    "revert": "Removed",
}

class Commit:
    def __init__(self, commit_hash: str, author: str, date: str, subject: str, body: str = ""):
        self.hash = commit_hash
        self.author = author
        self.date = date
        self.subject = subject.strip()
        self.body = body.strip()

    @property
    def short_hash(self) -> str:
        return self.hash[:7] if self.hash else ""

    def categorize(self) -> str:
        # Match conventional commits: type(scope)!: description
        conv_match = re.match(r"^([a-zA-Z]+)(?:\([^\)]+\))?!?:\s*(.+)$", self.subject)
        if conv_match:
            ctype = conv_match.group(1).lower()
            if ctype in CATEGORY_MAPPING:
                return CATEGORY_MAPPING[ctype]

        # Heuristic keyword search in subject
        sub_lower = self.subject.lower()
        if re.search(r"\b(add|added|adding|feature|support|supported|implement|implemented|introduce|introduced)\b", sub_lower):
            return "Added"
        if re.search(r"\b(fix|fixed|fixing|bug|bugfix|resolve|resolved|resolving|patch|patched)\b", sub_lower):
            return "Fixed"
        if re.search(r"\b(remove|removed|removing|delete|deleted|deleting|drop|dropped|deprecate|deprecated)\b", sub_lower):
            return "Removed"
        
        return "Changed"

    def clean_subject(self) -> str:
        # Strip conventional prefix if present for clean changelog display
        conv_match = re.match(r"^[a-zA-Z]+(?:\([^\)]+\))?!?:\s*(.+)$", self.subject)
        if conv_match:
            clean = conv_match.group(1).strip()
            # Capitalize first letter
            return clean[0].upper() + clean[1:] if clean else self.subject
        return self.subject[0].upper() + self.subject[1:] if self.subject else self.subject


class GitRepo:
    def __init__(self, repo_dir: str = "."):
        self.repo_dir = repo_dir

    def _run(self, args: List[str]) -> str:
        res = subprocess.run(
            ["git"] + args,
            cwd=self.repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()

    def get_latest_tag(self) -> Optional[str]:
        try:
            tag = self._run(["describe", "--tags", "--abbrev=0"])
            return tag if tag else None
        except subprocess.CalledProcessError:
            return None

    def get_commits(self, from_tag: Optional[str] = None, to_ref: str = "HEAD") -> List[Commit]:
        git_range = f"{from_tag}..{to_ref}" if from_tag else to_ref
        delimiter_record = "\x1e"
        delimiter_field = "\x1f"
        
        log_format = f"{delimiter_record}%H{delimiter_field}%an{delimiter_field}%ad{delimiter_field}%s{delimiter_field}%b"
        args = ["log", git_range, f"--pretty=format:{log_format}", "--date=short"]
        
        try:
            raw = self._run(args)
        except subprocess.CalledProcessError:
            return []

        commits = []
        records = raw.split(delimiter_record)
        for rec in records:
            if not rec.strip():
                continue
            parts = rec.strip().split(delimiter_field)
            if len(parts) >= 4:
                c_hash = parts[0].strip()
                c_author = parts[1].strip()
                c_date = parts[2].strip()
                c_subject = parts[3].strip()
                c_body = parts[4].strip() if len(parts) > 4 else ""
                
                # Ignore merge commits
                if c_subject.startswith("Merge branch") or c_subject.startswith("Merge pull request"):
                    continue
                
                commits.append(Commit(c_hash, c_author, c_date, c_subject, c_body))

        return commits


class ChangelogBuilder:
    def __init__(self, version_name: str = "Unreleased", release_date: Optional[str] = None):
        self.version_name = version_name
        self.release_date = release_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def build_markdown(self, commits: List[Commit], prev_tag: Optional[str] = None) -> str:
        categorized: Dict[str, List[Commit]] = {
            "Added": [],
            "Changed": [],
            "Deprecated": [],
            "Removed": [],
            "Fixed": [],
            "Security": []
        }

        for c in commits:
            cat = c.categorize()
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(c)

        lines: List[str] = []
        if self.version_name.lower() == "unreleased":
            lines.append(f"## [Unreleased] - {self.release_date}")
        else:
            lines.append(f"## [{self.version_name}] - {self.release_date}")

        if prev_tag:
            lines.append(f"> *Changes since `{prev_tag}` ({len(commits)} commits)*\n")
        else:
            lines.append(f"> *Initial release or all commits ({len(commits)} commits)*\n")

        order = ["Added", "Changed", "Fixed", "Deprecated", "Removed", "Security"]
        has_content = False

        for section in order:
            items = categorized.get(section, [])
            if items:
                has_content = True
                lines.append(f"### {section}")
                for item in items:
                    lines.append(f"- {item.clean_subject()} ([`{item.short_hash}`])")
                lines.append("")

        if not has_content:
            lines.append("- No documented changes in this range.\n")

        return "\n".join(lines)


def generate_changelog(
    repo_dir: str = ".",
    version: str = "Unreleased",
    output_file: Optional[str] = "CHANGELOG.md",
    dry_run: bool = False
) -> str:
    repo = GitRepo(repo_dir)
    tag = repo.get_latest_tag()
    commits = repo.get_commits(from_tag=tag)

    builder = ChangelogBuilder(version_name=version)
    new_section = builder.build_markdown(commits, prev_tag=tag)

    header = """# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

    final_content = ""
    if output_file and os.path.exists(os.path.join(repo_dir, output_file)):
        with open(os.path.join(repo_dir, output_file), "r", encoding="utf-8") as f:
            existing = f.read()

        if "# Changelog" in existing:
            # Prepend under the main header
            parts = existing.split("# Changelog", 1)
            final_content = f"# Changelog\n\n{new_section}\n" + parts[1].strip()
        else:
            final_content = f"{header}{new_section}\n\n" + existing
    else:
        final_content = f"{header}{new_section}\n"

    if not dry_run and output_file:
        out_path = os.path.join(repo_dir, output_file)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    return final_content


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--repo", default=".", help="Target git repository path")
    parser.add_argument("--version", default="Unreleased", help="Version title (e.g. v1.2.0 or Unreleased)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path (default: CHANGELOG.md)")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without modifying files")
    args = parser.parse_args()

    content = generate_changelog(
        repo_dir=args.repo,
        version=args.version,
        output_file=args.output,
        dry_run=args.dry_run
    )

    if args.dry_run:
        print(content)
    else:
        print(f"Successfully generated changelog at: {args.output}")

if __name__ == "__main__":
    main()
