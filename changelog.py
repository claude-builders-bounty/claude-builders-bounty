#!/usr/bin/env python3
"""Generate a categorized Markdown changelog from Git commit subjects."""

import argparse
import subprocess
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
PREFIXES = {
    "Added": ("feat", "add", "new"),
    "Fixed": ("fix", "bugfix", "bug"),
    "Removed": ("remove", "removed", "delete", "deleted"),
}


def run_git(repo, *args, allow_failure=False):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result


def commit_subjects(repo):
    # Validate the repository separately: an unborn repository legitimately has
    # no HEAD, while a non-repository must fail before any output is written.
    run_git(repo, "rev-parse", "--git-dir")
    if run_git(repo, "rev-parse", "--verify", "HEAD", allow_failure=True).returncode:
        return []
    tag = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    revision = f"refs/tags/{tag.stdout.strip()}..HEAD" if tag.returncode == 0 else "HEAD"
    output = run_git(repo, "log", revision, "--format=%s%x00").stdout
    return [subject.strip() for subject in output.split("\0") if subject.strip()]


def categorize(subject):
    prefix, separator, remainder = subject.partition(":")
    normalized = prefix.lower().split("(", 1)[0].strip()
    text = remainder.strip() if separator and remainder.strip() else subject.strip()
    for category, prefixes in PREFIXES.items():
        if normalized in prefixes:
            return category, text
    return "Changed", text


def render(subjects):
    grouped = {category: [] for category in CATEGORIES}
    for subject in subjects:
        category, text = categorize(subject)
        grouped[category].append(text)

    lines = ["# Changelog", ""]
    for category in CATEGORIES:
        lines.append(f"## {category}")
        entries = grouped[category]
        lines.extend(f"- {entry}" for entry in entries)
        if not entries:
            lines.append("- No changes.")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    try:
        content = render(commit_subjects(args.repo.resolve()))
    except RuntimeError as exc:
        parser.error(str(exc))
    if args.stdout:
        print(content, end="")
    else:
        output = args.output if args.output.is_absolute() else args.repo / args.output
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
