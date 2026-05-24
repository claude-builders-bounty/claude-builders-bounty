#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py [--tag TAG] [--repo PATH]
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime


def run_git(cmd: list[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        if result.stderr.strip():
            print(f"git warning: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def get_remote_owner_repo(cwd: str) -> str:
    """Extract owner/repo from git remote URL."""
    url = run_git(["remote", "get-url", "origin"], cwd)
    # Handle https:// and git@ formats
    m = re.search(r"(?:github\.com[/:])([\w.-]+/[\w.-]+?)(?:\.git)?$", url)
    return m.group(1) if m else ""


def categorize(subject: str) -> str:
    """Categorize a commit subject into Added/Fixed/Changed/Removed/Other."""
    s = subject.strip().lower()

    # Type prefixes from conventional commits + common patterns
    if re.match(r"^(feat(ure)?|add)(\([^)]+\))?[:\s].*", s) or s.startswith(("add ", "added ")):
        return "Added"
    if re.match(r"^(fix|bugfix|hotfix|patch)(\([^)]+\))?[:\s].*", s) or s.startswith(("fix ", "fixed ")):
        return "Fixed"
    if re.match(r"^(refactor|chore|update|bump|improve|perf|style)(\([^)]+\))?[:\s].*", s) or s.startswith(("update ", "improve ", "bump ", "refactor ")):
        return "Changed"
    if re.match(r"^(remove|deprecate|delete|rm)(\([^)]+\))?[:\s].*", s) or s.startswith(("remove ", "removed ", "delete ", "deprecate ")):
        return "Removed"
    return "Other"


def generate_changelog(repo_path: str, since_tag: str | None = None) -> str:
    """Generate CHANGELOG.md content for the given repo."""
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Error: not a git repository: {repo_path}", file=sys.stderr)
        sys.exit(1)

    # Determine tag range
    tag = since_tag
    if not tag:
        tag = run_git(["describe", "--tags", "--abbrev=0"], repo_path)
        if not tag:
            tag = run_git(["rev-list", "--max-parents=0", "HEAD"], repo_path)
            tag = tag[:12] if tag else ""
            header = "## [Unreleased]\n"
        else:
            header = f"## [Unreleased] (since {tag})\n"
    else:
        header = f"## [Unreleased] (since {tag})\n"

    log_range = f"{tag}..HEAD" if tag else "HEAD"
    commits_raw = run_git(
        ["log", log_range, "--pretty=format:%H||%s||%an||%ad", "--date=short"],
        repo_path,
    )

    owner_repo = get_remote_owner_repo(repo_path)

    # Parse commits into categories
    categories: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}

    if commits_raw:
        for line in commits_raw.split("\n"):
            if not line.strip():
                continue
            parts = line.split("||", 3)
            if len(parts) < 2:
                continue
            hash_val, subject = parts[0], parts[1]

            # Build commit link
            short_hash = hash_val[:7]
            if owner_repo:
                link = f"https://github.com/{owner_repo}/commit/{hash_val}"
                item = f"- {subject} ([{short_hash}]({link}))"
            else:
                item = f"- {subject} ({short_hash})"

            category = categorize(subject)
            categories[category].append(item)

    # Build changelog content
    lines = ["# Changelog\n", header, ""]

    for cat in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        items = categories[cat]
        if items:
            lines.append(f"### {cat}\n")
            lines.extend(f"{item}\n" for item in items)
            lines.append("")

    output = "".join(lines)
    if not output.strip():
        return "# Changelog\n\nNo changes since last release.\n"
    return output


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--tag", help="Start from a specific tag (default: last tag)")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current dir)")
    args = parser.parse_args()

    content = generate_changelog(args.repo, args.tag)
    output_path = os.path.join(args.repo, "CHANGELOG.md")
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Generated CHANGELOG.md ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
