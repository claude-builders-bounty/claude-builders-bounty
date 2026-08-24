#!/usr/bin/env python3
"""
generate-changelog — Structured CHANGELOG.md from git history.

Supports Conventional Commits, natural language heuristics, and conventional
prefixes. Zero external dependencies beyond Python 3.7+ and git.

Usage:
    python3 changelog.py                 # Write CHANGELOG.md
    python3 changelog.py --dry-run       # Preview to stdout
    python3 changelog.py --since v1.0.0  # Since a specific tag/commit
    python3 changelog.py --output HISTORY.md  # Custom output file
    python3 changelog.py --version 2.1.0  # Override version header
"""

import subprocess
import sys
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path


# ── Category definitions ──────────────────────────────────────────────────────

CATEGORIES = [
    ("Added", ["feat", "add", "new", "implement", "create", "introduce", "support"]),
    ("Fixed", ["fix", "bug", "patch", "hotfix", "correct", "resolve", "repair"]),
    ("Changed", ["refactor", "perf", "improve", "update", "upgrade", "change",
                 "style", "chore", "docs", "ci", "build", "test", "optimize",
                 "migrate", "rename", "restructure"]),
    ("Removed", ["remove", "delete", "drop", "deprecate", "revert", "strip"]),
    ("Security", ["security", "vuln", "cve", "xss", "injection", "csrf", "sanitize"]),
]


# ── Git helpers ───────────────────────────────────────────────────────────────

def git(*args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_latest_tag() -> str:
    """Get the most recent git tag, or empty string."""
    return git("describe", "--tags", "--abbrev=0")


def detect_version() -> str:
    """Auto-detect version from package.json, pyproject.toml, Cargo.toml, or date."""
    # package.json
    pj = Path("package.json")
    if pj.exists():
        import json
        try:
            data = json.loads(pj.read_text())
            v = data.get("version", "")
            if v:
                return v
        except Exception:
            pass

    # pyproject.toml
    pp = Path("pyproject.toml")
    if pp.exists():
        m = re.search(r'version\s*=\s*["\']([^"\']+)', pp.read_text())
        if m:
            return m.group(1)

    # Cargo.toml
    ct = Path("Cargo.toml")
    if ct.exists():
        m = re.search(r'^version\s*=\s*"([^"]+)"', ct.read_text(), re.MULTILINE)
        if m:
            return m.group(1)

    # setup.py
    sp = Path("setup.py")
    if sp.exists():
        m = re.search(r'version\s*=\s*["\']([^"\']+)', sp.read_text())
        if m:
            return m.group(1)

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_commits(since: str = "") -> list:
    """Fetch commits as list of (hash, subject, author, date) tuples."""
    args = ["log", "--pretty=format:%H|%s|%an|%aI", "--no-merges"]
    if since:
        args += [f"{since}..HEAD"]
    output = git(*args)
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        h, subject, author, date = parts
        if not subject.strip():
            continue
        commits.append((h, subject.strip(), author, date))
    return commits


# ── Classification ────────────────────────────────────────────────────────────

def classify(subject: str) -> str:
    """Classify a commit subject into a category."""
    lower = subject.lower().strip()

    # Check for BREAKING CHANGE marker (! or "breaking change")
    if "breaking change" in lower or re.match(r'^\w+(\(.+\))?!:', lower):
        return "Changed"

    # Strip conventional commit scope: feat(api): → feat:
    clean = re.sub(r'^(\w+)(\([^)]*\))?!?:', r'\1:', lower)
    prefix = clean.split(":")[0].split(" ")[0] if ":" in clean else clean.split(" ")[0]

    for category, keywords in CATEGORIES:
        if prefix.rstrip(":") in keywords:
            return category
        # Also check full subject for keyword starts
        for kw in keywords:
            if lower.startswith(kw + ":") or lower.startswith(kw + "(") or lower.startswith(kw + " "):
                return category

    return "Changed"  # Default: put uncategorized in Changed


def format_changelog(commits: list, version: str, since: str = "") -> str:
    """Build the CHANGELOG.md content string."""
    grouped = {}
    for _, subject, author, date in commits:
        cat = classify(subject)
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append((subject, author, date))

    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append(f"## [{version}] — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    if since:
        lines.append(f"_Changes since `{since}`_")
    lines.append("")

    # Only include categories that have entries
    for cat, _ in CATEGORIES:
        entries = grouped.get(cat, [])
        if not entries:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        for subject, author, date in entries:
            lines.append(f"- {subject} ({author})")
        lines.append("")

    if not commits:
        lines.append("_No changes detected._")
        lines.append("")

    total = len(commits)
    lines.append(f"---")
    lines.append(f"*{total} commit{'s' if total != 1 else ''} in this release.*")
    lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 changelog.py                    # Write CHANGELOG.md
  python3 changelog.py --dry-run          # Preview to stdout
  python3 changelog.py --since v1.0.0     # Since a specific tag
  python3 changelog.py --output HISTORY.md # Custom output file
  python3 changelog.py --version 2.1.0    # Override version header
""",
    )
    parser.add_argument("--since", default="", help="Tag or commit hash to start from")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--version", default="", help="Version string for header (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    # Determine range
    since = args.since
    if not since:
        since = get_latest_tag()
    if since:
        print(f"Using latest tag as baseline: {since}", file=sys.stderr)
    else:
        print("No tags found — using full history", file=sys.stderr)

    # Detect version
    version = args.version or detect_version()

    # Fetch commits
    commits = get_commits(since)

    if not commits:
        print("No commits found in range. Generating empty changelog entry.", file=sys.stderr)
    else:
        print(f"Found {len(commits)} commits", file=sys.stderr)

    # Generate
    content = format_changelog(commits, version, since)

    if args.dry_run:
        print(content)
    else:
        Path(args.output).write_text(content)
        print(f"Wrote {args.output} ({len(content)} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
