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
                r"\bresolve\b", r"\bresolved\b", r"\brepair\b", r"\bcorrect\b",
                r"\bcorrected\b", r"\bworkaround\b"],
    "Changed": [r"\bchange\b", r"\bchanged\b", r"\bupdate\b", r"\bupdated\b",
                r"\brefactor\b", r"\brefactored\b", r"\bimprove\b", r"\bimproved\b",
                r"\bmodify\b", r"\bmodified\b", r"\brename\b", r"\brenamed\b",
                r"\bmove\b", r"\bmoved\b", r"\boptimize\b", r"\boptimized\b",
                r"\benhance\b", r"\benhanced\b", r"\bupgrade\b", r"\bupgraded\b",
                r"\bBump\b", r"\bbump\b"],
    "Removed": [r"\bremove\b", r"\bremoved\b", r"\bdelete\b", r"\bdeleted\b",
                r"\bdrop\b", r"\bdropped\b", r"\bdeprecate\b", r"\bdeprecated\b",
                r"\bcleanup\b", r"\bclean up\b", r"\bstrip\b"],
}


def run_git(args, cwd=None):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True, cwd=cwd, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_last_tag(cwd=None):
    """Get the most recent git tag, or None."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    except RuntimeError:
        return None


def get_commits(since_tag=None, cwd=None):
    """Parse git log into structured dicts."""
    fmt = "%H||%s||%an||%aI"
    args = ["log", f"--pretty=format:{fmt}"]
    if since_tag:
        args.append(f"{since_tag}..HEAD")
    args.append("--no-merges")

    raw = run_git(args, cwd=cwd)
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split("||", 3)
        if len(parts) != 4:
            continue
        sha, subject, author, date_iso = parts
        # short hash
        sha_short = sha[:7]
        # parse date
        try:
            dt = datetime.fromisoformat(date_iso)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = date_iso[:10]
        commits.append({
            "sha": sha_short,
            "subject": subject,
            "author": author,
            "date": date_str,
        })
    return commits


def categorize(subject):
    """Return the category for a commit subject."""
    subj_lower = subject.lower()
    # check conventional commit prefix first: "feat:", "fix:", etc.
    cc_match = re.match(r"^(\w+)(\(.+\))?\!?:", subject)
    if cc_match:
        prefix = cc_match.group(1).lower()
        if prefix in ("feat",):
            return "Added"
        if prefix in ("fix",):
            return "Fixed"
        if prefix in ("refactor", "style", "perf", "build", "ci"):
            return "Changed"
        if prefix in ("chore",):
            return "Changed"
        if prefix in ("revert",):
            return "Removed"

    # keyword matching
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, subj_lower):
                return cat
    return "Changed"  # default


def build_changelog(commits, version=None, since_tag=None):
    """Build markdown changelog text from categorized commits."""
    buckets = defaultdict(list)
    for c in commits:
        cat = categorize(c["subject"])
        buckets[cat].append(c)

    # date header
    today = datetime.now().strftime("%Y-%m-%d")
    version_label = version or since_tag or "Unreleased"

    lines = [f"## [{version_label}] - {today}", ""]

    order = ["Added", "Fixed", "Changed", "Removed"]
    for cat in order:
        items = buckets.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat}")
        for c in items:
            lines.append(f"- {c['subject']} ([{c['sha']}](https://github.com/Qiu-Difeng/claude-builders-bounty/commit/{c['sha']})) — *{c['author']}*")
        lines.append("")

    return "\n".join(lines)


def prepend_to_file(filepath, new_content):
    """Prepend new changelog section to an existing CHANGELOG.md."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()
        # insert before first existing ## header (or at top if none)
        header = "# Changelog\n\n"
        if existing.startswith(header):
            body = existing[len(header):]
            combined = header + new_content + "\n" + body
        elif existing.startswith("# "):
            # find second line group
            idx = existing.find("\n## ")
            if idx >= 0:
                combined = existing[:idx+1] + new_content + "\n" + existing[idx+1:]
            else:
                combined = existing + "\n\n" + new_content
        else:
            combined = header + new_content + "\n" + existing
    else:
        combined = "# Changelog\n\n" + new_content + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(combined)


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured CHANGELOG.md from git history"
    )
    parser.add_argument("--since-tag", help="Only include commits after this tag")
    parser.add_argument("--version", "-v", help="Version label for this release")
    parser.add_argument("--output", "-o", default="CHANGELOG.md",
                        help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to stdout instead of writing file")
    parser.add_argument("--cwd", default=".", help="Git repo path (default: .)")
    args = parser.parse_args()

    since_tag = args.since_tag
    if not since_tag:
        # auto-detect last tag
        last = get_last_tag(cwd=args.cwd)
        if last:
            since_tag = last
            print(f"Auto-detected last tag: {since_tag}")

    commits = get_commits(since_tag=since_tag, cwd=args.cwd)
    if not commits:
        print("No commits found.")
        return

    print(f"Found {len(commits)} commits" +
          (f" since {since_tag}" if since_tag else ""))

    md = build_changelog(commits, version=args.version, since_tag=since_tag)

    if args.dry_run:
        print("\n" + md)
    else:
        prepend_to_file(args.output, md)
        print(f"Changelog written to {args.output}")


if __name__ == "__main__":
    main()
