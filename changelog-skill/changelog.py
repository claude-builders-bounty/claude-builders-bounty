#!/usr/bin/env python3
"""
CHANGELOG Generator — Conventional Commits parser with version grouping.

Usage:
    python changelog.py                    # since last tag
    python changelog.py --since v1.0.0     # since specific tag
    python changelog.py --output CHANGELOG.md
    python changelog.py --unreleased       # include uncommitted changes
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Conventional commit types → CHANGELOG sections
TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bug": "Fixed",
    "bugfix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "style": "Changed",
    "chore": "Changed",
    "revert": "Removed",
    "remove": "Removed",
    "rm": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "tests": "Changed",
}

BREAKING_TYPES = {"feat", "fix", "refactor", "perf", "remove", "revert"}

@dataclass
class Commit:
    sha: str
    subject: str
    body: str = ""
    commit_type: str = ""
    scope: str = ""
    breaking: bool = False
    raw: str = ""

@dataclass
class VersionSection:
    version: str
    date: str
    commits: list[Commit] = field(default_factory=list)

def run_git(args: list[str], cwd: Optional[Path] = None) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def parse_conventional(subject: str) -> tuple[str, str, bool, str]:
    """Parse conventional commit subject.
    Returns: (type, scope, breaking, description)"""
    # feat(scope)!: description  or  fix: description
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$", subject.strip())
    if not match:
        return "", "", False, subject.strip()
    ctype, scope, bang, desc = match.groups()
    return ctype.lower(), scope or "", bool(bang), desc.strip()

def get_commits(since: str, until: str = "HEAD", cwd: Optional[Path] = None) -> list[Commit]:
    """Get commits between since..until with full metadata."""
    fmt = "%H%x00%s%x00%b"
    output = run_git(["log", f"{since}..{until}", "--pretty=format:" + fmt, "--no-merges"], cwd=cwd)
    
    commits = []
    for line in output.split("\n"):
        if not line:
            continue
        parts = line.split("\x00", 2)
        if len(parts) < 2:
            continue
        sha, subject = parts[0], parts[1]
        body = parts[2] if len(parts) > 2 else ""
        
        ctype, scope, breaking, desc = parse_conventional(subject)
        commits.append(Commit(
            sha=sha[:8],
            subject=desc,
            body=body.strip(),
            commit_type=ctype,
            scope=scope,
            breaking=breaking,
            raw=f"{sha[:8]} {subject}",
        ))
    return commits

def get_last_tag(cwd: Optional[Path] = None) -> str:
    """Get most recent tag, or empty string if none."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    except SystemExit:
        return ""

def categorize(commit: Commit) -> str:
    """Map commit to CHANGELOG section."""
    if commit.breaking:
        return "Breaking Changes"
    return TYPE_MAP.get(commit.commit_type, "Changed")

def generate_changelog(
    since: str,
    until: str = "HEAD",
    unreleased: bool = False,
    cwd: Optional[Path] = None,
) -> str:
    commits = get_commits(since, until, cwd=cwd)
    
    # Group by category
    sections: dict[str, list[Commit]] = {}
    for c in commits:
        cat = categorize(c)
        sections.setdefault(cat, []).append(c)
    
    # Sort sections: Breaking, Added, Fixed, Changed, Removed, then alphabetical
    order = ["Breaking Changes", "Added", "Fixed", "Changed", "Removed"]
    sorted_sections = []
    for cat in order:
        if cat in sections:
            sorted_sections.append((cat, sections.pop(cat)))
    for cat in sorted(sections.keys()):
        sorted_sections.append((cat, sections[cat]))
    
    # Build output
    lines = ["# Changelog", ""]
    
    version_label = "Unreleased" if unreleased else since or "Unreleased"
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"## [{version_label}] - {date_str}")
    lines.append("")
    
    for cat, cat_commits in sorted_sections:
        lines.append(f"### {cat}")
        lines.append("")
        for c in cat_commits:
            scope_str = f"({c.scope})" if c.scope else ""
            breaking_str = "! " if c.breaking else ""
            lines.append(f"- {breaking_str}{c.commit_type}{scope_str}: {c.subject} (`{c.sha}`)")
        lines.append("")
    
    # Remove trailing empty line
    if lines and lines[-1] == "":
        lines.pop()
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since", help="Generate since tag (default: last tag)")
    parser.add_argument("--until", default="HEAD", help="Generate until ref (default: HEAD)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--unreleased", action="store_true", help="Include uncommitted changes")
    parser.add_argument("--repo-path", help="Repository path (default: current dir)")
    args = parser.parse_args()
    
    cwd = Path(args.repo_path).resolve() if args.repo_path else Path.cwd()
    
    # Determine since tag
    since = args.since
    if not since:
        since = get_last_tag(cwd=cwd)
        if not since:
            # No tags — use first commit
            since = run_git(["rev-list", "--max-parents=0", "HEAD"], cwd=cwd).split("\n")[-1]
    
    changelog = generate_changelog(
        since=since,
        until=args.until,
        unreleased=args.unreleased,
        cwd=cwd,
    )
    
    if args.output:
        Path(args.output).write_text(changelog + "\n")
        print(f"✅ CHANGELOG written to {args.output}")
    else:
        print(changelog)

if __name__ == "__main__":
    main()