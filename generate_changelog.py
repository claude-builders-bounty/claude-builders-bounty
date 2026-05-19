#!/usr/bin/env python3
import argparse
import subprocess
import sys
from datetime import datetime
from typing import Optional


CONVENTIONAL_PREFIXES = {
    "feat": "Added",
    "fix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "revert": "Removed",
    "docs": "Other",
    "test": "Other",
    "chore": "Other",
    "ci": "Other",
    "build": "Other",
}


def run(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def get_latest_tag() -> Optional[str]:
    tags = run("git", "tag", "--sort=-creatordate")
    return tags.splitlines()[0] if tags else None


def get_first_commit() -> str:
    return run("git", "rev-list", "--max-parents=0", "HEAD")


def get_commits_since(ref: str) -> list[tuple[str, str, str]]:
    log = run("git", "log", "--format=%h||%s||%ad", "--date=short", f"{ref}..HEAD")
    if not log:
        return []
    commits = []
    for line in log.splitlines():
        parts = line.split("||", 2)
        if len(parts) == 3:
            commits.append((parts[0], parts[1], parts[2]))
    return commits


def categorize(subject: str) -> tuple[str, str]:
    for prefix, category in CONVENTIONAL_PREFIXES.items():
        if subject.startswith(prefix) and (
            len(subject) > len(prefix) and subject[len(prefix)] in "(:"
        ):
            return category, subject
    return "Other", subject


def generate_changelog(
    version: str,
    since: str,
    output: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    commits = get_commits_since(since)
    if not commits:
        msg = f"No commits found since {since}"
        print(msg, file=sys.stderr)
        return msg

    sections: dict[str, list[str]] = {}
    for sha, subject, date in commits:
        category, display = categorize(subject)
        entry = f"- {sha} {display}"
        sections.setdefault(category, []).append(entry)

    category_order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [f"## [{version}] - {date_str}", ""]
    for cat in category_order:
        if cat in sections:
            lines.append(f"### {cat}")
            for entry in sections[cat]:
                lines.append(entry)
            lines.append("")

    changelog = "\n".join(lines)

    if dry_run:
        print(changelog)
        return changelog

    if output:
        with open(output, "w") as f:
            f.write(changelog)
        print(f"Wrote changelog to {output}")
    else:
        if run("test", "-f", "CHANGELOG.md"):
            content = run("cat", "CHANGELOG.md")
            if content:
                changelog = changelog + "\n" + content
        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)
        print("Wrote CHANGELOG.md")

    return changelog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--since", "-s",
        help="Git ref to start from (default: latest tag, or first commit)",
    )
    parser.add_argument(
        "--version", "-v",
        help="Version string for the changelog header (default: latest tag)",
        default=None,
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: CHANGELOG.md)",
        default=None,
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print changelog to stdout without writing",
    )
    args = parser.parse_args()

    since = args.since or get_latest_tag() or get_first_commit()
    version = args.version or get_latest_tag() or "HEAD"

    generate_changelog(
        version=version,
        since=since,
        output=args.output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
