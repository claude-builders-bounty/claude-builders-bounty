#!/usr/bin/env python3
"""
Auto-generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py                  # all commits
    python generate_changelog.py --since-tag v1.0 # commits since v1.0
    python generate_changelog.py --output RELEASE_NOTES.md

Requires: git CLI in PATH
"""

import subprocess
import re
import argparse
import os
from datetime import datetime
from collections import defaultdict

# ── commit categorization rules ──────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Added":   [r"\badd\b", r"\badded\b", r"\bnew\b", r"\bcreate\b", r"\bcreated\b",
                r"\binit\b", r"\bintroduce\b", r"\bsupport\b", r"\bimplement\b",
                r"\bfeat\b", r"\bfeature\b"],
    "Fixed":   [r"\bfix\b", r"\bfixed\b", r"\bfixes\b", r"\bbug\b", r"\bpatch\b",
                r"\bhotfix\b", r"\bresolve\b", r"\bresolved\b", r"\brepair\b"],
    "Changed": [r"\bupdate\b", r"\bupdated\b", r"\bchange\b", r"\bchanged\b",
                r"\bmodify\b", r"\bmodified\b", r"\brefactor\b", r"\brefactored\b",
                r"\bmove\b", r"\brename\b", r"\bimprove\b", r"\bimproved\b"],
    "Removed": [r"\bremove\b", r"\bremoved\b", r"\bdelete\b", r"\bdeleted\b",
                r"\bdeprecate\b", r"\bdeprecated\b", r"\bdrop\b", r"\bdropped\b"],
    "Docs":    [r"\bdoc\b", r"\bdocs\b", r"\breadme\b", r"\bcomment\b", r"\bchangelog\b"],
    "Test":    [r"\btest\b", r"\btests\b", r"\bspec\b", r"\bci\b", r"\bcoverage\b"],
}

# Conventional Commits prefix mapping (e.g. "feat: ..." -> Added)
CONVENTIONAL_MAP = {
    "feat": "Added", "fix": "Fixed", "docs": "Docs", "style": "Changed",
    "refactor": "Changed", "perf": "Changed", "test": "Test",
    "build": "Changed", "ci": "Test", "chore": "Changed",
}


def get_commits(since_tag=None):
    """Parse git log using unit/record separators for robust field splitting."""
    # Use non-printable delimiters to avoid collision with commit messages
    sep = "%x1f"   # unit separator between fields
    rec = "%x1e"   # record separator between commits
    fmt = f"{sep}%H{sep}%h{sep}%s{sep}%an{sep}%ai{rec}"

    cmd = ["git", "log", f"--format={fmt}"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"git log error: {result.stderr.strip()}")
        return []

    output = result.stdout
    if not output.strip():
        return []

    commits = []
    records = output.split("\x1e")

    for rec_text in records:
        rec_text = rec_text.strip()
        if not rec_text:
            continue
        fields = rec_text.split("\x1f")
        if len(fields) < 6:
            continue
        # fields[0] is empty (before first separator)
        sha_full = fields[1].strip()
        sha_short = fields[2].strip()
        subject = fields[3].strip()
        author = fields[4].strip()
        date = fields[5].strip()[:10]  # YYYY-MM-DD

        commits.append({
            "sha": sha_full,
            "sha_short": sha_short,
            "subject": subject,
            "author": author,
            "date": date,
        })

    return commits


def categorize(subject):
    """Assign a changelog category to a commit subject."""
    # Check Conventional Commits first (e.g. "feat: add login")
    cc_match = re.match(r'^(\w+)(?:\(.+?\))?:\s*', subject)
    if cc_match:
        prefix = cc_match.group(1).lower()
        if prefix in CONVENTIONAL_MAP:
            return CONVENTIONAL_MAP[prefix]

    # Fall back to keyword matching
    lower = subject.lower()
    for category, patterns in CATEGORY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, lower):
                return category
    return "Changed"


def get_repo_url():
    """Derive the repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Handle SSH URLs (git@github.com:user/repo.git)
            m = re.match(r'git@([^:]+):(.+?)(?:\.git)?$', url)
            if m:
                return f"https://{m.group(1)}/{m.group(2)}"
            # Handle HTTPS URLs
            m = re.match(r'https?://(.+?)(?:\.git)?$', url)
            if m:
                return f"https://{m.group(1)}"
    except Exception:
        pass
    return None


def build_changelog(commits, version=None, repo_url=None):
    """Build markdown changelog string from categorized commits."""
    if not commits:
        return "No commits found for this range.\n"

    grouped = defaultdict(list)
    for c in commits:
        cat = categorize(c["subject"])
        grouped[cat].append(c)

    label = version or datetime.now().strftime("%Y-%m-%d")
    lines = [f"## {label}\n"]

    for cat in ["Added", "Changed", "Fixed", "Removed", "Docs", "Test"]:
        items = grouped.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat}\n")
        for c in items:
            sha = c["sha"]
            short = c["sha_short"]
            if repo_url:
                link = f"[{short}]({repo_url}/commit/{sha})"
            else:
                link = short
            lines.append(f"- {c['subject']} — {link} ({c['author']}, {c['date']})")
        lines.append("")

    return "\n".join(lines)


def prepend_changelog(new_text, filepath):
    """Insert new changelog entry after the header, handling varied line endings."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            existing = f.read()
    else:
        existing = "# Changelog\n\n"

    # Normalize line endings for reliable parsing
    norm = existing.replace("\r\n", "\n")
    header = "# Changelog\n\n"
    if norm.startswith("# Changelog"):
        # Find end of header section (first ## or end of content)
        rest = norm[len(header):] if norm.startswith(header) else norm.split("\n\n", 1)[-1]
        result = header + new_text + "\n" + rest
    else:
        result = header + new_text + "\n" + norm

    with open(filepath, "w", newline="\n") as f:
        f.write(result)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since-tag", help="Only include commits after this tag")
    parser.add_argument("--version", "-v", help="Version label for the section header")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of file")
    args = parser.parse_args()

    commits = get_commits(since_tag=args.since_tag)
    print(f"Found {len(commits)} commits")

    repo_url = get_repo_url()
    changelog = build_changelog(commits, version=args.version, repo_url=repo_url)

    if args.dry_run:
        print(changelog)
    else:
        prepend_changelog(changelog, args.output)
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
