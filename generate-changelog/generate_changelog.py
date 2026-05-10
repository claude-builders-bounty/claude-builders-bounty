#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Categorizes commits into Added / Fixed / Changed / Removed
based on conventional commit prefixes and keyword detection.

Usage:
    python generate_changelog.py [--from TAG] [--to TAG] [--output PATH] [--append] [--all] [--scope]
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── Categorization Rules ──────────────────────────────────────────

CATEGORIES = {
    "Added": [
        r"^feat(?:\([^)]*\))?:",
        r"(?i)\b(?:add(?:ed?|s)?|new|create|introduce|implement|support)\b",
    ],
    "Fixed": [
        r"^fix(?:\([^)]*\))?:",
        r"(?i)\b(?:fix(?:ed|es)?|bug|patch|resolve|repair|correct|crash|error)\b",
    ],
    "Changed": [
        r"^refactor(?:\([^)]*\))?:",
        r"^change(?:\([^)]*\))?:",
        r"(?i)\b(?:change|update|modify|improve|enhance|migrate|move|rename|bump|upgrade)\b",
    ],
    "Removed": [
        r"^remove(?:\([^)]*\))?:",
        r"(?i)\b(?:remove|delete|drop|deprecat|eliminate|strip)\b",
    ],
    "Breaking": [
        r"^breaking(?:\([^)]*\))?:",
        r"BREAKING\s+CHANGE",
    ],
    # Internal — skipped unless --all
    "Maintenance": [
        r"^(?:chore|docs|test|ci|build|style)(?:\([^)]*\))?:",
    ],
}

CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed"]
MAINTENANCE_LABEL = "Maintenance"


def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"git error: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def get_tags() -> list[str]:
    """Return all tags sorted by version/date (newest first)."""
    raw = run_git("tag", "--sort=-version:refname")
    return raw.splitlines() if raw else []


def get_latest_tag() -> str | None:
    """Return the most recent tag, or None."""
    tags = get_tags()
    return tags[0] if tags else None


def get_commits(from_ref: str | None, to_ref: str = "HEAD") -> list[dict]:
    """Return a list of commit dicts between from_ref and to_ref."""
    if from_ref:
        rev_range = f"{from_ref}..{to_ref}"
    else:
        rev_range = to_ref

    # Format: hash|subject|body|author|date
    fmt = "%H|%s|%b|%an|%aI"
    raw = run_git("log", rev_range, f"--format={fmt}", "--no-merges")

    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        sha, subject, body, author, date_iso = parts
        # Extract PR/issue numbers
        pr_match = re.search(r"\(#(\d+)\)", subject)
        pr_number = pr_match.group(1) if pr_match else None
        # Clean subject
        clean_subject = re.sub(r"\s*\(#\d+\)\s*$", "", subject).strip()

        commits.append({
            "sha": sha[:7],
            "subject": clean_subject,
            "body": body.strip(),
            "author": author,
            "date": date_iso[:10],  # YYYY-MM-DD
            "pr": pr_number,
            "raw_subject": subject,
        })
    return commits


def categorize_commit(commit: dict) -> str | None:
    """Return the category for a commit, or None to skip."""
    text = commit["raw_subject"] + "\n" + commit["body"]

    # Check Breaking first (highest priority)
    for pattern in CATEGORIES["Breaking"]:
        if re.search(pattern, text):
            return "Breaking"

    # Check main categories in order
    for cat in CATEGORY_ORDER:
        for pattern in CATEGORIES.get(cat, []):
            if re.search(pattern, text):
                return cat

    # Check maintenance
    for pattern in CATEGORIES.get("Maintenance", []):
        if re.search(pattern, text):
            return MAINTENANCE_LABEL

    # Unclassified → Changed (default)
    return "Changed"


def extract_scope(commit: dict) -> str | None:
    """Extract scope from conventional commit prefix like feat(scope):."""
    m = re.match(r"^[a-z]+(?:\(([^)]+)\)):", commit["raw_subject"])
    return m.group(1) if m else None


def format_entry(commit: dict, use_scope: bool = False) -> str:
    """Format a single commit as a changelog entry."""
    scope = extract_scope(commit) if use_scope else None
    subject = commit["subject"]

    # Add breaking marker
    cat = categorize_commit(commit)
    if cat == "Breaking":
        subject = f"⚠️ **BREAKING**: {subject}"

    # Add scope prefix
    if scope and use_scope:
        subject = f"**{scope}**: {subject}"

    # Add PR link
    if commit["pr"]:
        subject += f" (#{commit['pr']})"

    return f"- {subject}"


