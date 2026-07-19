#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from a project's git history.

Parses conventional commit messages (feat:, fix:, docs:, chore:, refactor:,
perf:, test:, style:, ci:, build:, revert:) and groups them by type and
version tag intervals.

Usage:
    python3 generate_changelog.py [--repo PATH] [--output FILE] [--since TAG] [--max-commits N]

Examples:
    python3 generate_changelog.py
    python3 generate_changelog.py --repo /path/to/repo --output CHANGELOG.md
    python3 generate_changelog.py --since v1.0.0 --max-commits 500
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ──────────────────────────────────────────────────────────────────── #
# Constants
# ──────────────────────────────────────────────────────────────────── #

COMMIT_TYPES: dict[str, str] = {
    "feat": "✨ Features",
    "fix": "🐛 Bug Fixes",
    "docs": "📚 Documentation",
    "style": "💎 Styles",
    "refactor": "♻️ Code Refactoring",
    "perf": "⚡️ Performance Improvements",
    "test": "✅ Tests",
    "build": "📦 Build System",
    "ci": "🔧 Continuous Integration",
    "chore": "🎟️ Chores",
    "revert": "⏪ Reverts",
    "security": "🔒 Security",
}

# Pattern: type(scope)?: description  OR  type: description
COMMIT_PATTERN = re.compile(
    r"^(?P<type>\w+)"
    r"(?:\((?P<scope>[\w\-/.]+)\))?"
    r"(?P<breaking>!)?:\s*"
    r"(?P<description>.+)$"
)

# Pattern for merge commits: "Merge pull request #123" or "Merge branch 'x'"
MERGE_PATTERN = re.compile(r"^Merge\s+(pull request\s+#?\d+|branch\s+['\"]?\w+)", re.IGNORECASE)

# Git log format: hash|date|subject
GIT_LOG_FORMAT = "%H|%aI|%s"

# Maximum line length for descriptions in output
MAX_LINE_LENGTH = 80

# Default max commits to fetch
DEFAULT_MAX_COMMITS = 1000


# ──────────────────────────────────────────────────────────────────── #
# Data classes
# ──────────────────────────────────────────────────────────────────── #

@dataclass
class Commit:
    """A single git commit parsed from git log."""
    hash: str
    date: str  # ISO 8601
    raw_subject: str
    type: str = ""
    scope: str = ""
    description: str = ""
    is_breaking: bool = False
    is_merge: bool = False


@dataclass
class VersionSection:
    """A version section in the changelog."""
    version: str
    date: str
    commits: list[Commit] = field(default_factory=list)

    @property
    def grouped_commits(self) -> dict[str, list[Commit]]:
        """Group commits by conventional commit type."""
        groups: dict[str, list[Commit]] = defaultdict(list)
        for commit in self.commits:
            if commit.is_merge:
                continue
            if commit.type:
                groups[commit.type].append(commit)
            else:
                groups["other"].append(commit)
        return dict(groups)


# ──────────────────────────────────────────────────────────────────── #
# Git log parsing
# ──────────────────────────────────────────────────────────────────── #

def run_git_log(repo_path: str = ".", max_commits: int = DEFAULT_MAX_COMMITS, since_tag: str | None = None) -> str:
    """Run git log and return raw output."""
    cmd = ["git", "-C", repo_path, "log", f"--format={GIT_LOG_FORMAT}", f"-n{max_commits}"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        result.check_returncode()
        return result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"Error running git log: {exc}", file=sys.stderr)
        return ""


def parse_commit_line(line: str) -> Commit | None:
    """Parse a single line from git log output (hash|date|subject)."""
    parts = line.split("|", 2)
    if len(parts) < 3:
        return None
    hash_val, date, subject = parts[0].strip(), parts[1].strip(), parts[2].strip()
    if not hash_val or not subject:
        return None

    commit = Commit(hash=hash_val, date=date, raw_subject=subject)

    # Check for merge commits
    if MERGE_PATTERN.match(subject):
        commit.is_merge = True
        commit.type = "merge"
        commit.description = subject
        return commit

    # Parse conventional commit format
    match = COMMIT_PATTERN.match(subject)
    if match:
        commit.type = match.group("type").lower()
        commit.scope = match.group("scope") or ""
        commit.description = match.group("description").strip()
        commit.is_breaking = bool(match.group("breaking"))
    else:
        # Non-conventional commit — store as "other"
        commit.type = "other"
        commit.description = subject

    return commit


def get_tags(repo_path: str = ".") -> list[tuple[str, str]]:
    """Get all git tags with their dates. Returns list of (tag_name, date)."""
    cmd = ["git", "-C", repo_path, "tag", "--format=%(refname:short)|%(creatordate:iso-strict)"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        result.check_returncode()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []

    tags = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 1)
        if len(parts) == 2:
            tags.append((parts[0].strip(), parts[1].strip()[:10]))  # date only YYYY-MM-DD
    return tags


