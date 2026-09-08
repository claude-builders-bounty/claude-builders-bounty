"""Generate the Unreleased changelog section from local Git history."""

import argparse
from pathlib import Path
import re
import subprocess
import sys


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
TYPES = {"feat": "Added", "feature": "Added", "add": "Added",
         "fix": "Fixed", "bugfix": "Fixed", "remove": "Removed",
         "removed": "Removed", "delete": "Removed"}


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=check,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )


def make_section(repo):
    git(repo, "rev-parse", "--verify", "HEAD")
    if git(repo, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise ValueError("Shallow history: fetch full history and tags before generating.")
    tag_result = git(repo, "describe", "--tags", "--abbrev=0", check=False)
    tag = tag_result.stdout.strip() if tag_result.returncode == 0 else None
    revision = f"{tag}..HEAD" if tag else "HEAD"
    history = git(repo, "log", "--reverse", "--no-merges", "--format=%h%x00%s", revision).stdout
    groups = {category: [] for category in CATEGORIES}
    for line in history.splitlines():
        sha, subject = line.split("\0", 1)
        conventional = re.match(r"^(\w+)(?:\([^)]*\))?(!)?:\s*(.*)$", subject)
        kind = conventional.group(1).lower() if conventional else subject.split()[0].lower()
        category = TYPES.get(kind, "Changed")
        subject = re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", subject)
        groups[category].append(f"- {subject} (`{sha}`)")
    lines = ["## [Unreleased]", ""]
    for category in CATEGORIES:
        if groups[category]:
            lines.extend([f"### {category}", "", *groups[category], ""])
    if not any(groups.values()):
        lines.extend(["No changes since the latest tag.", ""])
    return "\n".join(lines).rstrip() + "\n"


def update_document(existing, section):
    unreleased = re.search(r"^## \[?Unreleased\]?[^\n]*\n?", existing, re.MULTILINE)
    if unreleased:
        following = re.search(r"^## ", existing[unreleased.end():], re.MULTILINE)
        end = unreleased.end() + following.start() if following else len(existing)
        suffix = existing[end:]
        return existing[:unreleased.start()] + section + ("\n" + suffix if suffix else "")
    release = re.search(r"^## ", existing, re.MULTILINE)
    offset = release.start() if release else len(existing)
    prefix = existing[:offset].rstrip() or "# Changelog"
    suffix = existing[offset:]
    return prefix + "\n\n" + section + ("\n" + suffix if suffix else "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Defaults to repository root/CHANGELOG.md")
    args = parser.parse_args()
    try:
        root = Path(git(args.repo, "rev-parse", "--show-toplevel").stdout.strip())
        section = make_section(root)
        output = args.output or root / "CHANGELOG.md"
        existing = output.read_text(encoding="utf-8") if output.exists() else ""
        output.write_text(update_document(existing, section), encoding="utf-8")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Cannot generate changelog: {detail}", file=sys.stderr)
        return 1
    print(f"Updated {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
