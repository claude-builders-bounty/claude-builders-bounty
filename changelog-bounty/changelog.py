#!/usr/bin/env python3
"""Deterministic CHANGELOG generator based on git history."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
PREFIXES = {
    "feat": "Added", "feature": "Added", "add": "Added", "added": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "fixed": "Fixed", "hotfix": "Fixed",
    "change": "Changed", "changed": "Changed", "refactor": "Changed",
    "perf": "Changed", "docs": "Changed", "chore": "Changed",
    "remove": "Removed", "removed": "Removed", "delete": "Removed",
}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def latest_tag(repo: Path) -> str | None:
    # `describe` selects the nearest reachable tag, avoiding unrelated tags.
    result = subprocess.run(["git", "-C", str(repo), "describe", "--tags",
                             "--abbrev=0", "HEAD"], text=True,
                            capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def classify(subject: str) -> str:
    match = re.match(r"^([A-Za-z]+)(?:\([^)]*\))?!?:\s+", subject)
    if match:
        return PREFIXES.get(match.group(1).lower(), "Changed")
    lowered = subject.lower()
    if re.match(r"^(remove|delete|drop|deprecate)[\s:-]", lowered):
        return "Removed"
    if re.match(r"^(fix|repair|resolve|correct|patch)[\s:-]", lowered):
        return "Fixed"
    if re.match(r"^(add|introduce|support|implement|create)[\s:-]", lowered):
        return "Added"
    return "Changed"


def commits(repo: Path, tag: str | None) -> list[tuple[str, str]]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    raw = git(repo, "log", revision, "--no-merges", "--date-order",
               "--format=%H%x09%s")
    rows = []
    for line in raw.splitlines():
        if "\t" in line:
            sha, subject = line.split("\t", 1)
            rows.append((sha, subject.strip()))
    return rows


def remote_url(repo: Path) -> str | None:
    try:
        url = git(repo, "config", "--get", "remote.origin.url").strip()
    except RuntimeError:
        return None
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    if url.endswith(".git"):
        url = url[:-4]
    return url if url.startswith(("http://", "https://")) else None


def render(repo: Path, output: Path) -> str:
    tag = latest_tag(repo)
    rows = commits(repo, tag)
    base = remote_url(repo)
    grouped = {category: [] for category in CATEGORIES}
    for sha, subject in rows:
        short = sha[:7]
        entry = f"{subject} ([{short}]({base}/commit/{sha}))" if base else f"{subject} ({short})"
        grouped[classify(subject)].append(entry)
    heading = f"Unreleased (since {tag})" if tag else "Unreleased (all commits; no git tag found)"
    lines = ["# Changelog", "", f"## {heading}", ""]
    if not rows:
        lines.append("No changes recorded.")
        lines.append("")
    else:
        for category in CATEGORIES:
            lines.append(f"### {category}")
            lines.extend(f"- {entry}" for entry in grouped[category])
            lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    return output.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic CHANGELOG.md from git commits")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = (args.output or repo / "CHANGELOG.md").resolve()
    try:
        render(repo, output)
    except RuntimeError as error:
        parser.error(str(error))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