def generate_changelog(
    from_tag: str | None,
    to_tag: str = "HEAD",
    use_scope: bool = False,
    include_maintenance: bool = False,
) -> str:
    """Generate the full changelog content."""
    commits = get_commits(from_tag, to_tag)

    if not commits:
        print("No commits found in range.", file=sys.stderr)
        sys.exit(0)

    # Determine version and date
    if to_tag == "HEAD":
        version = "Unreleased"
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        version = to_tag.lstrip("v")
        # Get tag date
        try:
            date_str = run_git("log", to_tag, "-1", "--format=%aI")[:10]
        except SystemExit:
            date_str = datetime.now().strftime("%Y-%m-%d")

    # Group by category
    grouped: dict[str, list[dict]] = {}
    for c in commits:
        cat = categorize_commit(c)
        # Breaking goes under Changed
        if cat == "Breaking":
            cat = "Changed"
        if cat == MAINTENANCE_LABEL and not include_maintenance:
            continue
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(c)

    # If scope mode, regroup by scope within each category
    if use_scope:
        return _format_with_scopes(version, date_str, grouped)
    else:
        return _format_simple(version, date_str, grouped)


def _format_simple(version: str, date_str: str, grouped: dict) -> str:
    """Format changelog without scope grouping."""
    lines = [f"## [{version}] - {date_str}", ""]

    for cat in CATEGORY_ORDER + [MAINTENANCE_LABEL]:
        if cat not in grouped:
            continue
        lines.append(f"### {cat}")
        for c in grouped[cat]:
            lines.append(format_entry(c))
        lines.append("")

    return "\n".join(lines)


def _format_with_scopes(version: str, date_str: str, grouped: dict) -> str:
    """Format changelog with scope sub-grouping."""
    lines = [f"## [{version}] - {date_str}", ""]

    for cat in CATEGORY_ORDER + [MAINTENANCE_LABEL]:
        if cat not in grouped:
            continue
        lines.append(f"### {cat}")

        # Group by scope within category
        scoped: dict[str | None, list[dict]] = {}
        for c in grouped[cat]:
            scope = extract_scope(c)
            if scope not in scoped:
                scoped[scope] = []
            scoped[scope].append(c)

        for scope, commits in scoped.items():
            if scope:
                lines.append(f"#### {scope}")
            for c in commits:
                lines.append(format_entry(c, use_scope=False))
        lines.append("")

    return "\n".join(lines)


def write_changelog(content: str, output_path: str, append: bool):
    """Write changelog to file."""
    path = Path(output_path)

    if append and path.exists():
        existing = path.read_text(encoding="utf-8")
        # Find insertion point: after header, before first version entry
        header_pattern = re.compile(r"^(#.*changelog.*\n(?:.*\n)*?)(##\s*\[)", re.IGNORECASE | re.MULTILINE)
        m = header_pattern.search(existing)
        if m:
            new_content = existing[: m.start(2)] + content + "\n" + existing[m.start(2) :]
        else:
            new_content = content + "\n\n" + existing
        path.write_text(new_content, encoding="utf-8")
    else:
        header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        path.write_text(header + content, encoding="utf-8")

    print(f"[OK] Changelog written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history."
    )
    parser.add_argument("--from", dest="from_tag", help="Start tag (default: latest tag)")
    parser.add_argument("--to", dest="to_tag", default="HEAD", help="End tag (default: HEAD)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--append", action="store_true", help="Prepend to existing CHANGELOG.md")
    parser.add_argument("--all", action="store_true", help="Include maintenance commits (chore/docs/test)")
    parser.add_argument("--scope", action="store_true", help="Group entries by scope")
    args = parser.parse_args()

    # Resolve from_tag
    from_tag = args.from_tag
    if from_tag is None:
        from_tag = get_latest_tag()
        if from_tag:
            print(f"[INFO] Auto-detected latest tag: {from_tag}")
        else:
            print("[INFO] No tags found, generating full history changelog")

    # Generate
    content = generate_changelog(
        from_tag=from_tag,
        to_tag=args.to_tag,
        use_scope=args.scope,
        include_maintenance=args.all,
    )

    # Write
    write_changelog(content, args.output, args.append)


if __name__ == "__main__":
    main()
