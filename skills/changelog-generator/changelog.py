#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Auto-categorises commits into Added / Fixed / Changed / Removed based on
Conventional Commits prefixes (feat:, fix:, refactor:, chore:, etc.).
Falls back to a heuristic bucket if no prefix is present.

Exit codes:
  0  success
  1  not inside a git working tree
  2  invalid arguments
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime

CATEGORY_ORDER = ("Added", "Changed", "Fixed", "Removed", "Deprecated", "Security")

# Conventional Commit prefix -> category mapping
_PREFIX_MAP = {
    "feat":     "Added",
    "feature":  "Added",
    "add":      "Added",
    "fix":      "Fixed",
    "bugfix":   "Fixed",
    "refactor": "Changed",
    "perf":     "Changed",
    "chore":    "Changed",
    "docs":     "Changed",
    "style":    "Changed",
    "test":     "Changed",
    "ci":       "Changed",
    "build":    "Changed",
    "remove":   "Removed",
    "rm":       "Removed",
    "delete":   "Removed",
    "deprecate":"Deprecated",
    "security": "Security",
    "sec":      "Security",
}

# Loose-keyword fallback when no Conventional prefix is present
_KEYWORD_FALLBACK = [
    (("add", "new", "introduce", "support"),                       "Added"),
    (("fix", "bug", "patch", "repair", "resolve"),                "Fixed"),
    (("remove", "delete", "drop", "deprecate"),                    "Removed"),
    (("refactor", "rewrite", "clean up", "restructure", "rename"), "Changed"),
    (("perf", "performance", "speed up", "optimize"),             "Changed"),
    (("docs", "doc ", "documentation", "readme"),                  "Changed"),
    (("security", "cve", "vulnerability"),                        "Security"),
]


