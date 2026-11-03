#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.
Follows the 'Keep a Changelog' standard (https://keepachangelog.com).
Zero external dependencies.
"""

import sys
import subprocess
import re
from datetime import datetime
from pathlib import Path


def run_git_command(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command and return its stdout, or empty string on error."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_latest_tag(repo_dir: Path) -> str | None:
    """Find the latest git tag reachable from HEAD, or None if no tags exist."""
    tag = run_git_command(["describe", "--tags", "--abbrev=0"], cwd=repo_dir)
    return tag if tag else None


def get_commits_since(tag: str | None, repo_dir: Path) -> list[str]:
    """Get commit subjects and hashes since the given tag (or all commits if no tag)."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    log_output = run_git_command(["log", rev_range, "--pretty=format:%h|%s"], cwd=repo_dir)
    if not log_output:
        return []
    return log_output.splitlines()


def categorize_commits(commit_lines: list[str]) -> dict[str, list[str]]:
    """
    Categorize commits into:
      - Added
      - Fixed
      - Changed
      - Removed
      - Documentation
      - Maintenance
    """
    categories: dict[str, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Security": [],
        "Documentation": [],
        "Other": [],
    }

    for line in commit_lines:
        if not line or "|" not in line:
            continue
        commit_hash, subject = line.split("|", 1)
        subject_clean = subject.strip()

        # Conventional Commits prefixes & keywords
        if re.search(r"^(feat|add|feature)\b", subject_clean, re.IGNORECASE):
            categories["Added"].append(f"- {subject_clean} (`{commit_hash}`)")
        elif re.search(r"^(fix|bug|patch|resolve)\b", subject_clean, re.IGNORECASE):
            categories["Fixed"].append(f"- {subject_clean} (`{commit_hash}`)")
        elif re.search(r"^(refactor|perf|change|update|mod)\b", subject_clean, re.IGNORECASE):
            categories["Changed"].append(f"- {subject_clean} (`{commit_hash}`)")
        elif re.search(r"^(remove|deprecate|delete)\b", subject_clean, re.IGNORECASE):
            categories["Removed"].append(f"- {subject_clean} (`{commit_hash}`)")
        elif re.search(r"^(sec|security)\b", subject_clean, re.IGNORECASE):
            categories["Security"].append(f"- {subject_clean} (`{commit_hash}`)")
        elif re.search(r"^(docs|doc)\b", subject_clean, re.IGNORECASE):
            categories["Documentation"].append(f"- {subject_clean} (`{commit_hash}`)")
        else:
            categories["Other"].append(f"- {subject_clean} (`{commit_hash}`)")

    return categories


def render_changelog_markdown(categories: dict[str, list[str]], version_label: str = "Unreleased") -> str:
    """Format categories into Keep a Changelog markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"## [{version_label}] - {today}",
        "",
    ]

    for cat_name in ["Added", "Fixed", "Changed", "Removed", "Security", "Documentation", "Other"]:
        items = categories.get(cat_name, [])
        if items:
            lines.append(f"### {cat_name}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip()


def update_or_create_changelog(repo_dir: Path, output_file: Path | None = None) -> Path:
    """Generate and write or prepend to CHANGELOG.md in the target directory."""
    target_path = output_file or (repo_dir / "CHANGELOG.md")
    latest_tag = get_latest_tag(repo_dir)
    commits = get_commits_since(latest_tag, repo_dir)

    categories = categorize_commits(commits)
    new_release_section = render_changelog_markdown(categories, version_label=latest_tag or "Unreleased")

    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
    )

    if target_path.exists():
        existing_content = target_path.read_text(encoding="utf-8")
        if "# Changelog" in existing_content:
            # Prepend new section after the header
            parts = existing_content.split("# Changelog", 1)
            updated = f"# Changelog\n\n{new_release_section}\n\n{parts[1].strip()}"
        else:
            updated = f"{header}{new_release_section}\n\n{existing_content}"
    else:
        updated = f"{header}{new_release_section}\n"

    target_path.write_text(updated, encoding="utf-8")
    return target_path


def main():
    repo_dir = Path.cwd()
    if len(sys.argv) > 1:
        repo_dir = Path(sys.argv[1]).resolve()

    changelog_file = update_or_create_changelog(repo_dir)
    print(f"✅ CHANGELOG generated successfully at: {changelog_file}")


if __name__ == "__main__":
    main()
