#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "feature", "add", "added"),
    "Fixed": ("fix", "fixed", "bug", "bugfix", "patch"),
    "Changed": (
        "change",
        "changed",
        "chore",
        "ci",
        "build",
        "docs",
        "doc",
        "perf",
        "refactor",
        "style",
        "test",
        "update",
        "updated",
    ),
    "Removed": ("remove", "removed", "delete", "deleted", "drop", "dropped"),
}


def run_git(repo, *args, allow_failure=False):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result


def last_tag(repo):
    result = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    if result.returncode:
        return None
    return result.stdout.strip() or None


def commits_since(repo, tag):
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    result = run_git(
        repo,
        "log",
        "--reverse",
        "--pretty=format:%h%x1f%s",
        revision_range,
    )
    commits = []
    for line in result.stdout.splitlines():
        short_hash, _, subject = line.partition("\x1f")
        if subject:
            commits.append((short_hash, subject))
    return commits


def split_subject(subject):
    match = re.match(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?!?:\s*(?P<summary>.+)$", subject)
    if match:
        return match.group("type").lower(), match.group("summary").strip()

    lowered = subject.lower()
    first_word = re.split(r"[\s:-]+", lowered, maxsplit=1)[0]
    return first_word, subject.strip()


def category_for(commit_type):
    for category, prefixes in CATEGORIES.items():
        if commit_type in prefixes:
            return category
    return "Changed"


def categorize(commits):
    grouped = {category: [] for category in CATEGORIES}
    for short_hash, subject in commits:
        commit_type, summary = split_subject(subject)
        category = category_for(commit_type)
        grouped[category].append((summary, short_hash))
    return grouped


def render_changelog(grouped, tag):
    lines = ["# Changelog", "", "## Unreleased", ""]
    if tag:
        lines.append(f"Changes since `{tag}`.")
    else:
        lines.append("Changes from the first commit.")
    lines.append("")

    has_changes = False
    for category in ("Added", "Fixed", "Changed", "Removed"):
        entries = grouped[category]
        if not entries:
            continue
        has_changes = True
        lines.append(f"### {category}")
        lines.append("")
        for summary, short_hash in entries:
            lines.append(f"- {summary} (`{short_hash}`)")
        lines.append("")

    if not has_changes:
        lines.append("No changes found.")
        lines.append("")

    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from commits since the last git tag."
    )
    parser.add_argument("--repo", default=".", help="Git repository to inspect.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Markdown file to write.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    repo = Path(args.repo).resolve()
    output_arg = Path(args.output)
    output = output_arg if output_arg.is_absolute() else repo / output_arg

    inside = run_git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip()
    if inside != "true":
        raise RuntimeError(f"{repo} is not a git repository")

    tag = last_tag(repo)
    commits = commits_since(repo, tag)
    changelog = render_changelog(categorize(commits), tag)
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"generate-changelog: {exc}", file=sys.stderr)
        sys.exit(1)