def run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a subprocess and return stdout (stripped). Raise on non-zero exit."""
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(cmd)}\n{out.stderr}")
    return out.stdout.strip()


def parse_last_tag(cwd: str | None) -> str | None:
    try:
        out = run(["git", "describe", "--tags", "--abbrev=0"], cwd)
    except RuntimeError:
        return None
    return out or None


def categorise(message: str) -> str:
    """Decide which Keep-a-Changelog bucket a commit message belongs in."""
    msg = message.strip()
    if not msg:
        return "Changed"

    # Conventional Commit: <type>(scope)!: <subject>
    m = re.match(r"^([a-zA-Z]+)(?:\([^)]*\))?!?:\s+", msg)
    if m:
        prefix = m.group(1).lower()
        if prefix in _PREFIX_MAP:
            return _PREFIX_MAP[prefix]
        # Unknown prefix -> still a prefix, treat as Changed
        return "Changed"

    lower = msg.lower()
    for keywords, category in _KEYWORD_FALLBACK:
        for kw in keywords:
            # Word-boundary match to avoid 'fix' matching 'prefix'
            if re.search(rf"\b{re.escape(kw)}\b", lower):
                return category

    return "Changed"


def clean_subject(message: str) -> str:
    """Strip Conventional Commit prefix from a commit message."""
    m = re.match(r"^([a-zA-Z]+)(?:\([^)]*\))?!?:\s+(.*)", message.strip())
    if m:
        return m.group(2).strip()
    return message.strip()


def fetch_commits(since_tag: str | None, cwd: str | None, limit: int) -> list[dict]:
    """Return [{sha, subject, author, date}] for commits after since_tag (or all)."""
    sep = "<<--COMMIT-->>"
    fmt = sep.join(["%H", "%s", "%an", "%aI"])

    if since_tag:
        rev_range = f"{since_tag}..HEAD"
    else:
        rev_range = "--all"

    try:
        raw = run(["git", "log", rev_range, f"--pretty=format:{fmt}",
                   "--no-merges", f"-n{limit}"], cwd)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    commits: list[dict] = []
    for block in raw.split(sep):
        if not block or "\x00" in block:
            continue
        # Each block may contain newlines if subject is multi-line; subject is first line.
        parts = block.split("\n", 1)[0].split("\x00", 0)  # noqa: PLW0122
        lines = block.split("\n", 1)
        if not lines or not lines[0]:
            continue
        # We rely on git log's format ordering: %H, %s, %an, %aI joined by newlines? No,
        # git puts them on ONE line if no %n in the format. So we split by the SEP marker
        # above instead of by \n.
        continue

    # Re-parse using the actual separator
    blocks = raw.split(sep)
    commits = []
    i = 0
    while i + 3 < len(blocks):
        sha = blocks[i].strip()
        # Subject may span remaining elements if no newline used; take whole middle.
        # Here we expect the subject to be a single line because we did not use %b.
        rest = [b for b in blocks[i + 1 : i + 4] if b is not None]
        if len(rest) < 3:
            i += 1
            continue
        subject = rest[0].strip()
        author = rest[1].strip()
        date = rest[2].strip()
        if not sha:
            i += 1
            continue
        commits.append({"sha": sha[:9], "subject": subject, "author": author, "date": date})
        i += 4

    return commits


def write_changelog(commits: list[dict], since_tag: str | None,
                    repo_name: str | None, out_path: str, top_n: int = 0) -> None:
    """Group commits into Keep-a-Changelog sections and write Markdown."""
    bucket: "OrderedDict[str, list[dict]]" = OrderedDict((c, []) for c in CATEGORY_ORDER)
    for c in commits:
        cat = categorise(c["subject"])
        bucket.setdefault(cat, []).append(c)

    lines: list[str] = []
    lines.append(f"# Changelog")
    lines.append("")
    title_repo = repo_name or "this project"
    if since_tag:
        lines.append(f"Changes in {title_repo} since `{since_tag}`.")
    else:
        lines.append(f"All recorded changes for {title_repo}.")
    lines.append("")
    lines.append(f"_Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")

    total = 0
    for category in CATEGORY_ORDER:
        items = bucket.get(category, [])
        if not items:
            continue
        if top_n and len(items) > top_n:
            items = items[:top_n]
        lines.append(f"## {category}")
        lines.append("")
        for c in items:
            lines.append(f"- {clean_subject(c['subject'])} (`{c['sha']}`, {c['author']}, {c['date']})")
        lines.append("")
        total += len(items)

    if total == 0:
        lines.append("_No commits recorded in this range._")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since-tag", default=None,
                   help="Only include commits after this tag (default: all reachable commits)")
    p.add_argument("--since", default=None,
                   help="Only include commits after this date (passed to `git log --since`)")
    p.add_argument("--limit", type=int, default=200,
                   help="Max commits to consider (default 200)")
    p.add_argument("--out", default="CHANGELOG.md", help="Output file path (default CHANGELOG.md)")
    p.add_argument("--top-per-section", type=int, default=0,
                   help="If >0, cap each category to N most recent items")
    p.add_argument("--repo-name", default=None, help="Override repo name in the header")
    p.add_argument("--cwd", default=".", help="Working directory (default '.')")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit:
        return 2

    try:
        run(["git", "rev-parse", "--show-toplevel"], args.cwd)
    except RuntimeError:
        print("fatal: not inside a git working tree", file=sys.stderr)
        return 1

    log_args = ["git", "log", "--pretty=format:%H%n%s%n%an%n%aI%n---END---", "--no-merges"]
    if args.since_tag:
        log_args.insert(2, f"{args.since_tag}..HEAD")
    if args.since:
        log_args.extend(["--since", args.since])
    log_args.append(f"-n{args.limit}")

    raw = run(log_args, args.cwd)

    commits: list[dict] = []
    blocks = [b for b in raw.split("---END---") if b.strip()]
    for block in blocks:
        parts = block.strip().split("\n", 3)
        if len(parts) < 4:
            continue
        sha, subject, author, date = parts[0], parts[1], parts[2], parts[3]
        commits.append({
            "sha": sha[:9],
            "subject": subject.strip(),
            "author": author.strip(),
            "date": date.strip(),
        })

    if not commits:
        # Still emit an empty CHANGELOG so downstream consumers have a file.
        commits = []

    write_changelog(commits, args.since_tag, args.repo_name, args.out, args.top_per_section)
    print(f"wrote {args.out} ({len(commits)} commits grouped)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
