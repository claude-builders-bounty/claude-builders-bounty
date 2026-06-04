#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Parses Conventional Commits, buckets them by semver tag into "Keep a Changelog"
sections, and emits Markdown. Zero third-party dependencies — standard library
and the `git` CLI only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone

RECORD_SEP = "\x1e"  # ASCII record separator — never appears in commit text
FIELD_SEP = "\x1f"   # ASCII unit separator

# Conventional Commit type -> Keep a Changelog section.
TYPE_TO_SECTION = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "change": "Changed",
    "revert": "Changed",
    "deprecate": "Deprecated",
    "remove": "Removed",
    "security": "Security",
    "sec": "Security",
}

# Order sections appear in each release block (Keep a Changelog convention).
SECTION_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

# Types that are noise in a user-facing changelog and dropped unless --include-all.
SKIP_TYPES = {"chore", "ci", "build", "test", "tests", "style", "docs", "doc"}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)
SEMVER_TAG_RE = re.compile(r"^v?\d+\.\d+\.\d+")


class GitError(RuntimeError):
    pass


def run_git(args: list[str], repo: str) -> str:
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def get_tags(repo: str) -> list[tuple[str, str]]:
    """Return [(tag, iso_date)] newest first, semver tags only."""
    out = run_git(
        ["tag", "--list", "--sort=-creatordate", "--format=%(refname:short)%(creatordate:short)"],
        repo,
    )
    tags: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # refname is everything up to the trailing YYYY-MM-DD date.
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})$", line)
        date = date_match.group(1) if date_match else ""
        name = line[: date_match.start()] if date_match else line
        name = name.strip()
        if SEMVER_TAG_RE.match(name):
            tags.append((name, date))
    return tags


def get_commits(repo: str, rev_range: str | None) -> list[dict]:
    fmt = FIELD_SEP.join(["%H", "%s", "%b", "%an", "%ad"]) + RECORD_SEP
    args = ["log", f"--pretty=format:{fmt}", "--date=short", "--no-merges"]
    if rev_range:
        args.append(rev_range)
    out = run_git(args, repo)
    commits: list[dict] = []
    for raw in out.split(RECORD_SEP):
        raw = raw.strip("\n")
        if not raw.strip():
            continue
        parts = raw.split(FIELD_SEP)
        if len(parts) < 5:
            continue
        sha, subject, body, author, date = parts[0], parts[1], parts[2], parts[3], parts[4]
        commits.append(
            {
                "sha": sha.strip(),
                "subject": subject.strip(),
                "body": body.strip(),
                "author": author.strip(),
                "date": date.strip(),
            }
        )
    return commits


def classify(commit: dict, include_all: bool) -> tuple[str, str, bool] | None:
    """Return (section, clean_description, is_breaking) or None to drop."""
    subject = commit["subject"]
    match = CONVENTIONAL_RE.match(subject)
    breaking = "BREAKING CHANGE" in commit["body"] or "BREAKING-CHANGE" in commit["body"]

    if match:
        ctype = match.group("type").lower()
        scope = match.group("scope")
        desc = match.group("desc").strip()
        if match.group("breaking"):
            breaking = True
        if ctype in SKIP_TYPES and not include_all:
            return None
        section = TYPE_TO_SECTION.get(ctype, "Changed")
        if scope:
            desc = f"**{scope}:** {desc}"
        return section, desc, breaking

    # Non-conventional commit: keep only when including everything.
    if include_all:
        return "Changed", subject, breaking
    return None


def build_release_blocks(repo: str, include_all: bool, unreleased_only: bool) -> "OrderedDict[str, dict]":
    tags = get_tags(repo)
    blocks: "OrderedDict[str, dict]" = OrderedDict()

    if unreleased_only or not tags:
        rev_range = f"{tags[0][0]}..HEAD" if tags else None
        commits = get_commits(repo, rev_range)
        blocks["Unreleased"] = {"date": "", "commits": commits}
        if unreleased_only:
            return blocks
        if not tags:
            return blocks

    # Unreleased: commits after the newest tag.
    if not unreleased_only and tags:
        unreleased = get_commits(repo, f"{tags[0][0]}..HEAD")
        if unreleased:
            blocks["Unreleased"] = {"date": "", "commits": unreleased}

    # One block per tag, range = previous_tag..tag.
    for i, (tag, date) in enumerate(tags):
        lower = tags[i + 1][0] if i + 1 < len(tags) else None
        rev_range = f"{lower}..{tag}" if lower else tag
        blocks[tag] = {"date": date, "commits": get_commits(repo, rev_range)}
    return blocks


def render(blocks: "OrderedDict[str, dict]", include_all: bool, repo_url: str | None) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented here.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
    ]

    for version, data in blocks.items():
        sections: dict[str, list[str]] = {name: [] for name in SECTION_ORDER}
        breaking_notes: list[str] = []

        for commit in data["commits"]:
            result = classify(commit, include_all)
            if result is None:
                continue
            section, desc, is_breaking = result
            short = commit["sha"][:7]
            entry = f"- {desc} (`{short}`)"
            sections[section].append(entry)
            if is_breaking:
                breaking_notes.append(f"- {desc} (`{short}`)")

        if not any(sections.values()) and not breaking_notes:
            continue

        if version == "Unreleased":
            header = "## [Unreleased]"
        else:
            date = data["date"] or today
            header = f"## [{version}] - {date}"
        lines.append(header)
        lines.append("")

        if breaking_notes:
            lines.append("### ⚠ BREAKING CHANGES")
            lines.append("")
            lines.extend(dict.fromkeys(breaking_notes))  # de-dupe, keep order
            lines.append("")

        for name in SECTION_ORDER:
            entries = sections[name]
            if not entries:
                continue
            lines.append(f"### {name}")
            lines.append("")
            lines.extend(entries)
            lines.append("")

    if repo_url:
        lines.append(f"[repository]: {repo_url}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a Keep a Changelog file from git history.",
    )
    p.add_argument("-r", "--repo", default=".", help="Path to the git repository (default: .)")
    p.add_argument("-o", "--output", help="Write to this file instead of stdout.")
    p.add_argument(
        "--unreleased-only",
        action="store_true",
        help="Only emit changes since the most recent semver tag.",
    )
    p.add_argument(
        "--include-all",
        action="store_true",
        help="Include chore/ci/docs/test and non-conventional commits.",
    )
    p.add_argument("--repo-url", help="Optional repository URL to footer-link.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        run_git(["rev-parse", "--is-inside-work-tree"], args.repo)
    except GitError as exc:
        print(f"error: {args.repo} is not a git repository ({exc})", file=sys.stderr)
        return 1
    try:
        blocks = build_release_blocks(args.repo, args.include_all, args.unreleased_only)
    except GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = render(blocks, args.include_all, args.repo_url)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
