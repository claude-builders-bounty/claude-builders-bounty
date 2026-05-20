#!/usr/bin/env python3
"""Categorize git commits into CHANGELOG sections using conventional commit parsing."""

import sys
import re
import argparse
from datetime import date
from collections import defaultdict

# Conventional commit prefixes mapped to changelog categories
CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "added": "Added",
    "new": "Added",
    "fix": "Fixed",
    "fixed": "Fixed",
    "bugfix": "Fixed",
    "bug": "Fixed",
    "patch": "Fixed",
    "hotfix": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "update": "Changed",
    "updated": "Changed",
    "refactor": "Changed",
    "improve": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "rename": "Changed",
    "move": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "deprecate": "Removed",
    "deprecated": "Removed",
    "drop": "Removed",
}

# Keyword patterns for fallback categorization (when no prefix matches)
KEYWORD_PATTERNS = {
    "Added": [
        r"\badd(ed|s|ing)?\b",
        r"\bintroduc(e|ed|ing)\b",
        r"\bimplement(ed|s)?\b",
        r"\bcreate[ds]?\b",
        r"\bnew\b",
        r"\bsupport\b",
        r"\benable[ds]?\b",
    ],
    "Fixed": [
        r"\bfix(ed|es|ing)?\b",
        r"\bresolve[ds]?\b",
        r"\brepair(ed)?\b",
        r"\bcorrect(ed|s)?\b",
        r"\bpatch(ed)?\b",
        r"\bbug\b",
    ],
    "Changed": [
        r"\bupdate[ds]?\b",
        r"\brefactor(ed|s)?\b",
        r"\bmodif(y|ied|ies)\b",
        r"\bimprov(e|ed|es|ing)\b",
        r"\boptimiz(e|ed)\b",
        r"\bmigrat(e|ed|ing)\b",
        r"\brenam(e|ed|ing)\b",
        r"\bmov(e|ed|ing)\b",
        r"\breplace[ds]?\b",
        r"\bupgrad(e|ed|ing)\b",
        r"\bbump(ed|s)?\b",
    ],
    "Removed": [
        r"\bremov(e|ed|es|ing)\b",
        r"\bdelet(e|ed|es|ing)\b",
        r"\bdrop(ped|s)?\b",
        r"\bdeprecate[ds]?\b",
        r"\bclean(ed)?\s*up\b",
    ],
}


def parse_conventional_commit(message: str) -> tuple[str, str]:
    """Parse conventional commit format: type(scope): description."""
    pattern = r"^(\w+)(?:\(.+?\))?[!]?:\s*(.+)$"
    match = re.match(pattern, message.strip())
    if match:
        prefix = match.group(1).lower()
        description = match.group(2).strip()
        return prefix, description
    return "", message.strip()


def categorize_by_keywords(message: str) -> str:
    """Fallback: categorize by scanning message for keywords."""
    msg_lower = message.lower()
    scores = defaultdict(int)

    for category, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                scores[category] += 1

    if scores:
        return max(scores, key=scores.get)
    return "Changed"  # Default category


def categorize_commit(message: str) -> tuple[str, str]:
    """Return (category, clean_description) for a commit message."""
    prefix, description = parse_conventional_commit(message)

    if prefix and prefix in CATEGORY_MAP:
        return CATEGORY_MAP[prefix], description

    # Fallback to keyword analysis on full message
    category = categorize_by_keywords(message)
    return category, message.strip()


def generate_changelog(commits: list[dict], version: str, output: str):
    """Generate CHANGELOG.md content from categorized commits."""
    categories = defaultdict(list)

    for commit in commits:
        category, description = categorize_commit(commit["message"])
        # Capitalize first letter of description
        if description:
            description = description[0].upper() + description[1:]
        categories[category].append(
            {"description": description, "author": commit["author"], "date": commit["date"]}
        )

    # Build markdown
    lines = []
    lines.append("# Changelog\n")
    lines.append(f"## [{version}] - {date.today().isoformat()}\n")

    # Order: Added, Changed, Fixed, Removed
    section_order = ["Added", "Changed", "Fixed", "Removed"]

    for section in section_order:
        if section in categories:
            lines.append(f"### {section}\n")
            for entry in categories[section]:
                lines.append(f"- {entry['description']}")
            lines.append("")

    content = "\n".join(lines).rstrip() + "\n"

    # Write or print
    if output == "-":
        sys.stdout.write(content)
    else:
        # If file exists, prepend new section after header
        try:
            with open(output, "r") as f:
                existing = f.read()
            # Insert after the first "# Changelog" header
            if existing.startswith("# Changelog"):
                header = "# Changelog\n"
                rest = existing[len(header):]
                new_section = "\n".join(lines[1:]).rstrip() + "\n"
                content = header + "\n" + new_section + "\n" + rest.lstrip("\n")
        except FileNotFoundError:
            pass

        with open(output, "w") as f:
            f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Categorize commits for CHANGELOG")
    parser.add_argument("--version", default="Unreleased", help="Version label")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file (- for stdout)")
    args = parser.parse_args()

    commits = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|||")
        if len(parts) >= 4:
            commits.append(
                {
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                }
            )

    if not commits:
        print("No commits to process.", file=sys.stderr)
        sys.exit(0)

    generate_changelog(commits, args.version, args.output)


if __name__ == "__main__":
    main()
