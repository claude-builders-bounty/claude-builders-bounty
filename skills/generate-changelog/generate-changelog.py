#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md section from git history.

Usage:
    python3 generate-changelog.py
    python3 generate-changelog.py --since v1.2.0
    python3 generate-changelog.py --since 2026-03-01 --until 2026-03-26
    python3 generate-changelog.py --version v2.0.0 --output CHANGELOG.md

When --output is provided, the new entry is prepended to the existing file
(if any) while preserving a top-level header.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_URL: Optional[str] = None


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def get_repo_url() -> Optional[str]:
    """Infer https GitHub URL from git remote origin."""
    try:
        remote = run_git(["remote", "get-url", "origin"]).strip()
    except RuntimeError:
        return None
    # Convert git@host:owner/repo.git to https://host/owner/repo
    if remote.startswith("git@"):
        remote = remote.replace(":", "/", 1).replace("git@", "https://")
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("http"):
        # Strip credentials from https://user:pass@host/... URLs.
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(remote)
        netloc = parsed.hostname or parsed.netloc
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    return None


def get_last_tag() -> Optional[str]:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"]).strip() or None
    except RuntimeError:
        return None


def get_commits(since: Optional[str], until: str = "HEAD") -> list[dict]:
    range_spec = f"{since}..{until}" if since else until
    log = run_git(
        ["log", range_spec, "--pretty=format:%H%x1f%h%x1f%s%x1f%an", "--no-merges"]
    )
    commits = []
    for line in log.strip().splitlines():
        if not line:
            continue
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        commits.append(
            {
                "hash": parts[0],
                "short": parts[1],
                "message": parts[2],
                "author": parts[3],
            }
        )
    return commits


def parse_conventional(message: str) -> tuple[str, str, bool]:
    """Return (type, clean_message, is_breaking)."""
    pattern = re.compile(
        r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(?P<bang>!)?:\s*(?P<rest>.*)$"
    )
    m = pattern.match(message)
    if not m:
        return "", message, "BREAKING" in message.upper() or "breaking" in message.lower()
    commit_type = m.group("type").lower()
    rest = m.group("rest")
    is_breaking = m.group("bang") == "!" or "BREAKING" in message.upper()
    return commit_type, rest, is_breaking


SECTIONS = [
    ("breaking", "Breaking Changes"),
    ("feat", "Added"),
    ("fix", "Fixed"),
    ("refactor", "Changed"),
    ("perf", "Changed"),
    ("docs", "Documentation"),
    ("test", "Tests"),
    ("chore", "Maintenance"),
    ("ci", "Maintenance"),
    ("build", "Maintenance"),
]


def categorize(commits: list[dict]) -> dict[str, list[dict]]:
    sections: dict[str, list[dict]] = defaultdict(list)
    for commit in commits:
        ctype, clean, breaking = parse_conventional(commit["message"])
        if breaking:
            sections["Breaking Changes"].append({**commit, "message": clean})
            continue
        placed = False
        for prefix, title in SECTIONS:
            if prefix == "breaking":
                continue
            if ctype == prefix:
                sections[title].append({**commit, "message": clean})
                placed = True
                break
        if not placed:
            # Heuristic fallback
            lowered = clean.lower()
            if any(w in lowered for w in ["fix", "bug", "patch"]):
                sections["Fixed"].append(commit)
            elif any(w in lowered for w in ["add", "new", "introduce"]):
                sections["Added"].append(commit)
            elif any(w in lowered for w in ["update", "change", "improve", "refactor", "perf"]):
                sections["Changed"].append(commit)
            elif any(w in lowered for w in ["doc", "readme"]):
                sections["Documentation"].append(commit)
            elif any(w in lowered for w in ["test"]):
                sections["Tests"].append(commit)
            else:
                sections["Other"].append(commit)
    return sections


def format_entry(commit: dict, repo_url: Optional[str]) -> str:
    msg = commit["message"].strip()
    short = commit["short"]
    if repo_url:
        return f"- {msg} ([`{short}`]({repo_url}/commit/{commit['hash']}))"
    return f"- {msg} (`{short}`)"


def render_markdown(
    sections: dict[str, list[dict]], header: str, repo_url: Optional[str]
) -> str:
    lines = [f"## {header}", ""]
    order = [
        "Breaking Changes",
        "Added",
        "Fixed",
        "Changed",
        "Documentation",
        "Tests",
        "Maintenance",
        "Other",
    ]
    for title in order:
        items = sections.get(title, [])
        if not items:
            continue
        lines.append(f"### {title}")
        for commit in items:
            lines.append(format_entry(commit, repo_url))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepend_to_file(content: str, output: Path) -> None:
    existing = ""
    if output.exists():
        existing = output.read_text(encoding="utf-8")
    if existing.strip():
        # Keep a top-level # CHANGELOG header if present.
        lines = existing.splitlines(keepends=True)
        if lines and lines[0].strip().lower().startswith("# changelog"):
            new_body = "".join(lines[1:]).lstrip()
            output.write_text(lines[0] + "\n" + content + "\n" + new_body, encoding="utf-8")
        else:
            output.write_text(content + "\n" + existing, encoding="utf-8")
    else:
        output.write_text("# Changelog\n\n" + content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a CHANGELOG entry from git history")
    parser.add_argument("--since", help="Tag, commit, or date to start from (default: latest tag)")
    parser.add_argument("--until", default="HEAD", help="Tag, commit, or date to end at")
    parser.add_argument("--version", help="Version header (default: Unreleased YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, help="File to prepend the entry to")
    args = parser.parse_args(argv)

    since = args.since or get_last_tag()
    commits = get_commits(since, args.until)
    if not commits:
        print("No commits found in the requested range.", file=sys.stderr)
        return 0

    if args.version:
        header = args.version
    elif args.until != "HEAD":
        header = args.until
    elif since:
        header = f"Unreleased — since {since}"
    else:
        header = f"Unreleased ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"

    sections = categorize(commits)
    repo_url = get_repo_url()
    markdown = render_markdown(sections, header, repo_url)

    if args.output:
        prepend_to_file(markdown, args.output)
        print(f"Updated {args.output}")
    else:
        print(markdown, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
