#!/usr/bin/env python3
"""
generate-changelog — Generate a structured CHANGELOG.md from git history.

Parses Conventional Commit messages, categorizes them into Added / Fixed /
Changed / Removed sections, and outputs a clean Keep a Changelog-style
CHANGELOG.md.

Usage:
    python changelog.py                   # All commits since last tag
    python changelog.py --since v1.0.0    # Commits since a specific tag
    python changelog.py --since 2025-01-01 --until 2025-06-30  # Date range
    python changelog.py --output CHANGELOG.md                    # Custom output
"""

import argparse
import os
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, date


# ── Conventional Commit prefix → CHANGELOG section mapping ──────────────
# Order controls section appearance in the output.
SECTION_MAP = OrderedDict([
    ("added",     ["feat", "feature", "add"]),
    ("fixed",     ["fix", "bug", "bugfix", "hotfix", "patch"]),
    ("changed",   ["refactor", "perf", "performance", "optimize",
                    "optimization", "update", "upgrade", "deps",
                    "dependencies", "migrate", "migration"]),
    ("removed",   ["remove", "revert", "deprecate", "delete", "drop", "rm"]),
    ("docs",      ["docs", "doc", "documentation"]),
    ("test",      ["test", "tests", "testing"]),
    ("ci",        ["ci", "cd", "devops", "build", "chore"]),
])

# Prefixes that should be skipped entirely (noise).
SKIP_PREFIXES = {"merge", "wip", "initial"}

# Maps section names to their CHANGELOG headings.
SECTION_HEADING = {
    "added":   "Added",
    "fixed":   "Fixed",
    "changed": "Changed",
    "removed": "Removed",
    "docs":    "Documentation",
    "test":    "Tests",
    "ci":      "CI & Build",
}


# ── Helpers ─────────────────────────────────────────────────────────────

