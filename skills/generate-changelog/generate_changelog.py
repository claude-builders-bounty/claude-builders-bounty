#!/usr/bin/env python3
import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass
class Commit:
    subject: str
    short_hash: str


def run_git(args):
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def latest_tag():
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except RuntimeError:
        return ""


def load_commits(since):
    revision = f"{since}..HEAD" if since else "HEAD"
    output = run_git(["log", revision, "--pretty=format:%s%x1f%h"])
    commits = []
    for line in output.splitlines():
        if not line.strip():
            continue
        subject, _, short_hash = line.partition("\x1f")
        commits.append(Commit(subject=subject.strip(), short_hash=short_hash.strip()))
    return commits


def clean_subject(subject):
    if ":" in subject:
        prefix, rest = subject.split(":", 1)
        if prefix.replace("!", "").split("(")[0].lower() in {
            "feat",
            "fix",
            "refactor",
            "perf",
            "docs",
            "style",
            "test",
            "chore",
            "remove",
            "delete",
            "drop",
            "deprecate",
            "breaking",
        }:
            return rest.strip()
    return subject.strip()


def categorize(subject):
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0].replace("!", "").split("(")[0]

    if prefix == "feat":
        return "Added"
    if prefix == "fix":
        return "Fixed"
    if prefix in {"remove", "delete", "drop", "deprecate"}:
        return "Removed"
    if prefix in {"refactor", "perf", "docs", "style", "test", "chore", "ci", "build"}:
        return "Changed"

    if any(word in lowered for word in ("remove", "delete", "drop", "deprecat")):
        return "Removed"
    if any(word in lowered for word in ("fix", "bug", "repair", "correct")):
        return "Fixed"
    if any(word in lowered for word in ("add", "new", "introduce", "create")):
        return "Added"
    return "Changed"


def build_changelog(commits, since):
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    date = dt.date.today().isoformat()
    title = "Unreleased" if not since else f"Changes since {since}"
    lines = [
        "# Changelog",
        "",
        f"## {title} - {date}",
        "",
    ]
    for category in CATEGORIES:
        lines.append(f"### {category}")
        items = grouped[category]
        if items:
            for item in items:
                text = clean_subject(item.subject)
                suffix = f" ({item.short_hash})" if item.short_hash else ""
                lines.append(f"- {text}{suffix}")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--since", help="Git tag or revision to start from. Defaults to latest tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    since = args.since if args.since is not None else latest_tag()
    commits = load_commits(since)
    changelog = build_changelog(commits, since)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} with {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
