#!/usr/bin/env python3
"""Generate a Keep-a-Changelog formatted CHANGELOG from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CATEGORY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Added", re.compile(r"^(feat|add|new)(\(.+\))?!?:", re.I)),
    ("Fixed", re.compile(r"^(fix|bug|hotfix)(\(.+\))?!?:", re.I)),
    ("Changed", re.compile(r"^(change|refactor|perf|style|chore)(\(.+\))?!?:", re.I)),
    ("Removed", re.compile(r"^(remove|drop|delete)(\(.+\))?!?:", re.I)),
    ("Security", re.compile(r"^security(\(.+\))?!?:", re.I)),
]

NATURAL_KEYWORDS: dict[str, str] = {
    "add": "Added",
    "added": "Added",
    "introduce": "Added",
    "fix": "Fixed",
    "fixed": "Fixed",
    "bug": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "refactor": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "security": "Security",
}


@dataclass
class Commit:
    sha: str
    date: str
    subject: str
    breaking: bool


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    try:
        return run_git(repo, "describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def detect_version(repo: Path) -> str:
    for name in ("package.json", "pyproject.toml", "Cargo.toml", "setup.py"):
        path = repo / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if name == "package.json":
            m = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        elif name == "pyproject.toml":
            m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
        elif name == "Cargo.toml":
            m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
        else:
            m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return m.group(1)
    return "Unreleased"


def categorize(subject: str) -> str:
    for category, pattern in CATEGORY_RULES:
        if pattern.match(subject):
            return category
    lowered = subject.lower()
    for keyword, category in NATURAL_KEYWORDS.items():
        if keyword in lowered:
            return category
    return "Changed"


def is_breaking(subject: str, body: str) -> bool:
    if subject.endswith("!") or "!" in subject.split(":", 1)[0]:
        return True
    return "breaking change" in f"{subject}\n{body}".lower()


def load_commits(repo: Path, since: str | None) -> list[Commit]:
    fmt = "%H%x00%ad%x00%s"
    args = ["log", f"--pretty=format:{fmt}", "--date=short"]
    if since:
        args.append(f"{since}..HEAD")
    else:
        tag = latest_tag(repo)
        if tag:
            args.append(f"{tag}..HEAD")
    raw = run_git(repo, *args)
    commits: list[Commit] = []
    if not raw:
        return commits
    for line in raw.splitlines():
        sha, date, subject = line.split("\x00", 2)
        body = ""
        try:
            body = run_git(repo, "log", "-1", f"--pretty=format:%b", sha)
        except subprocess.CalledProcessError:
            pass
        commits.append(
            Commit(
                sha=sha[:7],
                date=date,
                subject=subject.strip(),
                breaking=is_breaking(subject, body),
            )
        )
    return commits


def render(version: str, commits: list[Commit]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grouped: dict[str, list[Commit]] = {k: [] for k, _ in CATEGORY_RULES}
    breaking: list[Commit] = []
    for commit in commits:
        if commit.breaking:
            breaking.append(commit)
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version}] - {today}",
        "",
    ]
    if breaking:
        lines.append("### ⚠ BREAKING CHANGES")
        lines.append("")
        for c in breaking:
            lines.append(f"- {c.subject} ({c.sha})")
        lines.append("")

    for category, _ in CATEGORY_RULES:
        items = grouped[category]
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for c in items:
            lines.append(f"- {c.subject} ({c.sha})")
        lines.append("")

    if len(lines) == 5:
        lines.append("### Changed")
        lines.append("")
        lines.append("- No commits since last tag.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path to git repository")
    parser.add_argument("--since", help="Git ref to start from (default: latest tag)")
    parser.add_argument("--version", help="Version heading (default: auto-detect)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of writing")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 1

    version = args.version or detect_version(repo)
    commits = load_commits(repo, args.since)
    content = render(version, commits)

    if args.dry_run:
        print(content, end="")
        return 0

    out = Path(args.output)
    if not out.is_absolute():
        out = repo / out
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out} ({len(commits)} commits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
