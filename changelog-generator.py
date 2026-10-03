#!/usr/bin/env python3

import re
import subprocess
import sys
from pathlib import Path

CATEGORIES = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "added": "Added",
    "fix": "Fixed",
    "fixed": "Fixed",
    "bugfix": "Fixed",
    "bug": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "update": "Changed",
    "updated": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "improve": "Changed",
    "improved": "Changed",
    "optimize": "Changed",
    "optimized": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
}

SKIP_PREFIXES = (
    "merge ",
    "revert merge ",
)


def run_git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "git command failed"
        )

    return result.stdout.strip()


def latest_tag(repo):
    try:
        return run_git(
            repo,
            "describe",
            "--tags",
            "--abbrev=0",
        )
    except Exception:
        return None


def is_merge_commit(subject):
    return subject.strip().lower().startswith(SKIP_PREFIXES)


def classify(subject):
    original = subject.strip()

    if not original:
        return None

    if is_merge_commit(original):
        return None

    match = re.match(
        r"^([A-Za-z]+)(?:\([^)]*\))?!?:\s*",
        original,
    )

    if match:
        prefix = match.group(1).lower()

        if prefix.startswith("revert"):
            return "Removed"

        if prefix in CATEGORIES:
            return CATEGORIES[prefix]

    lower = original.lower()

    if lower.startswith(("add ", "added ", "adding ")):
        return "Added"

    if lower.startswith(
        ("fix ", "fixed ", "fixes ", "bugfix ", "bug fix ")
    ):
        return "Fixed"

    if lower.startswith(
        ("remove ", "removed ", "removes ", "delete ", "deleted ")
    ):
        return "Removed"

    if lower.startswith(
        (
            "change ",
            "changed ",
            "changes ",
            "update ",
            "updated ",
            "updates ",
            "refactor ",
            "improve ",
            "improved ",
            "optimize ",
            "optimized ",
            "bump ",
        )
    ):
        return "Changed"

    if ":" in original:
        action = original.split(":", 1)[1].strip().lower()

        if action.startswith(("fix ", "fixed ", "fixes ")):
            return "Fixed"

        if action.startswith(("add ", "added ", "adding ")):
            return "Added"

        if action.startswith(
            ("remove ", "removed ", "delete ", "deleted ")
        ):
            return "Removed"

        if action.startswith(
            (
                "change ",
                "changed ",
                "update ",
                "updated ",
                "refactor ",
                "improve ",
                "optimized ",
                "optimize ",
            )
        ):
            return "Changed"

    return "Changed"


def get_commits(repo):
    tag = latest_tag(repo)

    if tag:
        output = run_git(
            repo,
            "log",
            f"{tag}..HEAD",
            "--pretty=format:%H%x09%s",
        )
    else:
        output = run_git(
            repo,
            "log",
            "--pretty=format:%H%x09%s",
        )

    commits = []

    for line in output.splitlines():
        if "\t" not in line:
            continue

        sha, subject = line.split("\t", 1)
        category = classify(subject)

        if category is None:
            continue

        commits.append(
            {
                "sha": sha,
                "subject": subject,
                "category": category,
            }
        )

    return tag, commits


def generate(repo):
    tag, commits = get_commits(repo)

    groups = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for commit in commits:
        groups[commit["category"]].append(commit)

    lines = [
        "# Changelog",
        "",
        "Generated automatically from git history.",
        "",
        "## Unreleased",
        "",
    ]

    for category in (
        "Added",
        "Fixed",
        "Changed",
        "Removed",
    ):
        entries = groups[category]

        if not entries:
            continue

        lines.append(f"### {category}")
        lines.append("")

        for commit in entries:
            lines.append(
                f"- {commit['subject']} "
                f"(`{commit['sha'][:8]}`)"
            )

        lines.append("")

    if tag:
        lines.append(f"_Changes since `{tag}`_")
    else:
        lines.append(
            "_Changes since repository history start._"
        )

    lines.append("")

    output = "\n".join(lines)

    output_path = Path(repo) / "CHANGELOG.md"

    output_path.write_text(
        output,
        encoding="utf-8",
    )

    print(output)


def main():
    if len(sys.argv) > 1:
        repo = Path(sys.argv[1]).expanduser().resolve()
    else:
        repo = Path.cwd()

    if not (repo / ".git").exists():
        print(
            f"ERROR: '{repo}' is not a Git repository.",
            file=sys.stderr,
        )
        print(
            "Usage: python3 changelog-generator.py [REPOSITORY]",
            file=sys.stderr,
        )
        sys.exit(1)

    generate(repo)


if __name__ == "__main__":
    main()
