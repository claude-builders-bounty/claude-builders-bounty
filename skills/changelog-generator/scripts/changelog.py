#!/usr/bin/env python3
"""
Generate a Keep-A-Changelog formatted changelog from git history.

Usage:
  python changelog.py [--since vX.Y.Z] [--until HEAD] [--out CHANGELOG.md] [--repo PATH]

Defaults:
  --since   most recent annotated tag, or first commit if no tags exist
  --until   HEAD
  --out     stdout (no file written)
  --repo    current working directory

Categorization order: conventional-commit prefix > keyword in subject > Other.
Author names are stripped from output (we keep only short SHA).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


CC_PREFIX = re.compile(r"^([a-z]+)(?:\([^)]+\))?!?:\s*(.+)$", re.IGNORECASE)

PREFIX_BUCKET = {
    "feat": "Added", "add": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "patch": "Fixed",
    "refactor": "Changed", "perf": "Changed", "style": "Changed",
    "chore": "Changed", "docs": "Changed", "build": "Changed",
    "ci": "Changed", "test": "Changed", "deps": "Changed",
    "revert": "Removed", "remove": "Removed",
}

# Keyword fallback applied when no conventional-commit prefix found.
KEYWORD_BUCKET = [
    ("Removed", re.compile(r"\b(remove|removed|drop|dropped|delete[ds]?)\b", re.I)),
    ("Fixed",   re.compile(r"\b(fix|fixed|repair|correct|resolve[ds]?|patch[ed]?)\b", re.I)),
    ("Added",   re.compile(r"\b(add|added|introduce[ds]?|new)\b", re.I)),
    ("Changed", re.compile(r"\b(update[ds]?|change[ds]?|improve[ds]?|bump|rename[ds]?|refactor[ed]?)\b", re.I)),
]

BUCKET_ORDER = ["Added", "Changed", "Fixed", "Removed", "Other"]


def run(cmd: list[str], cwd: Path) -> str:
    cp = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if cp.returncode != 0:
        raise RuntimeError(f"$ {' '.join(cmd)}\n{cp.stderr}")
    return cp.stdout


def latest_tag(repo: Path) -> str | None:
    try:
        out = run(["git", "describe", "--tags", "--abbrev=0"], repo).strip()
        return out or None
    except RuntimeError:
        return None


def first_commit(repo: Path) -> str:
    return run(["git", "rev-list", "--max-parents=0", "HEAD"], repo).strip().splitlines()[0]


def commits_in_range(repo: Path, since: str, until: str) -> list[tuple[str, str]]:
    """Return [(short_sha, subject), ...] for the given range, oldest first."""
    fmt = "%h%x09%s"  # short_sha TAB subject
    range_arg = f"{since}..{until}" if since else until
    out = run(["git", "log", "--no-merges", "--reverse", f"--pretty=format:{fmt}", range_arg], repo)
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        rows.append((sha, subject))
    return rows


def categorize(subject: str) -> str:
    m = CC_PREFIX.match(subject)
    if m:
        prefix = m.group(1).lower()
        if prefix in PREFIX_BUCKET:
            return PREFIX_BUCKET[prefix]
    for bucket, rx in KEYWORD_BUCKET:
        if rx.search(subject):
            return bucket
    return "Other"


def strip_cc_prefix(subject: str) -> str:
    m = CC_PREFIX.match(subject)
    return m.group(2).strip() if m else subject.strip()


def render(buckets: dict[str, list[tuple[str, str]]], heading: str) -> str:
    out: list[str] = [heading, ""]
    for bucket in BUCKET_ORDER:
        items = buckets.get(bucket) or []
        if not items:
            continue
        out.append(f"### {bucket}")
        for sha, subject in items:
            cleaned = strip_cc_prefix(subject)
            # Normalize first letter to uppercase if reasonable
            if cleaned and cleaned[0].islower():
                cleaned = cleaned[0].upper() + cleaned[1:]
            out.append(f"- {cleaned} ({sha})")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--since", default=None, help="git ref (tag/SHA). Default: latest tag or first commit.")
    p.add_argument("--until", default="HEAD")
    p.add_argument("--out", default=None, help="Write to this file (prepend if exists). Default: stdout.")
    p.add_argument("--repo", default=".", type=Path)
    p.add_argument("--version", default=None, help="Override version label in heading. Default: 'Unreleased' or --since+1.")
    args = p.parse_args()

    repo = args.repo.resolve()
    since = args.since or latest_tag(repo) or first_commit(repo)
    rows = commits_in_range(repo, since, args.until)

    buckets: dict[str, list[tuple[str, str]]] = {}
    for sha, subj in rows:
        buckets.setdefault(categorize(subj), []).append((sha, subj))

    today = dt.date.today().isoformat()
    if args.version:
        label = args.version
    elif args.since and re.match(r"^v?\d+\.\d+\.\d+", args.since):
        label = "Unreleased"  # let humans decide bump; safer default
    else:
        label = "Unreleased"

    heading = f"## [{label}] - {today}"
    body = render(buckets, heading)

    if args.out:
        path = Path(args.out)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if not existing.startswith("# Changelog"):
            existing = "# Changelog\n\nAll notable changes to this project will be documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n" + existing
        # Prepend new section right after the header block.
        if "# Changelog" in existing:
            head, _, rest = existing.partition("\n\n")
            # 'head' is "# Changelog"; rest may start with "All notable..."
            # We want: header + intro paragraph + new section + prior sections.
            # Simpler: split on first "## [" if present.
            idx = existing.find("\n## [")
            if idx >= 0:
                new_text = existing[: idx + 1] + body + "\n" + existing[idx + 1 :]
            else:
                new_text = existing + "\n" + body
        else:
            new_text = body
        path.write_text(new_text, encoding="utf-8")
        print(f"wrote {path}")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
