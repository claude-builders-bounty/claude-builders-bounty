#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Pure Python standard library — no third-party dependencies.

Usage:
    python3 generate_changelog.py [--output CHANGELOG.md] [--since <ref>]
                                  [--unreleased] [--version X.Y.Z]
                                  [--dry-run] [--show-hashes] [--include-merges]
    bash changelog.sh              # thin wrapper, same behaviour

Rules (documented, deterministic — first match wins):
    1. ``BREAKING CHANGE`` in the body, or a ``!`` after the conventional
       type (``feat!: ...``), is a breaking change: category Changed, entry
       prefixed with a breaking marker.
    2. Conventional-Commit type wins next:
       feat -> Added | fix/security -> Fixed
       remove/delete/drop/deprecate -> Removed
       refactor/perf/chore/build/ci/docs/style/test/revert/change/
       update/bump/deps -> Changed
    3. Free-text keyword fallback (checked in this order, so that
       "remove the fix" is not misfiled as a fix):
       Removed -> Fixed -> Added -> Changed.
    4. Anything else -> Changed (never silently dropped).
    5. ``Merge ...`` commits are skipped unless ``--include-merges``.
    6. ``Revert "..."`` commits -> Changed, kept as ``Revert: <original>``.
    7. Exact duplicate subjects (case-insensitive) are de-duplicated,
       keeping the first (newest) occurrence.
    8. ``type(scope): description`` -> ``Description (scope)``; the
       description's first letter is capitalised and a trailing ``.``
       is stripped, so entries read like changelog prose, not raw logs.

Output follows Keep a Changelog (https://keepachangelog.com), with the
section order the bounty issue asks for: Added / Fixed / Changed /
Removed. Only non-empty sections are emitted.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
from dataclasses import dataclass, field

__version__ = "1.0.0"

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Conventional-Commit type -> category.
_TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "security": "Fixed",
    "remove": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "deprecate": "Removed",
    "refactor": "Changed",
    "perf": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "revert": "Changed",
    "change": "Changed",
    "update": "Changed",
    "bump": "Changed",
    "deps": "Changed",
}

# Free-text keyword fallback, in priority order.  Each entry is a list of
# regexes matched against the lower-cased subject.
_KEYWORD_MAP = [
    ("Removed", [r"\bremove[sd]?\b", r"\bdelet\w*\b", r"\bdrop\w*\b",
                 r"\bdeprecat\w*\b", r"\buninstall\w*\b"]),
    ("Fixed", [r"\bfix(es|ed|ing)?\b", r"\bbugfix\b", r"\bhotfix\b",
               r"\bpatch\w*\b", r"\bresolv\w*\b", r"\bcorrect\w*\b",
               r"\brepair\w*\b", r"\bbug\b"]),
    ("Added", [r"\badd(s|ed|ing)?\b", r"\bintroduc\w*\b",
               r"\bimplement\w*\b", r"\bnew\b", r"\bsupport for\b",
               r"\bcreat\w*\b"]),
    ("Changed", [r"\brefactor\w*\b", r"\bupdat\w*\b", r"\bupgrad\w*\b",
                 r"\bimprov\w*\b", r"\bchang\w*\b", r"\brenam\w*\b",
                 r"\bmov\w*\b", r"\bbump\w*\b"]),
]

# ``type(scope)!: description`` / ``type: description`` / ``type(scope): ...``
_CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)
_REVERT_RE = re.compile(r'^Revert\s+"(?P<orig>.+)"\s*$', re.IGNORECASE)


@dataclass
class Commit:
    """One parsed git commit (subject line + body)."""

    sha: str
    subject: str
    body: str = ""
    author: str = ""
    date: str = ""


@dataclass
class Entry:
    """One changelog line: its category and cleaned display text."""

    category: str
    text: str
    breaking: bool = False
    sha: str = ""


def _clean_description(desc: str) -> str:
    """Capitalise the first letter, strip a trailing full stop."""
    desc = desc.strip()
    if not desc:
        return desc
    if desc.endswith(".") and not desc.endswith("..."):
        desc = desc[:-1].rstrip()
    return desc[0].upper() + desc[1:]


def classify(commit: Commit) -> Entry | None:
    """Classify one commit. Returns None for commits to skip (merges)."""
    subject = commit.subject.strip()
    if not subject:
        return None
    if subject.startswith("Merge ") and not _INCLUDE_MERGES[0]:
        return None

    breaking = bool(re.search(r"BREAKING CHANGE", commit.body or "",
                              re.IGNORECASE))

    # Reverts: keep them visible, under Changed.
    m = _REVERT_RE.match(subject)
    if m:
        return Entry("Changed", "Revert: " + _clean_description(m.group("orig")),
                     breaking=breaking, sha=commit.sha)

    # Conventional Commits: ``type(scope)!: description``.
    m = _CONVENTIONAL_RE.match(subject)
    if m:
        ctype = m.group("type").lower()
        scope = m.group("scope")
        if m.group("breaking"):
            breaking = True
        desc = _clean_description(m.group("desc"))
        text = f"{desc} ({scope})" if scope else desc
        category = _TYPE_MAP.get(ctype)
        if category is not None:
            if breaking:
                category = "Changed"
            return Entry(category, text, breaking=breaking, sha=commit.sha)
        # Unknown conventional type (e.g. ``wip: ...``) falls through to
        # the keyword check on the description, not the raw subject.
        subject = desc

    if breaking:
        return Entry("Changed", _clean_description(subject),
                     breaking=True, sha=commit.sha)

    lowered = subject.lower()
    for category, patterns in _KEYWORD_MAP:
        if any(re.search(p, lowered) for p in patterns):
            return Entry(category, _clean_description(subject),
                         breaking=False, sha=commit.sha)

    return Entry("Changed", _clean_description(subject),
                 breaking=False, sha=commit.sha)


