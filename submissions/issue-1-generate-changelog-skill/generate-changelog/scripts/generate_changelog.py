#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def repo_root(path: Path) -> Path:
    result = git(path, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip())


def latest_tag(repo: Path) -> str | None:
    result = git(repo, "describe", "--tags", "--abbrev=0", check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commits_since(repo: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    result = git(
        repo,
        "log",
        "--reverse",
        "--pretty=format:%H%x1f%s%x1f%b%x1e",
        revision_range,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    commits: list[Commit] = []
    for raw in result.stdout.strip("\x1e\n").split("\x1e"):
        parts = raw.strip("\n").split("\x1f")
        if len(parts) < 3:
            continue
        commits.append(Commit(sha=parts[0], subject=parts[1].strip(), body=parts[2].strip()))
    return commits


def categorize(commit: Commit) -> str:
    text = f"{commit.subject}\n{commit.body}".lower()
    subject = commit.subject.lower()
    if "breaking change" in text or subject.startswith(("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecat")):
        return "Removed"
    if subject.startswith(("fix", "bug", "repair", "resolve", "resolved")) or any(word in text for word in (" bug", " regression", " hotfix")):
        return "Fixed"
    if subject.startswith(("feat", "add", "added", "implement", "implemented", "introduce", "introduced")):
        return "Added"
    return "Changed"


def render_changelog(commits: list[Commit], tag: str | None) -> str:
    groups = {category: [] for category in CATEGORIES}
    for commit in commits:
        groups[categorize(commit)].append(commit)

    range_line = f"Changes since `{tag}`." if tag else "No git tag found; includes all reachable commits."
    lines = [
        "# Changelog",
        "",
        "## Unreleased",
        "",
        range_line,
        "",
    ]
    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        items = groups[category]
        if items:
            for commit in items:
                lines.append(f"- {commit.subject} (`{commit.sha[:7]}`)")
        else:
            lines.append("- None.")
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history since the latest tag.")
    parser.add_argument("--repo", default=".", help="Repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path relative to repo unless absolute.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing the output file.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root(Path(args.repo).resolve())
    tag = latest_tag(root)
    changelog = render_changelog(commits_since(root, tag), tag)
    if args.stdout:
        print(changelog, end="")
        return 0
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.write_text(changelog)
    print(f"changelog={output}")
    print(f"latest_tag={tag or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
