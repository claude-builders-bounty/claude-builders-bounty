#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a structured CHANGELOG from git history.

Works in two modes:
1. local repository:  python changelog.py --repo /path/to/repo
2. GitHub API only:   python changelog.py --github owner/repo

The second mode is useful when git clone is unavailable but the GitHub API is.
No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = ("Added", "Fixed", "Changed", "Removed", "Other")
TYPE_MAP = {
    "feat": "Added", "feature": "Added", "add": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed",
    "refactor": "Changed", "perf": "Changed", "update": "Changed",
    "improve": "Changed", "change": "Changed", "docs": "Changed",
    "chore": "Changed", "style": "Changed", "test": "Changed",
    "build": "Changed", "ci": "Changed",
    "remove": "Removed", "delete": "Removed", "drop": "Removed", "deprecate": "Removed",
}
PREFIX = re.compile(r"^\s*([a-zA-Z]+)(?:\([^)]*\))?!?:\s*(.+)$")
VERB = [
    ("Added", re.compile(r"^(add|new|implement|introduce|create|support)\b", re.I)),
    ("Fixed", re.compile(r"^(fix|resolve|correct|repair|handle)\b", re.I)),
    ("Removed", re.compile(r"^(remove|delete|drop|deprecate)\b", re.I)),
    ("Changed", re.compile(r"^(update|improve|refactor|change|rename|move|bump|optimize|replace|docs?)\b", re.I)),
]


@dataclass
class Commit:
    sha: str
    message: str
    url: str = ""

    @property
    def short(self) -> str:
        return self.sha[:7]

    def clean_message(self) -> str:
        text = self.message.splitlines()[0].strip()
        m = PREFIX.match(text)
        if m:
            text = m.group(2).strip()
        return text or self.message.splitlines()[0].strip()

    def category(self) -> str:
        raw = self.message.splitlines()[0].strip()
        m = PREFIX.match(raw)
        if m:
            return TYPE_MAP.get(m.group(1).lower(), "Other")
        for cat, pattern in VERB:
            if pattern.search(raw):
                return cat
        return "Other"


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def latest_tag_local(repo: str) -> str | None:
    try:
        tag = git(repo, "describe", "--tags", "--abbrev=0").strip()
        return tag or None
    except RuntimeError:
        return None


def commits_local(repo: str, since: str | None) -> list[Commit]:
    rng = f"{since}..HEAD" if since else "HEAD"
    out = git(repo, "log", "--no-merges", "--pretty=format:%H%x09%s", rng)
    commits = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, message=subject))
    return commits


def github_json(url: str) -> object:
    headers = {"User-Agent": "changelog-bounty", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def github_latest_tag(repo: str) -> str | None:
    try:
        tags = github_json(f"https://api.github.com/repos/{repo}/tags?per_page=1")
        return tags[0]["name"] if tags else None
    except Exception:
        return None


def commits_github(repo: str, since: str | None) -> list[Commit]:
    if since:
        url = f"https://api.github.com/repos/{repo}/compare/{urllib.parse.quote(since)}...HEAD"
        data = github_json(url)
        raw = data.get("commits", [])
        return [Commit(sha=c["sha"], message=c["commit"]["message"], url=c.get("html_url", "")) for c in raw]
    url = f"https://api.github.com/repos/{repo}/commits?per_page=100"
    data = github_json(url)
    return [Commit(sha=c["sha"], message=c["commit"]["message"], url=c.get("html_url", "")) for c in data]


def build_changelog(commits: list[Commit], title: str = "Changelog", include_links: bool = True) -> str:
    buckets = {cat: [] for cat in CATEGORIES}
    for commit in commits:
        buckets[commit.category()].append(commit)
    lines = [f"# {title}", ""]
    lines.append(f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")
    for cat in CATEGORIES:
        if not buckets[cat]:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for commit in buckets[cat]:
            text = commit.clean_message()
            if include_links and commit.url:
                text += f" ([{commit.short}]({commit.url}))"
            elif include_links:
                text += f" ({commit.short})"
            lines.append(f"- {text}")
        lines.append("")
    if not any(buckets.values()):
        lines.append("_No commits found._")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG from git history")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--repo", help="path to a local git repository")
    src.add_argument("--github", help="GitHub repository, e.g. owner/repo (uses GitHub API)")
    parser.add_argument("--since-tag", help="start after this tag (default: latest tag)")
    parser.add_argument("--output", help="write output file (default: stdout)")
    parser.add_argument("--title", default="Changelog")
    parser.add_argument("--no-links", action="store_true", help="omit commit links/hashes")
    args = parser.parse_args(argv)

    try:
        if args.repo:
            repo_path = str(Path(args.repo).resolve())
            since = args.since_tag if args.since_tag is not None else latest_tag_local(repo_path)
            commits = commits_local(repo_path, since)
        else:
            repo = args.github
            since = args.since_tag if args.since_tag is not None else github_latest_tag(repo)
            commits = commits_github(repo, since)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changelog = build_changelog(commits, title=args.title, include_links=not args.no_links)
    if args.output:
        Path(args.output).write_text(changelog, encoding="utf-8")
        print(f"wrote {args.output} ({len(commits)} commits)")
    else:
        sys.stdout.write(changelog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
