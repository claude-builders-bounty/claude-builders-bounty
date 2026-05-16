#!/usr/bin/env python3
"""
generate_changelog.py — Generate structured CHANGELOG.md from git history.

Usage:
    python3 generate_changelog.py [output_file]

No external dependencies required (stdlib only).
"""

import subprocess
import sys
import re
from datetime import date
from collections import defaultdict

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"

# Conventional commit patterns
CATEGORY_PATTERNS = {
    "Added": [
        r"^feat(\(.+?\))?[!:]",
        r"^add(\(.+?\))?[!:]",
        r"^added[!:]",
        r"^(add|implement|create|introduce|new) ",
    ],
    "Fixed": [
        r"^fix(\(.+?\))?[!:]",
        r"^bugfix(\(.+?\))?[!:]",
        r"^hotfix(\(.+?\))?[!:]",
        r"^fixed[!:]",
        r"^(fix|resolve|patch|correct) ",
    ],
    "Changed": [
        r"^refactor(\(.+?\))?[!:]",
        r"^change(\(.+?\))?[!:]",
        r"^update(\(.+?\))?[!:]",
        r"^improve(\(.+?\))?[!:]",
        r"^perf(\(.+?\))?[!:]",
        r"^style(\(.+?\))?[!:]",
        r"^(update|change|modify|refactor|improve|optimize) ",
    ],
    "Removed": [
        r"^remove(\(.+?\))?[!:]",
        r"^delete(\(.+?\))?[!:]",
        r"^deprecate(\(.+?\))?[!:]",
        r"^(remove|delete|drop|deprecate) ",
    ],
}


def run_git(*args):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def get_last_tag():
    """Get the most recent git tag, or the root commit."""
    out, rc = run_git("describe", "--tags", "--abbrev=0")
    if rc == 0 and out:
        return out
    # No tags — use root commit
    out, _ = run_git("rev-list", "--max-parents=0", "HEAD")
    return out.split("\n")[0] if out else None


def get_commits_since(ref):
    """Get commit messages since a given ref."""
    if ref:
        out, rc = run_git("log", f"{ref}..HEAD", "--pretty=format:%s")
    else:
        out, rc = run_git("log", "--pretty=format:%s")
    if not out:
        return []
    return [line for line in out.split("\n") if line.strip()]


def categorize(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    lower = message.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, lower):
                return category
    return "Other"


def clean_message(message):
    """Remove conventional commit prefix for cleaner display."""
    # Remove prefix like "feat(scope): " or "fix: "
    cleaned = re.sub(r"^[a-z]+(\(.+?\))?[!]?:\s*", "", message)
    return cleaned if cleaned else message


def main():
    last_tag = get_last_tag()
    if not last_tag:
        print("Error: Not a git repository or no commits found.")
        sys.exit(1)

    commits = get_commits_since(last_tag)
    if not commits:
        print(f"No new commits since {last_tag}. Nothing to generate.")
        sys.exit(0)

    # Categorize all commits
    categorized = defaultdict(list)
    for msg in commits:
        category = categorize(msg)
        cleaned = clean_message(msg)
        categorized[category].append(cleaned)

    # Build CHANGELOG
    today = date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        f"## [Unreleased] — {today}",
        "",
    ]

    # Output in order: Added, Fixed, Changed, Removed, Other
    for section in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        if section in categorized and categorized[section]:
            lines.append(f"### {section}")
            for item in categorized[section]:
                lines.append(f"  - {item}")
            lines.append("")

    # Write output
    with open(OUTPUT, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ Generated {OUTPUT} ({len(lines)} lines)")
    print(f"   Commits processed: {len(commits)}")
    for section in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        if section in categorized:
            print(f"   {section}: {len(categorized[section])}")


if __name__ == "__main__":
    main()
