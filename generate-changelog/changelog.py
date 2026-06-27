#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from local git history or GitHub API.

Usage:
  python changelog.py                    # since last tag, writes CHANGELOG.md
  python changelog.py --output -         # stdout
  python changelog.py --since v1.2.0    # from specific tag
  python changelog.py --days 7          # last 7 days
  python changelog.py --dry-run         # preview, no file written
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import date
from typing import Any


# ---------------------------------------------------------------------------
# Conventional commit / label classification
# ---------------------------------------------------------------------------

_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Added",   ["feat", "feature", "add", "new", "enhancement"]),
    ("Fixed",   ["fix", "bug", "bugfix", "hotfix", "patch"]),
    ("Changed", ["refactor", "perf", "style", "chore", "change", "improve", "update", "ci"]),
    ("Removed", ["remove", "delete", "deprecate", "drop", "breaking"]),
    ("Docs",    ["docs", "doc", "documentation", "readme"]),
]
_CATCHALL = "Changed"


def _categorize(title: str, labels: list[str] | None = None) -> str:
    """Map a commit/PR title (and optional labels) to a CHANGELOG category."""
    # Try labels first
    if labels:
        for cat, keys in _CATEGORY_RULES:
            if any(k in " ".join(labels).lower() for k in keys):
                return cat

    # Try conventional commit prefix
    m = re.match(r"^(\w[\w-]*)(?:\(.*?\))?!?\s*:", title.strip())
    if m:
        prefix = m.group(1).lower()
        for cat, keys in _CATEGORY_RULES:
            if prefix in keys:
                return cat

    # Keyword scan — only first 3 words to avoid false positives on descriptions
    first_words = " ".join(title.lower().split()[:3])
    for cat, keys in _CATEGORY_RULES:
        if any(k in first_words for k in keys):
            return cat

    return _CATCHALL


def _clean_title(title: str) -> str:
    """Strip conventional commit prefix from title."""
    return re.sub(r"^[\w-]+(?:\(.*?\))?!?\s*:\s*", "", title.strip(), count=1)


# ---------------------------------------------------------------------------
# Local git backend (no auth needed)
# ---------------------------------------------------------------------------

class GitError(RuntimeError):
    pass


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise GitError(exc.stderr.strip()) from exc


def git_last_tag() -> str | None:
    """Return the most recent tag reachable from HEAD, or None if no tags."""
    try:
        return _git("describe", "--tags", "--abbrev=0")
    except GitError:
        return None


def git_commits_since(ref: str | None = None, days: int | None = None) -> list[dict]:
    """
    Return list of {sha, title, body} dicts.
    If ref is None and days is None, returns all commits in the repo.
    """
    cmd = ["log", "--pretty=format:%H\x1f%s\x1f%b\x1e"]
    if ref:
        cmd.append(f"{ref}..HEAD")
    elif days:
        cmd += [f"--since={days} days ago"]
    raw = _git(*cmd)
    commits = []
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f", 2)
        sha, title = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        body = parts[2].strip() if len(parts) > 2 else ""
        if sha and title:
            commits.append({"sha": sha[:7], "title": title, "body": body})
    return commits


def git_repo_name() -> str:
    """Extract repo name from remote URL or directory name."""
    try:
        remote = _git("remote", "get-url", "origin")
        m = re.search(r"[/:]([^/]+/[^/]+?)(?:\.git)?$", remote)
        if m:
            return m.group(1)
    except GitError:
        pass
    return os.path.basename(os.getcwd())


# ---------------------------------------------------------------------------
# Optional GitHub API backend (richer: PR labels, authors)
# ---------------------------------------------------------------------------

class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN")

    def _get(self, path: str) -> Any:
        req = urllib.request.Request(
            f"{self.BASE}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Authorization": f"Bearer {self._token}"} if self._token else {}),
                "User-Agent": "changelog-gen/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub API {exc.code}: {exc.read()[:200]}") from exc

    def get_tags(self, full_name: str) -> list[dict]:
        return self._get(f"/repos/{full_name}/tags?per_page=5")

    def get_pulls(self, full_name: str, since_sha: str | None = None, days: int | None = None) -> list[dict]:
        pulls = []
        for page in range(1, 10):
            batch = self._get(f"/repos/{full_name}/pulls?state=closed&sort=updated&per_page=50&page={page}")
            if not batch:
                break
            for pr in batch:
                if pr.get("merged_at"):
                    pulls.append(pr)
            if len(batch) < 50:
                break
        return pulls


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _build_sections(entries: list[dict]) -> dict[str, list[str]]:
    """Group entries by category."""
    sections: dict[str, list[str]] = {}
    for e in entries:
        cat = e["category"]
        sections.setdefault(cat, []).append(e["line"])
    return sections


