#!/usr/bin/env python3
"""Generate a categorized Markdown changelog for commits after the nearest tag."""
import argparse
import html
from pathlib import Path
import re
import subprocess
import sys

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$", re.DOTALL)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True,
    ).stdout.strip()


def categorize(subject):
    subject = subject.strip() or "(no commit subject)"
    match = CONVENTIONAL.match(subject)
    kind, scope, breaking, message = match.groups() if match else ("", None, None, subject)
    word = (kind or message.split(maxsplit=1)[0]).lower()
    if word in {"feat", "feature", "add", "added", "adds", "introduce"}:
        category = "Added"
    elif word in {"fix", "fixed", "fixes", "bugfix", "hotfix", "repair"}:
        category = "Fixed"
    elif word in {"remove", "removed", "removes", "delete", "deleted", "drop"}:
        category = "Removed"
    else:
        category = "Changed"
    description = (f"{scope}: " if scope else "") + message
    if breaking:
        description += " (breaking change)"
    return category, description


def markdown_text(value):
    # Preserve literal subjects as a single Markdown list entry.
    value = html.escape(" ".join(value.split()), quote=False)
    return re.sub(r"([\\`*_\[\]])", r"\\\1", value)


def generate(repo):
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    try:
        head = git(root, "rev-parse", "--verify", "HEAD")
    except subprocess.CalledProcessError:
        head = None
    tag = None
    groups = {name: [] for name in CATEGORIES}
    if head:
        try:
            tag = git(root, "describe", "--tags", "--abbrev=0", head)
        except subprocess.CalledProcessError:
            pass
        base = git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}") if tag else None
        revision = f"{base}..{head}" if base else head
        log = git(root, "log", "--no-merges", "--reverse", "--format=%H%x00%s", revision, "--")
        for line in log.splitlines():
            if not line:
                continue
            sha, subject = line.split("\0", 1)
            category, description = categorize(subject)
            groups[category].append(f"- {markdown_text(description)} (`{sha[:12]}`)")
    lines = ["# Changelog", "", "## [Unreleased]", ""]
    if tag:
        lines += [f"Changes since {markdown_text(tag)} (exclusive).", ""]
    else:
        lines += ["No reachable tag; includes all non-merge commits on HEAD.", ""]
    for category, entries in groups.items():
        lines += [f"### {category}", "", *(entries or ["_None._"]), ""]
    return root, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git working tree (default: current directory)")
    parser.add_argument("--output", help="Output path, relative to the current directory")
    parser.add_argument("--stdout", action="store_true", help="Print Markdown without writing a file")
    args = parser.parse_args()
    if args.stdout and args.output:
        parser.error("--stdout and --output cannot be combined")
    try:
        root, content = generate(args.repo)
        if args.stdout:
            sys.stdout.write(content)
        else:
            output = Path(args.output) if args.output else root / "CHANGELOG.md"
            output.write_text(content, encoding="utf-8")
            print(f"Wrote {output}", file=sys.stderr)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"changelog: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
