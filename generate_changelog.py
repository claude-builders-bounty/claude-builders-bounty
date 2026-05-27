#!/usr/bin/env python3
"""
Auto-generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py                  # all commits
    python generate_changelog.py --since-tag v1.0 # commits since v1.0
    python generate_changelog.py --output RELEASE_NOTES.md
    python generate_changelog.py --repo-url https://github.com/owner/repo

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
                r"\bbump\b"],
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


def get_remote_url(cwd=None):
    """Auto-detect the GitHub repo URL from git remote."""
    try:
        url = run_git(["config", "--get", "remote.origin.url"], cwd=cwd)
        # Handle SSH URLs: git@github.com:owner/repo.git
        match = re.match(r'git@github\.com:([^/]+/[^/]+?)(?:\.git)?$', url)
        if match:
            return f"https://github.com/{match.group(1)}"
        # Handle HTTPS URLs: https://github.com/owner/repo.git
        match = re.match(r'https://github\.com/([^/]+/[^/]+?)(?:\.git)?$', url)
        if match:
            return f"https://github.com/{match.group(1)}"
    except RuntimeError:
        pass
    return None


def get_last_tag(cwd=None):
    """Get the most recent git tag, or None."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    except RuntimeError:
        return None


def get_commits(since_tag=None, cwd=None):
    """Parse git log into structured dicts.
    
    Uses %x1f (unit separator) as field delimiter to avoid collisions
    with commit message content.
    """
    # Use ASCII unit separator (\x1f) as delimiter — extremely unlikely
    # to appear in commit subjects
    fmt = "%H%x1f%s%x1f%an%x1f%aI"
    args = ["log", f"--pretty=format:{fmt}"]
    if since_tag:
        args.append(f"{since_tag}..HEAD")
    args.append("--no-merges")

    raw = run_git(args, cwd=cwd)
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split("\x1f", 3)
        if len(parts) != 4:
            continue
        sha_full, subject, author, date_iso = parts
        # Keep full SHA for link generation, use short SHA for display
        sha_short = sha_full[:7]
        # parse date
        try:
            dt = datetime.fromisoformat(date_iso)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = date_iso[:10]
        commits.append({
            "sha": sha_short,
            "sha_full": sha_full,
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


def build_changelog(commits, version=None, since_tag=None, repo_url=None):
    """Build markdown changelog text from categorized commits."""
    buckets = defaultdict(list)
    for c in commits:
        cat = categorize(c["subject"])
        buckets[cat].append(c)

    # date header
    today = datetime.now().strftime("%Y-%m-%d")
    version_label = version or since_tag or "Unreleased"

    lines = [f"## [{version_label}] - {today}", ""]

    # Build commit link using full SHA for reliability
    def commit_link(c):
        sha_display = c["sha"]
        sha_target = c["sha_full"]
        if repo_url:
            return f"[{sha_display}]({repo_url}/commit/{sha_target})"
        return sha_display

    order = ["Added", "Fixed", "Changed", "Removed"]
    for cat in order:
        items = buckets.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat}")
        for c in items:
            lines.append(
                f"- {c['subject']} ({commit_link(c)} by *{c['author']}* on {c['date']})"
            )
        lines.append("")

    return "\n".join(lines)


def prepend_to_file(filepath, new_content):
    """Prepend new changelog section to an existing CHANGELOG.md.
    
    Handles various header formats:
    - Windows line endings (\\r\\n)
    - Single or multiple newlines after title
    - Extra whitespace
    """
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()

        # Normalize line endings for processing
        existing_norm = existing.replace("\r\n", "\n")

        # Match the changelog header flexibly: "# Changelog" followed by whitespace
        header_match = re.match(r'#[ \t]+[Cc]hangelog\s*\n', existing_norm)

        if header_match:
            header_end = header_match.end()
            body = existing_norm[header_end:]
            combined = existing_norm[:header_end] + new_content + "\n" + body
        elif existing_norm.startswith("# "):
            # find second ## header
            idx = existing_norm.find("\n## ")
            if idx >= 0:
                combined = existing_norm[:idx + 1] + new_content + "\n" + existing_norm[idx + 1:]
            else:
                combined = existing_norm + "\n\n" + new_content
        else:
            combined = "# Changelog\n\n" + new_content + "\n" + existing
    else:
        combined = "# Changelog\n\n" + new_content + "\n"

    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
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
    parser.add_argument("--repo-url",
                        help="Base URL for commit links (default: auto-detect from git remote)")
    args = parser.parse_args()

    # Auto-detect repo URL if not provided
    repo_url = args.repo_url
    if not repo_url:
        repo_url = get_remote_url(cwd=args.cwd)
        if repo_url:
            print(f"Auto-detected repo URL: {repo_url}")

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

    md = build_changelog(commits, version=args.version, since_tag=since_tag,
                         repo_url=repo_url)

    if args.dry_run:
        print("\n" + md)
    else:
        prepend_to_file(args.output, md)
        print(f"Changelog written to {args.output}")


if __name__ == "__main__":
    main()
