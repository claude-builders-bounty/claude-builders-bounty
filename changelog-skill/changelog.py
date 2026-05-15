#!/usr/bin/env python3
"""
CHANGELOG Generator — generates structured Keep-a-Changelog formatted
CHANGELOG.md from git history using conventional commit classification.

Usage:
    python changelog.py                    # since last git tag
    python changelog.py v1.0.0             # since v1.0.0
    python changelog.py v1.0.0 v2.0.0      # between two tags
    python changelog.py --stdout            # print to stdout only
"""

import subprocess
import sys
from collections import defaultdict
from datetime import datetime

CATEGORIES = {
    "Added": ["feat", "add", "added", "feature"],
    "Fixed": ["fix", "bug", "fixed", "hotfix", "patch"],
    "Changed": ["change", "update", "updated", "refactor", "tweak", "chore"],
    "Removed": ["remove", "removed", "drop", "dropped", "delete", "deleted"],
    "Deprecated": ["deprecate", "deprecated"],
    "Security": ["security", "secure", "vuln", "cve"],
}

IGNORE_PREFIXES = ["Merge", "Bump", "Release", "CI", "ci(", "test("]


def git(*args):
    return subprocess.check_output(["git"] + list(args), text=True).strip()


def resolve_range(argv):
    """Determine the commit range from CLI args."""
    if len(argv) >= 3:
        return f"{argv[1]}..{argv[2]}"
    if len(argv) == 2:
        return f"{argv[1]}..HEAD"
    try:
        last_tag = git("describe", "--tags", "--abbrev=0")
        return f"{last_tag}..HEAD"
    except subprocess.CalledProcessError:
        print("No git tags found. Using all commits.", file=sys.stderr)
        return "HEAD"


def parse_conventional_prefix(subject):
    """Extract conventional commit type & scope, return (type, message)."""
    clean = subject.strip()
    # conventional: type(scope): message
    if "(" in clean and "):" in clean:
        before = clean[: clean.index("):") + 1]
        prefix = before.split("(")[0].strip().lower()
        message = clean[clean.index("):") + 2 :].strip()
        return prefix, message
    # conventional: type: message
    if ": " in clean:
        prefix = clean[: clean.index(":")].strip().lower()
        message = clean[clean.index(":") + 2 :].strip()
        return prefix, message
    return None, clean


def classify(subject):
    """Classify a commit subject into a changelog category."""
    prefix, message = parse_conventional_prefix(subject)

    if prefix:
        for category, keywords in CATEGORIES.items():
            if prefix in keywords:
                return category, message
        return "Other", subject

    # fallback: check first word
    first_word = subject.split()[0].lower().rstrip(":")
    for category, keywords in CATEGORIES.items():
        if first_word in keywords:
            return category, " ".join(subject.split()[1:])

    return "Other", subject


def should_ignore(subject):
    return any(subject.strip().startswith(p) for p in IGNORE_PREFIXES)


def generate_changelog(commit_range):
    """Get commits for range and group by category."""
    log = git("log", commit_range, "--oneline", "--no-merges", "--format=%h %s")
    if not log:
        return None

    grouped = defaultdict(list)
    for line in log.split("\n"):
        line = line.strip()
        if not line or should_ignore(line):
            continue
        # strip short hash
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        _, subject = parts
        category, message = classify(subject)
        grouped[category].append(f"- {message}")

    if not grouped:
        return None
    return grouped


def format_title(commit_range):
    parts = commit_range.split("..")
    if len(parts) == 2 and parts[0] != "HEAD":
        return f"{parts[0]}..{parts[1]}"
    return "Unreleased"


def write_changelog(grouped, commit_range, out_file):
    now = datetime.utcnow().strftime("%Y-%m-%d")
    title = format_title(commit_range)

    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append(f"## [{title}] — {now}")
    lines.append("")

    order = ["Added", "Changed", "Fixed", "Security", "Deprecated", "Removed", "Other"]
    for category in order:
        entries = grouped.get(category, [])
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for entry in sorted(entries):
            lines.append(entry)
        lines.append("")

    if out_file:
        # prepend or create
        existing = ""
        try:
            with open(out_file, encoding="utf-8") as f:
                existing = f.read()
        except FileNotFoundError:
            pass
        new_block = "\n".join(lines) + "\n"
        if existing and existing.startswith("# Changelog"):
            # insert after header
            header_end = existing.find("\n##")
            if header_end == -1:
                header_end = existing.find("\n---")
            if header_end == -1:
                header_end = len(existing)
            final = existing[:header_end].rstrip() + "\n\n" + new_block + existing[header_end:].lstrip()
        else:
            final = new_block + "\n---\n\n" + existing
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"CHANGELOG.md updated ({out_file})")

    return "\n".join(lines)


def main():
    stdout_only = "--stdout" in sys.argv
    args = [a for a in sys.argv if a != "--stdout"]

    commit_range = resolve_range(args)
    grouped = generate_changelog(commit_range)
    if grouped is None:
        print("No commits found for range:", commit_range, file=sys.stderr)
        sys.exit(1)

    out_file = None if stdout_only else "CHANGELOG.md"
    output = write_changelog(grouped, commit_range, out_file)

    if stdout_only:
        print(output)


if __name__ == "__main__":
    main()