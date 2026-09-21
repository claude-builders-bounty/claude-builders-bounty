#!/usr/bin/env python3
"""Generate a Keep-a-Changelog-style CHANGELOG.md from git history since the last tag.

Stdlib only. Conventional-commit prefixes + keyword fallback.
Categories: Added / Fixed / Changed / Removed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Iterable

CONVENTIONAL = re.compile(
    r"^(?P<type>feat|fix|fixes|bugfix|docs|doc|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<sub>.+)$",
    re.IGNORECASE,
)

TYPE_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "fixes": "Fixed",
    "bugfix": "Fixed",
    "docs": "Changed",
    "doc": "Changed",
    "style": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "revert": "Changed",
}

KEYWORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(remove|removed|delete|deleted|drop|dropped)\b", re.I), "Removed"),
    (re.compile(r"\b(add|added|introduce|introduced|implement|implemented|support|new)\b", re.I), "Added"),
    (re.compile(r"\b(fix|fixed|bug|hotfix|patch|resolve|resolved)\b", re.I), "Fixed"),
    (re.compile(r"\b(change|changed|update|updated|upgrade|upgraded|rename|renamed|refactor|improve|improved)\b", re.I), "Changed"),
]

SKIP = re.compile(r"^(merge|wip|tmp|temp)\b", re.I)
HASH_RE = re.compile(r"\b([0-9a-f]{7,40})\b")


def run(cmd: list[str], cwd: str) -> str:
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Command failed ({' '.join(cmd)}):\n{e.output.decode(errors='replace')}") from e
    return out.decode(errors="replace").strip()


def last_tag(cwd: str) -> str | None:
    try:
        return run(["git", "describe", "--tags", "--abbrev=0"], cwd) or None
    except SystemExit:
        return None


def commits_since(cwd: str, tag: str | None, max_count: int) -> list[tuple[str, str]]:
    rng = f"{tag}..HEAD" if tag else "HEAD"
    fmt = "%H%x00%s"
    raw = run(["git", "log", rng, f"--max-count={max_count}", f"--pretty=format:{fmt}"], cwd)
    rows: list[tuple[str, str]] = []
    if not raw:
        return rows
    for line in raw.split("\n"):
        if "\x00" not in line:
            continue
        sha, subject = line.split("\x00", 1)
        rows.append((sha[:7], subject.strip()))
    return rows


def categorize(subject: str) -> tuple[str, str, bool]:
    """Return (category, cleaned_subject, breaking)."""
    m = CONVENTIONAL.match(subject)
    breaking = False
    if m:
        ctype = m.group("type").lower()
        breaking = bool(m.group("breaking")) or "breaking" in subject.lower()
        sub = m.group("sub").strip()
        scope = m.group("scope")
        if scope:
            sub = f"**{scope}**: {sub}"
        cat = TYPE_MAP.get(ctype, "Changed")
        # Wording beats type for removals (e.g. "docs: remove dead link")
        for pat, override in KEYWORD_RULES:
            if override == "Removed" and pat.search(sub):
                return override, sub, breaking
        return cat, sub, breaking

    if SKIP.match(subject):
        return "Changed", subject, False

    for pat, cat in KEYWORD_RULES:
        if pat.search(subject):
            return cat, subject, "breaking" in subject.lower()
    return "Changed", subject, False


def render(
    repo_name: str,
    tag: str | None,
    items: dict[str, list[tuple[str, str, bool]]],
    today: str,
) -> str:
    version = "Unreleased"
    header = f"# Changelog\n\nAll notable changes to **{repo_name}** are documented here.\n"
    range_note = f"Generated from commits since `{tag}`." if tag else "Generated from recent commits (no git tag found)."
    body = [header, f"## [{version}] — {today}", "", f"_{range_note}_", ""]
    order = ["Added", "Fixed", "Changed", "Removed"]
    for cat in order:
        entries = items.get(cat) or []
        if not entries:
            continue
        body.append(f"### {cat}")
        body.append("")
        for sha, text, breaking in entries:
            prefix = "⚠️ **BREAKING** " if breaking else ""
            body.append(f"- {prefix}{text} (`{sha}`)")
        body.append("")
    if not any(items.get(c) for c in order):
        body.append("_No categorized commits in range._")
        body.append("")
    return "\n".join(body).rstrip() + "\n"


def build_items(commits: Iterable[tuple[str, str]]) -> dict[str, list[tuple[str, str, bool]]]:
    items: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)
    seen: set[str] = set()
    for sha, subject in commits:
        key = subject.lower()
        if key in seen:
            continue
        seen.add(key)
        cat, text, breaking = categorize(subject)
        items[cat].append((sha, text, breaking))
    return items


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history since last tag")
    p.add_argument("--cwd", default=".", help="git repo path (default: .)")
    p.add_argument("-o", "--output", default="CHANGELOG.md", help="output file (default: CHANGELOG.md)")
    p.add_argument("--stdout", action="store_true", help="print to stdout instead of writing a file")
    p.add_argument("--max-count", type=int, default=200, help="max commits to scan")
    p.add_argument("--repo-name", default=None, help="display name (default: directory name)")
    args = p.parse_args(argv)

    cwd = os.path.abspath(args.cwd)
    if not os.path.isdir(os.path.join(cwd, ".git")) and not os.path.isfile(os.path.join(cwd, ".git")):
        # allow worktrees / gitdir files
        try:
            run(["git", "rev-parse", "--git-dir"], cwd)
        except SystemExit:
            print(f"Not a git repository: {cwd}", file=sys.stderr)
            return 2

    tag = last_tag(cwd)
    commits = commits_since(cwd, tag, args.max_count)
    items = build_items(commits)
    name = args.repo_name or os.path.basename(cwd.rstrip(os.sep))
    today = dt.date.today().isoformat()
    text = render(name, tag, items, today)

    if args.stdout:
        sys.stdout.write(text)
    else:
        out_path = args.output if os.path.isabs(args.output) else os.path.join(cwd, args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {out_path} ({sum(len(v) for v in items.values())} entries; since {tag or 'beginning'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
