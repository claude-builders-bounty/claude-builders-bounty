#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py                 # Output to CHANGELOG.md
    python changelog.py --stdout        # Print to stdout
    python changelog.py --repo /path    # Use a different repo path
    python changelog.py --since v1.0.0  # Specify starting tag
"""

import subprocess
import re
import os
import sys
from datetime import datetime


def run_git(cmd, cwd=None):
    """Run a git command and return output. Exits on failure."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd or os.getcwd(),
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else "unknown error"
        print(f"Git error ({' '.join(cmd)}): {err_msg}", file=sys.stderr)
        sys.exit(1)


def get_last_tag(cwd=None):
    """Get the most recent git tag. Returns None if no tags found."""
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=cwd or os.getcwd(),
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def get_commits_since(since=None, cwd=None):
    """Get commits since a given ref, or all commits if no ref."""
    log_range = f"{since}..HEAD" if since else "HEAD"
    fmt = "--format=---COMMIT---%n%H%n%an%n%ai%n%s%n%b"
    raw = run_git(["log", fmt, log_range], cwd=cwd)

    commits = []
    blocks = raw.split("---COMMIT---\n")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 4)
        if len(lines) < 4:
            continue
        sha, author, date_str, subject = lines[0], lines[1], lines[2], lines[3]
        body = lines[4] if len(lines) > 4 else ""
        commits.append({
            "sha": sha[:7],
            "author": author,
            "date": date_str,
            "subject": subject,
            "body": body.strip(),
        })
    return commits


TYPE_MAP = {
    "feat": "Added", "feature": "Added", "add": "Added", "new": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "bug": "Fixed", "hotfix": "Fixed",
    "change": "Changed", "changed": "Changed", "update": "Changed",
    "refactor": "Changed", "perf": "Changed", "improve": "Changed",
    "deprecate": "Deprecated", "deprecated": "Deprecated",
    "remove": "Removed", "removed": "Removed", "delete": "Removed",
    "security": "Fixed", "docs": "Changed", "doc": "Changed",
    "chore": "Changed", "style": "Changed", "test": "Changed",
    "ci": "Changed", "build": "Changed",
}
FALLBACK_SECTION = "Changed"


def categorize(subject, body):
    """Categorize a commit into a changelog section."""
    full_msg = f"{subject}\n{body}".lower()
    m = re.match(r"^(\w+)(?:\(.*?\))?[!:]", subject)
    if m:
        pfx = m.group(1).lower()
        if pfx in TYPE_MAP:
            return TYPE_MAP[pfx]
    kw_map = {
        "Added": r"\b(add|new|feature|implement|introduce|create|support)\b",
        "Fixed": r"\b(fix|bug|hotfix|patch|repair|correct|resolve|crash|error|broken)\b",
        "Removed": r"\b(remove|delete|deprecat|drop|eliminate|strip)\b",
        "Changed": r"\b(update|change|refactor|improve|migrate|redesign|rework)\b",
    }
    for section, pattern in kw_map.items():
        if re.search(pattern, full_msg):
            return section
    return FALLBACK_SECTION


def build_changelog(commits, version=None, date=None):
    """Build a CHANGELOG.md string from categorized commits."""
    order = ["Added", "Fixed", "Changed", "Deprecated", "Removed", "Security"]
    sections = {k: [] for k in order}
    uncategorized = []

    for c in commits:
        section = categorize(c["subject"], c["body"])
        entry = f"- {c['subject']}"
        if c["sha"]:
            entry += f" ([{c['sha']}](https://github.com/example/commit/{c['sha']}))"
        if section in sections:
            sections[section].append(entry)
        else:
            uncategorized.append(entry)

    ver = version or "Unreleased"
    d = date or datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Changelog\n", f"## [{ver}] - {d}\n"]

    has = False
    for s in order:
        if sections[s]:
            lines.append(f"### {s}\n")
            lines.extend(x + "\n" for x in sections[s])
            lines.append("")
            has = True
    if uncategorized:
        lines.append("### Other\n")
        lines.extend(x + "\n" for x in uncategorized)
        lines.append("")
        has = True
    if not has:
        lines.append("_No notable changes._\n")
    return "\n".join(lines)


def parse_args():
    args = {}
    i = 0
    while i < len(sys.argv[1:]):
        arg = sys.argv[1:][i]
        if arg == "--stdout":
            args["stdout"] = True
        elif arg == "--repo" and i + 1 < len(sys.argv[1:]):
            args["repo"] = sys.argv[1:][i + 1]
            i += 1
        elif arg == "--since" and i + 1 < len(sys.argv[1:]):
            args["since"] = sys.argv[1:][i + 1]
            i += 1
        elif arg in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        i += 1
    return args


def main():
    args = parse_args()
    cwd = args.get("repo")

    run_git(["rev-parse", "--git-dir"], cwd=cwd)

    since = args.get("since") or get_last_tag(cwd=cwd)
    if not since:
        since = None

    # Get repo name from remote for link replacement
    repo_name = ""
    try:
        r = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, cwd=cwd or os.getcwd(),
        )
        if r.returncode == 0:
            url = r.stdout.strip()
            m = re.search(r"[:/]([^/]+/[^/.]+)(?:\.git)?$", url)
            if m:
                repo_name = m.group(1)
    except Exception:
        pass

    commits = get_commits_since(since, cwd=cwd)
    if not commits:
        print("No new commits found.", file=sys.stderr)
        sys.exit(0)

    version = since or "Unreleased"
    changelog = build_changelog(commits, version=version)

    if repo_name:
        changelog = changelog.replace(
            "https://github.com/example/",
            f"https://github.com/{repo_name}/",
        )

    if args.get("stdout"):
        print(changelog)
    else:
        out = os.path.join(cwd or os.getcwd(), "CHANGELOG.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(changelog)
        print(f"✓ CHANGELOG.md generated at {out}")
        print(f"  {len(commits)} commits categorized since {version}")


if __name__ == "__main__":
    main()
