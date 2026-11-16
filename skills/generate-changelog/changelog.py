#!/usr/bin/env python3
"""
Structured CHANGELOG.md Generator (claude-builders-bounty/claude-builders-bounty#1)
Fetches commits since the latest git tag and categorizes them into:
- Added
- Fixed
- Changed
- Removed
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)
PR_ISSUE_RE = re.compile(r"\(#(\d+)\)")


def classify_commit(subject: str) -> Tuple[str, str]:
    """
    Classifies a commit subject into one of ('Added', 'Fixed', 'Changed', 'Removed')
    and returns (category, cleaned_description).
    """
    raw = subject.strip()
    if not raw:
        return "Changed", "Miscellaneous update"

    m = CONVENTIONAL_RE.match(raw)
    if m:
        ctype = m.group("type").lower()
        scope = m.group("scope")
        desc = m.group("desc").strip()
        formatted = f"**{scope}**: {desc}" if scope else desc

        if ctype in ("feat", "feature", "add"):
            return "Added", formatted
        if ctype in ("fix", "bugfix", "hotfix"):
            return "Fixed", formatted
        if ctype in ("remove", "delete", "drop", "deprecate"):
            return "Removed", formatted
        return "Changed", formatted

    lower = raw.lower()
    first_word = re.split(r"[\s:()-]+", lower)[0] if lower else ""

    if first_word in ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate", "deprecated", "prune"):
        return "Removed", raw
    if first_word in ("fix", "fixed", "fixes", "bug", "hotfix", "resolve", "resolved", "patch", "patched", "repair"):
        return "Fixed", raw
    if first_word in ("add", "added", "feat", "feature", "new", "introduce", "introduced", "implement", "implemented", "create", "created", "support"):
        return "Added", raw
    return "Changed", raw


def get_latest_tag(repo_path: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "describe", "--tags", "--abbrev=0"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out or None
    except Exception:
        return None


def get_remote_repo_url(repo_path: Path) -> Optional[str]:
    try:
        url = subprocess.check_output(
            ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url[len("git@github.com:") :]
        if url.endswith(".git"):
            url = url[:-4]
        return url if url.startswith("http") else None
    except Exception:
        return None


def fetch_commits(repo_path: Path, since_tag: Optional[str] = None, max_count: int = 200) -> List[Dict[str, str]]:
    rev_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        rev_range,
        "--no-merges",
        f"--max-count={max_count}",
        "--pretty=format:%h%x09%s%x09%an%x09%ad",
        "--date=short",
    ]
    out = subprocess.check_output(cmd, text=True, encoding="utf-8", errors="replace")
    commits: List[Dict[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            commits.append(
                {
                    "hash": parts[0].strip(),
                    "subject": parts[1].strip(),
                    "author": parts[2].strip() if len(parts) > 2 else "",
                    "date": parts[3].strip() if len(parts) > 3 else "",
                }
            )
    return commits


def render_changelog(
    commits: List[Dict[str, str]],
    version: str = "Unreleased",
    since_tag: Optional[str] = None,
    repo_url: Optional[str] = None,
    date_str: Optional[str] = None,
) -> str:
    grouped: Dict[str, List[str]] = {cat: [] for cat in CATEGORY_ORDER}
    seen_subjects = set()

    for c in commits:
        subj = c.get("subject", "").strip()
        if not subj or subj in seen_subjects:
            continue
        seen_subjects.add(subj)

        cat, clean_desc = classify_commit(subj)
        short_hash = c.get("hash", "")
        if repo_url and short_hash:
            hash_ref = f"([`{short_hash}`]({repo_url}/commit/{short_hash}))"
        elif short_hash:
            hash_ref = f"(`{short_hash}`)"
        else:
            hash_ref = ""

        entry = f"- {clean_desc} {hash_ref}".strip()
        grouped[cat].append(entry)

    today = date_str or dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        f"## [{version}] - {today}",
    ]
    if since_tag:
        lines.append(f"> Changes since tag `{since_tag}` ({len(commits)} commits analyzed)")
    lines.append("")

    for cat in CATEGORY_ORDER:
        lines.append(f"### {cat}")
        if grouped[cat]:
            lines.extend(grouped[cat])
        else:
            lines.append("- _None_")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history since the last git tag."
    )
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current directory)")
    parser.add_argument("--since-tag", default=None, help="Explicit git tag or revision to start from")
    parser.add_argument("--version", default="Unreleased", help="Version title for the generated release block")
    parser.add_argument("--max-count", type=int, default=200, help="Maximum commits to inspect")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path ('-' for stdout)")
    args = parser.parse_args(argv)

    repo_path = Path(args.repo).resolve()
    since_tag = args.since_tag or get_latest_tag(repo_path)
    repo_url = get_remote_repo_url(repo_path)
    commits = fetch_commits(repo_path, since_tag=since_tag, max_count=args.max_count)
    markdown = render_changelog(
        commits=commits,
        version=args.version,
        since_tag=since_tag,
        repo_url=repo_url,
    )

    if args.output == "-":
        sys.stdout.write(markdown)
    else:
        out_path = Path(args.output)
        out_path.write_text(markdown, encoding="utf-8")
        print(f"[OK] Generated {out_path} ({len(commits)} commits categorized into Added/Fixed/Changed/Removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