def group_commits_by_version(commits: list[Commit], tags: list[tuple[str, str]]) -> list[VersionSection]:
    """Group commits into version sections based on tag boundaries.

    If no tags exist, all commits go into a single "Unreleased" section.
    """
    if not commits:
        return []

    if not tags:
        # No tags — single "Unreleased" section
        latest_date = commits[0].date[:10] if commits else ""
        return [VersionSection(version="Unreleased", date=latest_date, commits=commits)]

    # Build version sections from tags
    sections: list[VersionSection] = []
    tag_commits: dict[str, list[Commit]] = defaultdict(list)

    # Assign each commit to the most recent tag that precedes it
    # Tags are ordered newest-first from git
    sorted_tags = list(reversed(tags))  # oldest first

    for commit in commits:
        assigned = False
        for i in range(len(sorted_tags) - 1, -1, -1):
            tag_name, tag_date = sorted_tags[i]
            if commit.date[:10] <= tag_date:
                tag_commits[tag_name].append(commit)
                assigned = True
                break
        if not assigned:
            tag_commits["Unreleased"].append(commit)

    # Build sections (newest first)
    unreleased = tag_commits.pop("Unreleased", [])
    if unreleased:
        latest_date = unreleased[0].date[:10] if unreleased else ""
        sections.append(VersionSection(version="Unreleased", date=latest_date, commits=unreleased))

    for tag_name, tag_date in reversed(tags):
        commits_for_tag = tag_commits.get(tag_name, [])
        if commits_for_tag:
            sections.append(VersionSection(version=tag_name, date=tag_date, commits=commits_for_tag))

    return sections


# ──────────────────────────────────────────────────────────────────── #
# Markdown generation
# ──────────────────────────────────────────────────────────────────── #

def format_commit_entry(commit: Commit) -> str:
    """Format a single commit as a markdown list item."""
    desc = commit.description[:MAX_LINE_LENGTH]
    if commit.scope:
        return f"- **{commit.scope}:** {desc} (`{commit.hash[:7]}`)"
    return f"- {desc} (`{commit.hash[:7]}`)"


def generate_markdown(sections: list[VersionSection]) -> str:
    """Generate the full CHANGELOG.md content from version sections."""
    lines: list[str] = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        "---",
        "",
    ]

    if not sections:
        lines.extend(["*No commits found.*", ""])
        return "\n".join(lines)

    for section in sections:
        # Version header
        if section.version == "Unreleased":
            lines.append("## [Unreleased]")
        else:
            lines.append(f"## [{section.version}] - {section.date}")
        lines.append("")

        grouped = section.grouped_commits
        if not grouped:
            lines.append("*No notable changes.*")
            lines.append("")
            continue

        # Output each type in the order defined in COMMIT_TYPES
        for type_key, type_label in COMMIT_TYPES.items():
            if type_key in grouped and grouped[type_key]:
                lines.append(f"### {type_label}")
                lines.append("")
                for commit in grouped[type_key]:
                    lines.append(format_commit_entry(commit))
                lines.append("")

        # Handle "other" (non-conventional commits)
        if "other" in grouped and grouped["other"]:
            lines.append("### 📝 Other Changes")
            lines.append("")
            for commit in grouped["other"][:20]:  # cap at 20 to avoid noise
                lines.append(format_commit_entry(commit))
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────── #
# Main
# ──────────────────────────────────────────────────────────────────── #

def generate_changelog(
    repo_path: str = ".",
    output_file: str | None = None,
    since_tag: str | None = None,
    max_commits: int = DEFAULT_MAX_COMMITS,
) -> str:
    """Generate a CHANGELOG.md from git history.

    Args:
        repo_path: Path to the git repository.
        output_file: If provided, write the changelog to this file. Also returns the content.
        since_tag: Only include commits after this tag.
        max_commits: Maximum number of commits to fetch.

    Returns:
        The generated changelog markdown content.
    """
    # 1. Fetch git log
    raw_log = run_git_log(repo_path, max_commits, since_tag)
    if not raw_log.strip():
        return "# Changelog\n\n*No commits found.*\n"

    # 2. Parse commits
    commits: list[Commit] = []
    for line in raw_log.strip().split("\n"):
        commit = parse_commit_line(line)
        if commit:
            commits.append(commit)

    if not commits:
        return "# Changelog\n\n*No commits found.*\n"

    # 3. Get tags for version grouping
    tags = get_tags(repo_path)

    # 4. Group commits by version
    sections = group_commits_by_version(commits, tags)

    # 5. Generate markdown
    markdown = generate_markdown(sections)

    # 6. Write to file if specified
    if output_file:
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = Path(repo_path) / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

    return markdown


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history."
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository (default: current directory)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--since", default=None, help="Only include commits after this tag (e.g., v1.0.0)")
    parser.add_argument("--max-commits", type=int, default=DEFAULT_MAX_COMMITS, help=f"Max commits to fetch (default: {DEFAULT_MAX_COMMITS})")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing a file")

    args = parser.parse_args()

    markdown = generate_changelog(
        repo_path=args.repo,
        output_file=None if args.stdout else args.output,
        since_tag=args.since,
        max_commits=args.max_commits,
    )

    if args.stdout:
        print(markdown)
    else:
        print(f"✅ CHANGELOG.md generated ({len(markdown)} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
