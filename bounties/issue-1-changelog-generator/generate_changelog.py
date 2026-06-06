#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from Git history."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SECTION_ORDER = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
    )


def latest_tag(repo: Path) -> str | None:
    result = git(repo, "describe", "--tags", "--abbrev=0", check=False)
    tag = result.stdout.strip()
    return tag if result.returncode == 0 and tag else None


def commits_since(repo: Path, tag: str | None) -> list[Commit]:
    range_arg = f"{tag}..HEAD" if tag else "HEAD"
    result = git(repo, "log", "--pretty=format:%H%x1f%s%x1f%b%x1e", range_arg)
    raw = result.stdout.strip("\x1e\n")
    if not raw:
        return []

    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        parts = record.strip("\n").split("\x1f", 2)
        if len(parts) < 2:
            continue
        sha, subject = parts[0], parts[1].strip()
        body = parts[2].strip() if len(parts) == 3 else ""
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def categorize(subject: str) -> str:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0]

    if prefix.startswith(("feat", "add")) or any(word in lowered for word in (" add ", "added ", "implement", "create ")):
        return "Added"
    if prefix.startswith(("fix", "bug")) or any(word in lowered for word in ("fix", "bug", "resolve", "patch")):
        return "Fixed"
    if prefix.startswith(("remove", "delete")) or any(word in lowered for word in ("remove", "delete", "drop ", "deprecat")):
        return "Removed"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    groups = {section: [] for section in SECTION_ORDER}
    for commit in commits:
        groups[categorize(commit.subject)].append(commit)
    return groups


def render_changelog(commits: list[Commit], tag: str | None) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    range_label = f"since `{tag}`" if tag else "from all commits"
    groups = grouped_commits(commits)

    lines = [
        "# Changelog",
        "",
        f"Generated on {generated_at} from Git history {range_label}.",
        "",
        "## Unreleased",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for section in SECTION_ORDER:
        lines.extend([f"### {section}", ""])
        section_commits = groups[section]
        if section_commits:
            for commit in section_commits:
                lines.append(f"- {commit.subject} ({commit.sha[:7]})")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines)


def generate(repo: Path, output: Path) -> str:
    repo = repo.resolve()
    tag = latest_tag(repo)
    commits = commits_since(repo, tag)
    changelog = render_changelog(commits, tag)
    output.write_text(changelog, encoding="utf-8")
    return changelog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from Git commits since the latest tag.")
    parser.add_argument("--repo", default=".", help="Path to the Git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path for the changelog.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    generate(Path(args.repo), output)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
