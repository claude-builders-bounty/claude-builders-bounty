#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        if allow_failure:
            return ""
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.rstrip("\r\n")


def latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True).strip()
    return tag or None


def read_commits(repo: Path, since: str | None) -> list[Commit]:
    revision_range = f"{since}..HEAD" if since else "HEAD"
    output = run_git(repo, "log", revision_range, "--pretty=format:%H%x1f%s%x1f%b%x1e", allow_failure=True)
    commits: list[Commit] = []

    for record in output.split("\x1e"):
        record = record.strip("\r\n")
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(sha=parts[0], subject=parts[1].strip(), body=parts[2].strip()))

    return commits


def categorize(subject: str) -> str:
    normalized = subject.strip().lower()
    prefix = normalized.split(":", 1)[0].split("(", 1)[0]

    if prefix in {"feat", "feature"} or normalized.startswith(("add ", "adds ", "added ")):
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"} or "fix" in normalized or "bug" in normalized:
        return "Fixed"
    if prefix in {"remove", "removed"} or normalized.startswith(("remove ", "delete ", "drop ", "deprecate ")):
        return "Removed"
    return "Changed"


def render_changelog(repo: Path, commits: list[Commit], since: str | None) -> str:
    today = dt.date.today().isoformat()
    repo_name = repo.resolve().name
    range_label = f"since `{since}`" if since else "from full git history"
    grouped = {category: [] for category in CATEGORIES}

    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"Generated for `{repo_name}` on {today}, using commits {range_label}.",
        "",
        f"## {today}",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        if grouped[category]:
            for commit in grouped[category]:
                lines.append(f"- {commit.subject} (`{commit.sha[:7]}`)")
        else:
            lines.append("- No entries.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown path. Defaults to CHANGELOG.md.")
    parser.add_argument("--since", default=None, help="Git tag or revision to use instead of the latest tag.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()

    if not (repo / ".git").exists():
        raise SystemExit(f"{repo} is not a git repository")

    since = args.since or latest_tag(repo)
    commits = read_commits(repo, since)
    changelog = render_changelog(repo, commits, since)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo / output_path
    output_path.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
