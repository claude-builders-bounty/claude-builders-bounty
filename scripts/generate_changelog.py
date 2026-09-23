#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Collects commits since the last git tag, categorizes them into
Added / Fixed / Changed / Removed based on conventional-commit
keywords in the subject line, and writes a Markdown changelog.

Usage:
    python3 generate_changelog.py [output_file]

If output_file is omitted, defaults to CHANGELOG.md in the current
directory. Requires a git repository with at least one commit.
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(args, cwd=None):
    """Run a git command and return stdout (stripped)."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def find_last_tag(cwd):
    """Return the most recent reachable tag name, or None if none exist."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd)
    except RuntimeError:
        return None


def get_commits_since(tag, cwd):
    """Return a list of commit dicts (sha, date, subject) since `tag`.

    If tag is None, all commits on HEAD are returned.
    """
    if tag:
        rev_range = f"{tag}..HEAD"
    else:
        rev_range = "HEAD"

    # Include merge commits' second-parent range to catch feature branches.
    format = "%H%x09%ad%x09%s"
    raw = run_git(
        ["log", rev_range, f"--pretty=format:{format}", "--no-merges",
         "--date=short", "--all"],
        cwd=cwd,
    )
    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, date, subject = line.split("\t", 2)
        commits.append({"sha": sha, "date": date, "subject": subject})
    return commits


# Mapping of category -> regex patterns matched against the commit subject.
# Order matters: the first matching category wins.
CATEGORY_PATTERNS = {
    "Added": re.compile(
        r"^(feat|feature|add|new|support)\b", re.IGNORECASE
    ),
    "Removed": re.compile(
        r"^(remov|deprecat|delete|drop|breaking)\b", re.IGNORECASE
    ),
    "Fixed": re.compile(
        r"^(fix|bugfix|patch|hotfix)\b", re.IGNORECASE
    ),
    "Changed": re.compile(
        r"^(change|update|refactor|improve|chore|perf|doc|test|style)\b",
        re.IGNORECASE,
    ),
}


def categorize(subject):
    """Return a category name for a commit subject line."""
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.match(subject):
            return category
    return "Changed"


def clean_subject(subject, sha):
    """Strip conventional-commit prefixes and return a readable summary."""
    # Strip leading conventional-commit type (e.g. "feat:", "fix: (auth)")
    cleaned = re.sub(r"^(feat|feature|add|new|support|fix|bugfix|patch|"
                     r"hotfix|remov\w+|deprecat\w+|delete|drop|breaking|"
                     r"change\w*|update\w*|refactor\w*|improve\w*|chore|"
                     r"perf\w*|doc\w*|test\w*|style\w*)\s*\(.*?\)\s*[:!-]\s*",
                     "", subject, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(feat|fix|chore|docs|test|style|refactor|perf|ci|build)\s*[:!-]\s*",
                     "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip() or subject.strip()
    # Title-case for readability
    return cleaned[0].upper() + cleaned[1:]


def build_changelog(commits, tag, version):
    """Return the full Markdown string for the changelog entry."""
    by_category = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for commit in commits:
        category = categorize(commit["subject"])
        entry = clean_subject(commit["subject"], commit["sha"])
        short = commit["sha"][:7]
        by_category[category].append(f"- {entry} (`{short}`)")

    lines = []
    if tag:
        lines.append(f"## {version} ({commits[0]['date']})")
    else:
        lines.append(f"## {version} ({commits[0]['date']})")

    for category in ("Added", "Fixed", "Changed", "Removed"):
        entries = by_category[category]
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.extend(entries)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def prepend_changelog(existing, new_block):
    """Insert the new block after the first H1 in existing, or at top."""
    lines = existing.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[:1]) + "\n\n" + new_block + "\n" + "\n".join(lines[1:]).lstrip("\n")
    return new_block + existing


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("CHANGELOG.md")
    cwd = str(out_path.parent.resolve())

    try:
        run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    except RuntimeError as exc:
        print(f"error: not a git repository ({exc})", file=sys.stderr)
        sys.exit(1)

    tag = find_last_tag(cwd)
    version = tag or datetime.now().strftime("%Y.%m.%d")

    commits = get_commits_since(tag, cwd)
    if not commits:
        print("No new commits since the last tag; nothing to do.")
        return

    block = build_changelog(commits, tag, version)

    existing = out_path.read_text() if out_path.exists() else ""
    if existing:
        content = prepend_changelog(existing, block)
    else:
        content = "# Changelog\n\n" + block

    out_path.write_text(content)
    print(f"Wrote {out_path} with {len(commits)} commit(s) since {tag or 'beginning'}.")


if __name__ == "__main__":
    main()