def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, check=True,
            cwd=cwd,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git {args[0]}: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def _parse_commit_log(raw: str) -> list[dict]:
    """Parse ``git log --format`` output into structured commit dicts."""
    commits = []
    for block in raw.strip().split("\n\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        if len(lines) < 1:
            continue

        # First line: hash|author|date|subject
        meta = lines[0].split("|", 4)
        if len(meta) < 4:
            continue

        commit = {
            "hash": meta[0][:8],
            "author": meta[1] if len(meta) > 1 else "",
            "date": meta[2] if len(meta) > 2 else "",
            "subject": meta[3] if len(meta) > 3 else "",
            "body": "\n".join(lines[1:]).strip() if len(lines) > 1 else "",
        }
        commits.append(commit)
    return commits


def _categorize(subject: str) -> tuple[str, str, bool]:
    """
    Given a commit subject, return (section_key, clean_message, is_breaking).

    Determines the section (added/fixed/changed/removed/docs/test/ci) and
    strips the conventional-commit prefix from the message.
    """
    subject = subject.strip()

    # Detect breaking change indicator: "feat!: ..." or "feat(scope)!: ..."
    # Also detect "BREAKING CHANGE:" at the start of the subject.
    # We handle the latter in the body; here we check the prefix.
    is_breaking = False
    bare = subject

    # Pattern: prefix[(scope)][!]:  message
    m = re.match(
        r"^(\w+)"                # prefix (feat, fix, …)
        r"(?:\([^)]*\))?"        # optional (scope)
        r"(!)?\s*:\s*"           # optional ! then colon-space
        r"(.*)$",                # the actual message
        subject,
        re.IGNORECASE,
    )
    if m:
        prefix = m.group(1).lower()
        is_breaking = bool(m.group(2))
        message = m.group(3).strip()
    else:
        # No conventional-commit prefix — leave as-is, category "changed"
        return "changed", subject, False

    # Check skip list
    if prefix in SKIP_PREFIXES:
        return "skip", message or subject, is_breaking

    # Map prefix → section
    for section, prefixes in SECTION_MAP.items():
        if prefix in prefixes:
            return section, message or subject, is_breaking

    # Unrecognized prefix: treat as changed
    return "changed", message or subject, is_breaking


def _detect_breaking_in_body(body: str) -> bool:
    """Check if the commit body contains a ``BREAKING CHANGE`` footer."""
    if not body:
        return False
    # Common patterns: "BREAKING CHANGE: ..." or "BREAKING-CHANGE: ..."
    return bool(re.search(r"BREAKING[-\s]CHANGE\s*:", body, re.IGNORECASE))


def _format_message(subject: str, body: str, hash_: str, is_breaking: bool) -> str:
    """Format a single changelog entry."""
    entry = f"- {subject}"
    if is_breaking:
        entry = f"- **BREAKING**: {subject}"
    # Optionally append hash
    # entry += f" ({hash_})"
    # Include body (first paragraph only, truncated)
    if body:
        para = body.split("\n\n")[0].strip()
        # Remove BREAKING CHANGE footer from body preview
        para = re.sub(r"BREAKING[-\s]CHANGE:.*", "", para).strip()
        if para:
            # Indent body as a continuation paragraph
            entry += f"\n  {para}"
    return entry


def get_last_tag(cwd: str | None = None) -> str | None:
    """Return the most recent tag reachable from HEAD."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "HEAD"],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_commits(
    since: str | None = None,
    until: str | None = None,
    cwd: str | None = None,
) -> list[dict]:
    """
    Fetch commits, optionally filtered by tag or date range.

    If *since* is a date (YYYY-MM-DD), uses ``--since`` / ``--after``.
    If *since* is a tag name, uses ``tag..HEAD``.
    If *since* is None, tries the last tag; falls back to the last 100 commits.
    """
    # Resolve 'since'
    if since is None:
        last_tag = get_last_tag(cwd)
        if last_tag:
            since_ref = last_tag
            since_desc = f"tag {last_tag}"
        else:
            # Check how many commits exist
            try:
                count_result = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    capture_output=True, text=True, cwd=cwd,
                )
                commit_count = int(count_result.stdout.strip())
            except Exception:
                commit_count = 0
            if commit_count == 0:
                print("No commits found in this repository.", file=sys.stderr)
                return []
            since_ref = f"HEAD~{min(commit_count, 100)}"
            since_desc = f"last {min(commit_count, 100)} commits"
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", since):
        since_ref = since
        since_desc = since
    elif re.match(r"^HEAD~?\d*$", since):
        # Git ref like HEAD~20 — use directly
        since_ref = since
        since_desc = since
    else:
        # Check if it's a valid tag
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", f"refs/tags/{since}"],
                capture_output=True, check=True, cwd=cwd,
            )
            since_ref = since
            since_desc = f"tag {since}"
        except subprocess.CalledProcessError:
            # Not a tag — treat as git revision
            since_ref = since
            since_desc = since

    # Build git log args
    # We use a separator that won't appear in real commit messages.
    if until:
        log_spec = f"{since_ref}..{until}" if not re.match(r"^\d{4}", since_ref) else f"--after={since_ref} --before={until}"
    else:
        log_spec = f"{since_ref}..HEAD" if not re.match(r"^\d{4}", since_ref) else f"--after={since_ref}"

    # Handle empty repos before running git log
    try:
        count_check = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, cwd=cwd,
        )
        if int(count_check.stdout.strip()) == 0:
            print("No commits found in this repository.", file=sys.stderr)
            return []
    except Exception:
        pass

    # Produce hash|author|date|subject\nbody\n\n\n (triple-newline separator)
    fmt = "--format=%h|%an|%ad|%s%n%b%n%n%n"
    
    args = ["log", "--no-merges"]

    if re.match(r"^\d{4}", since_ref):
        args.append(f"--after={since_ref}")
        if until:
            args.append(f"--before={until}")
    else:
        args.append(log_spec)

    args.extend([fmt, "--date=short"])

    raw = _run_git(args, cwd=cwd)
    commits = _parse_commit_log(raw)

    if not commits:
        print(f"No commits found since {since_desc}.", file=sys.stderr)
        return []

    print(f"Found {len(commits)} commit(s) since {since_desc}.", file=sys.stderr)
    return commits


def build_changelog(
    commits: list[dict],
    version: str = "Unreleased",
    date_str: str | None = None,
) -> str:
    """
    Build a CHANGELOG.md string from a list of commit dicts.

    *version* is the heading version string (e.g. "1.2.3" or "Unreleased").
    *date_str* is the optional release date (ISO format). If None and
    version != "Unreleased", today's date is used.
    """
    # Categorize commits
    sections: dict[str, list[str]] = defaultdict(list)
    breaking_entries: list[str] = []

    for c in commits:
        section, message, is_breaking_prefix = _categorize(c["subject"])
        if section == "skip":
            continue

        is_breaking_body = _detect_breaking_in_body(c["body"])
        is_breaking = is_breaking_prefix or is_breaking_body

        entry = _format_message(message, c["body"], c["hash"], is_breaking)
        if is_breaking:
            breaking_entries.append(entry)
        else:
            sections[section].append(entry)

    # Build the markdown
    lines: list[str] = []
    lines.append("# Changelog")

    if date_str is None and version.lower() != "unreleased":
        date_str = date.today().isoformat()

    heading = f"## {version}"
    if date_str:
        heading += f" — {date_str}"
    lines.append("")
    lines.append(heading)
    lines.append("")

    # Breaking changes first (standalone section)
    if breaking_entries:
        lines.append("### ⚠ Breaking Changes")
        lines.append("")
        lines.extend(breaking_entries)
        lines.append("")

    # Regular sections in order
    for section_key in ["added", "fixed", "changed", "removed", "docs", "test", "ci"]:
        entries = sections.get(section_key)
        if not entries:
            continue
        heading_text = SECTION_HEADING.get(section_key, section_key.capitalize())
        lines.append(f"### {heading_text}")
        lines.append("")
        lines.extend(entries)
        lines.append("")

    # If nothing was generated
    if not breaking_entries and not any(sections.values()):
        lines.append("_No notable changes._")
        lines.append("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.",
    )
    parser.add_argument(
        "--since", "-s",
        default=None,
        help="Tag name or ISO date (YYYY-MM-DD). Default: last git tag.",
    )
    parser.add_argument(
        "--until", "-u",
        default=None,
        help="End date (YYYY-MM-DD) for date-range filtering. Requires --since as date.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path. Default: print to stdout.",
    )
    parser.add_argument(
        "--version", "-v",
        default="Unreleased",
        help="Version string for the changelog heading (default: Unreleased).",
    )
    parser.add_argument(
        "--repo", "-r",
        default=None,
        help="Path to the git repository (default: current directory).",
    )
    parser.add_argument(
        "--date", "-d",
        default=None,
        help="Release date (YYYY-MM-DD). Default: today for versioned, none for Unreleased.",
    )
    args = parser.parse_args()

    # Resolve repo path
    repo_path = os.path.abspath(args.repo) if args.repo else os.getcwd()

    # Fetch commits
    commits = get_commits(since=args.since, until=args.until, cwd=repo_path)
    if not commits:
        sys.exit(0)

    # Build changelog
    changelog = build_changelog(commits, version=args.version, date_str=args.date)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog)
            f.write("\n")
        print(f"CHANGELOG written to {args.output}")
    else:
        print(changelog)


if __name__ == "__main__":
    main()