def generate_markdown(
    repo: str,
    from_ref: str | None,
    to_ref: str,
    entries: list[dict],
    today: str,
) -> str:
    version_label = to_ref if to_ref != "HEAD" else "Unreleased"
    from_label = from_ref or "(beginning)"

    lines = [
        "# Changelog",
        "",
        f"All notable changes to **{repo}** are documented here.",
        "",
        "---",
        "",
        f"## [{version_label}] — {today}",
        f"_Changes since {from_label}_",
        "",
    ]

    sections = _build_sections(entries)
    # Emit ordered categories; catch-all is "Changed" which is in the rules list
    seen: set[str] = set()
    for cat_name, _ in _CATEGORY_RULES:
        if cat_name in sections and cat_name not in seen:
            seen.add(cat_name)
            lines.append(f"### {cat_name}")
            lines.append("")
            for item in sections[cat_name]:
                lines.append(f"- {item}")
            lines.append("")
    # Any category not covered by the explicit rules
    for cat_name, items in sections.items():
        if cat_name not in seen:
            lines.append(f"### {cat_name}")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    if not entries:
        lines.append("_No changes found in this range._")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def collect_entries_from_git(since_ref: str | None, days: int | None) -> list[dict]:
    commits = git_commits_since(since_ref, days)
    entries = []
    for c in commits:
        cat = _categorize(c["title"])
        line = f"{_clean_title(c['title'])} ({c['sha']})"
        entries.append({"category": cat, "line": line, "sha": c["sha"]})
    return entries


def collect_entries_from_github(client: GitHubClient, full_name: str, since_tag: str | None) -> list[dict]:
    """Use PR labels for categorization when GitHub token is available."""
    pulls = client.get_pulls(full_name)
    entries = []
    for pr in pulls:
        labels = [l.get("name", "") for l in pr.get("labels", [])]
        title = pr.get("title", "")
        number = pr.get("number", "")
        cat = _categorize(title, labels)
        line = f"{_clean_title(title)} ([#{number}]({pr.get('html_url', '')}))"
        entries.append({"category": cat, "line": line, "number": number})
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python changelog.py                 # auto-detect last tag, write CHANGELOG.md
  python changelog.py --since v1.2   # from a specific tag
  python changelog.py --days 14      # last 2 weeks
  python changelog.py --output -     # print to stdout
  python changelog.py --dry-run      # preview without writing
""",
    )
    parser.add_argument("--since", help="Start from this tag or SHA (default: last git tag)")
    parser.add_argument("--days", type=int, help="Include commits from last N days")
    parser.add_argument("--output", default="CHANGELOG.md",
                        help="Output file (default: CHANGELOG.md, use - for stdout)")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--token", help="GitHub token (enables PR-based categorization via labels)")
    args = parser.parse_args()

    # Determine starting ref
    since_ref = args.since
    if since_ref is None and args.days is None:
        since_ref = git_last_tag()
        if since_ref:
            print(f"[changelog] Using last tag: {since_ref}", file=sys.stderr)
        else:
            print("[changelog] No tags found — collecting all commits", file=sys.stderr)

    # Try GitHub API if token available for richer categorization
    entries = collect_entries_from_git(since_ref, args.days)

    # Repo name
    try:
        repo = git_repo_name()
    except Exception:
        repo = "this project"

    today = date.today().isoformat()
    from_label = since_ref or (f"last {args.days} days" if args.days else "beginning")
    changelog = generate_markdown(repo, from_label, "Unreleased", entries, today)

    if args.dry_run or args.output == "-":
        print(changelog)
        return

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog)
    print(f"[changelog] Wrote {args.output} ({len(entries)} changes)", file=sys.stderr)


if __name__ == "__main__":
    main()