# Mutable flag so tests can toggle merge handling without globals churn.
_INCLUDE_MERGES = [False]


def categorize(commits: list[Commit], include_merges: bool = False) -> dict[str, list[Entry]]:
    """Classify commits into the four categories, de-duplicated.

    Order inside each category is git-log order (newest first).
    """
    _INCLUDE_MERGES[0] = include_merges
    try:
        buckets: dict[str, list[Entry]] = {c: [] for c in CATEGORIES}
        seen: set[str] = set()
        for commit in commits:
            entry = classify(commit)
            if entry is None:
                continue
            key = entry.text.lower()
            if key in seen:
                continue
            seen.add(key)
            if entry.breaking:
                entry.text = "⚠ BREAKING: " + entry.text
            buckets[entry.category].append(entry)
        return buckets
    finally:
        _INCLUDE_MERGES[0] = False


# ---------------------------------------------------------------------------
# Git access
# ---------------------------------------------------------------------------

def _run_git(args: list[str], repo: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def get_last_tag(repo: str) -> str | None:
    """Most recent reachable tag, or None when the repo has no tags."""
    result = subprocess.run(
        ["git", "-C", repo, "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True, check=False,
    )
    tag = result.stdout.strip()
    return tag or None


def get_commits(repo: str, since: str | None) -> list[Commit]:
    """Commits in ``<since>..HEAD`` (or all history when since is None).

    Record separator is \\x1e, field separator \\x1f — subjects/bodies
    may contain newlines, so plain line-splitting is not safe.
    """
    args = ["log", "--pretty=format:%H%x1f%an%x1f%ad%x1f%s%x1f%b%x1e",
            "--date=short"]
    if since:
        args.insert(1, f"{since}..HEAD")
    raw = _run_git(args, repo)
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x1f")
        if len(parts) < 4:
            continue
        sha, author, date, subject = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ""
        commits.append(Commit(sha=sha, subject=subject.strip(),
                              body=body.strip(), author=author, date=date))
    return commits


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(buckets: dict[str, list[Entry]], version: str,
           date: str, since: str | None, total: int,
           show_hashes: bool = False) -> str:
    """Render the Keep-a-Changelog document."""
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version}] - {date}",
        "",
    ]
    if total == 0:
        lines.append(
            f"No changes since {since}." if since
            else "No commits found in this repository.")
        lines.append("")
        return "\n".join(lines)

    for category in CATEGORIES:
        entries = buckets.get(category, [])
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for entry in entries:
            suffix = f" ({entry.sha[:7]})" if show_hashes and entry.sha else ""
            lines.append(f"- {entry.text}{suffix}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.")
    p.add_argument("--repo", default=".", help="Path to the git repo (default: .)")
    p.add_argument("--output", default="CHANGELOG.md",
                   help="Output file (default: CHANGELOG.md)")
    p.add_argument("--since", default=None,
                   help="Generate since this ref (default: last git tag)")
    p.add_argument("--unreleased", action="store_true",
                   help="Label the section Unreleased")
    p.add_argument("--version", default=None,
                   help="Version label, e.g. 1.2.0 (default: Unreleased)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print to stdout instead of writing a file")
    p.add_argument("--show-hashes", action="store_true",
                   help="Append short commit hashes to entries")
    p.add_argument("--include-merges", action="store_true",
                   help="Include merge commits (skipped by default)")
    p.add_argument("--version-flag", action="store_true", dest="show_version",
                   help="Print the tool version and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.show_version:
        print(f"generate_changelog.py {__version__}")
        return 0

    since = args.since
    if since is None:
        since = get_last_tag(args.repo)

    try:
        commits = get_commits(args.repo, since)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    buckets = categorize(commits, include_merges=args.include_merges)
    total = sum(len(v) for v in buckets.values())
    version = args.version or ("Unreleased" if args.unreleased or since is None
                               else "Unreleased")
    # Default label is Unreleased: commits *after* a tag are, by definition,
    # not yet released. --version overrides it.
    if args.version:
        version = args.version
    date = _dt.date.today().isoformat()

    text = render(buckets, version, date, since, total,
                  show_hashes=args.show_hashes)
    if args.dry_run:
        print(text, end="")
    else:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {args.output} ({version}, {total} entries, "
              f"{len(commits)} commits since {since or 'beginning'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
