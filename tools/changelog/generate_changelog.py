#!/usr/bin/env python3
"""generate_changelog — turn git history into a Keep a Changelog-formatted
section, auto-categorized into Added / Changed / Fixed / Removed.

Recognizes Conventional Commits prefixes (feat:, fix:, perf:, refactor:,
revert:, BREAKING CHANGE:) and falls back to verb-prefix heuristics on the
commit subject when prefixes are absent. Skips chore/style/test/build/ci
commits by default.

Usage
-----
    # Print to stdout the diff since the last tag
    generate_changelog.py

    # Specify a base ref (tag, branch, or sha)
    generate_changelog.py --since v1.2.3

    # Override the new release header
    generate_changelog.py --version v1.2.4 --date 2026-05-09

    # Update CHANGELOG.md in place (creates the file if missing)
    generate_changelog.py --in-place --version v1.2.4

    # Write to a different file
    generate_changelog.py --output RELEASE_NOTES.md --version v1.2.4

    # Different project root (default = current working directory)
    generate_changelog.py --repo /path/to/repo

Exit codes
----------
    0   wrote a changelog section successfully
    1   git error (not a repo, ref not found, etc.)
    2   nothing to write (no commits since the base ref)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

KAC_HEADER = "# Changelog"
KAC_PREAMBLE = (
    "All notable changes to this project will be documented in this file.\n\n"
    "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
    "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class Commit:
    sha: str
    short_sha: str
    subject: str
    body: str
    author: str
    email: str

    @property
    def has_breaking(self) -> bool:
        if "BREAKING CHANGE:" in self.body:
            return True
        # Conventional Commits: `feat!:`, `fix(scope)!:` etc. The `!`
        # appears at the end of the prefix, immediately before the colon.
        head, _, _ = self.subject.partition(":")
        return head.endswith("!")


CATEGORIES = ("Added", "Changed", "Fixed", "Removed")


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


_CC_PREFIX = re.compile(
    r"^(?P<type>feat|fix|perf|refactor|revert|chore|docs|style|test|build|ci|deps)"
    r"(?P<scope>\([^)]*\))?(?P<bang>!)?:\s*(?P<rest>.+)$",
    re.I,
)

_CC_TO_BUCKET = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "revert": "Removed",
    "deps": "Changed",
    # The rest are filtered by default
}

# Verbs that strongly suggest a category. Order matters: more specific first.
_VERB_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^(?:add|adds|added|introduce|introduces|introduced|implement|implements|implemented|create|creates|created|support)\b", re.I), "Added"),
    (re.compile(r"^(?:fix|fixes|fixed|resolve|resolves|resolved|patch|patches|patched|correct|corrects|corrected|address|addresses|addressed)\b", re.I), "Fixed"),
    (re.compile(r"^(?:remove|removes|removed|drop|drops|dropped|delete|deletes|deleted|deprecate|deprecates|deprecated|revert|reverts|reverted)\b", re.I), "Removed"),
    (re.compile(r"^(?:update|updates|updated|improve|improves|improved|refactor|refactors|refactored|rename|renames|renamed|change|changes|changed|replace|replaces|replaced|migrate|migrates|migrated|bump|bumps|bumped|upgrade|upgrades|upgraded)\b", re.I), "Changed"),
]

# Default-skip Conventional Commit types (keep `chore`, `docs`, etc. out)
_DEFAULT_SKIPPED_CC = {"chore", "docs", "style", "test", "build", "ci"}


def categorize(commit: Commit, *, include_skipped: bool = False) -> tuple[str | None, str]:
    """Return (bucket, headline). bucket is None when the commit is filtered out.

    The headline is the human-friendly text we put in the changelog: the
    Conventional-Commit `rest` for CC commits, the original subject otherwise.
    """
    subject = commit.subject.strip()

    m = _CC_PREFIX.match(subject)
    if m:
        cc_type = m.group("type").lower()
        rest = m.group("rest").strip()
        if cc_type in _CC_TO_BUCKET:
            bucket = _CC_TO_BUCKET[cc_type]
        elif cc_type in _DEFAULT_SKIPPED_CC and not include_skipped:
            return None, rest
        else:
            bucket = "Changed"
        if commit.has_breaking and bucket != "Removed":
            bucket = "Changed"  # Breaking changes go in Changed unless they're a removal
        return bucket, rest

    for pattern, bucket in _VERB_RULES:
        if pattern.search(subject):
            return bucket, subject

    return "Changed", subject  # catch-all


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------


class GitError(RuntimeError):
    pass


def _run_git(args: list[str], cwd: Path) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise GitError(exc.stderr.strip() or f"git {' '.join(args)} failed") from exc
    return out.stdout


def detect_last_tag(repo: Path) -> str | None:
    try:
        out = _run_git(["describe", "--tags", "--abbrev=0"], repo).strip()
        return out or None
    except GitError:
        return None


_LOG_FORMAT = "%H%x1f%h%x1f%s%x1f%an%x1f%ae%x1f%b%x1e"


def fetch_commits(repo: Path, base: str | None, *, include_merges: bool = False) -> list[Commit]:
    rev_range = f"{base}..HEAD" if base else "HEAD"
    args = ["log", rev_range, f"--format={_LOG_FORMAT}"]
    if not include_merges:
        args.insert(2, "--no-merges")
    log = _run_git(args, repo)
    commits: list[Commit] = []
    for chunk in log.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 6:
            continue
        sha, short, subject, author, email, body = parts[:6]
        commits.append(
            Commit(
                sha=sha,
                short_sha=short,
                subject=subject,
                body=body.strip(),
                author=author,
                email=email,
            )
        )
    return commits


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_section(
    commits: list[Commit],
    version: str,
    on: date,
    *,
    include_skipped: bool = False,
    repo_url: str | None = None,
) -> tuple[str, dict[str, list[str]]]:
    """Return (markdown_section, buckets_used)."""
    buckets: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    skipped = 0
    breaking_seen = False

    for commit in commits:
        bucket, headline = categorize(commit, include_skipped=include_skipped)
        if bucket is None:
            skipped += 1
            continue
        if commit.has_breaking:
            breaking_seen = True
            headline = f"⚠️ **BREAKING:** {headline}"
        bullet = f"- {headline} ({_short_link(commit, repo_url)})"
        buckets[bucket].append(bullet)

    out: list[str] = []
    out.append(f"## [{version}] - {on.isoformat()}")
    out.append("")
    if breaking_seen:
        out.append("> ⚠️  This release contains breaking changes — review before upgrading.")
        out.append("")

    any_written = False
    for cat in CATEGORIES:
        if not buckets[cat]:
            continue
        any_written = True
        out.append(f"### {cat}")
        out.extend(buckets[cat])
        out.append("")

    if not any_written:
        out.append(f"_No notable changes (filtered {skipped} chore/docs/test/style commits)._ ")
        out.append("")

    return "\n".join(out).rstrip() + "\n", buckets


def _short_link(commit: Commit, repo_url: str | None) -> str:
    if repo_url:
        return f"[`{commit.short_sha}`]({repo_url.rstrip('/')}/commit/{commit.sha})"
    return f"`{commit.short_sha}`"


# ---------------------------------------------------------------------------
# In-place file update
# ---------------------------------------------------------------------------


def upsert_changelog(path: Path, new_section: str) -> str:
    """Insert `new_section` directly under the top-level `# Changelog` header.

    Creates the file with the Keep-a-Changelog preamble if it does not exist.
    Returns the resulting full file content.
    """
    if not path.exists():
        full = f"{KAC_HEADER}\n\n{KAC_PREAMBLE}\n\n{new_section.rstrip()}\n"
        path.write_text(full, encoding="utf-8")
        return full

    existing = path.read_text(encoding="utf-8")
    lines = existing.splitlines(keepends=True)

    # Find the '# Changelog' header (allow leading blank lines / BOM)
    header_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            header_index = i
            break

    if header_index is None:
        # No header — prepend a fresh one
        full = f"{KAC_HEADER}\n\n{KAC_PREAMBLE}\n\n{new_section.rstrip()}\n\n{existing}"
        path.write_text(full, encoding="utf-8")
        return full

    # Walk past the header and any preamble paragraphs until we hit the first
    # `## ` release section (or end of file).
    insert_at = header_index + 1
    while insert_at < len(lines) and not lines[insert_at].lstrip().startswith("## "):
        insert_at += 1

    rebuilt = (
        "".join(lines[:insert_at])
        + ("" if insert_at == 0 or lines[insert_at - 1].endswith("\n\n") else "\n")
        + new_section.rstrip()
        + "\n\n"
        + "".join(lines[insert_at:])
    )
    # Collapse 3+ blank lines down to 2 to keep the file tidy.
    rebuilt = re.sub(r"\n{3,}", "\n\n", rebuilt)
    path.write_text(rebuilt, encoding="utf-8")
    return rebuilt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="generate-changelog", description=__doc__.split("\n\n")[0])
    p.add_argument("--repo", default=".", help="Path to the git repo (default: cwd)")
    p.add_argument("--since", help="Base ref (tag, branch, sha). Defaults to last git tag.")
    p.add_argument("--version", default="Unreleased", help="Version label for the new section")
    p.add_argument("--date", default=date.today().isoformat(), help="Date for the new section (YYYY-MM-DD)")
    p.add_argument("--output", help="Write to this file (use '-' for stdout). Default: stdout.")
    p.add_argument("--in-place", action="store_true", help="Update CHANGELOG.md in the repo, prepending the new section")
    p.add_argument("--repo-url", help="GitHub repo URL for commit links (e.g. https://github.com/owner/repo)")
    p.add_argument("--include-skipped", action="store_true", help="Include chore/docs/test/style commits as Changed")
    p.add_argument("--include-merges", action="store_true", help="Include merge commits (default: skipped)")
    p.add_argument("--quiet", action="store_true", help="Suppress stderr informational messages")
    args = p.parse_args(list(argv) if argv is not None else None)

    repo = Path(args.repo).resolve()

    base = args.since
    if not base:
        detected = detect_last_tag(repo)
        if detected:
            base = detected
            if not args.quiet:
                sys.stderr.write(f"Using last tag as base: {base}\n")
        elif not args.quiet:
            sys.stderr.write("No tag found; including the entire history.\n")

    try:
        commits = fetch_commits(repo, base, include_merges=args.include_merges)
    except GitError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    if not commits:
        sys.stderr.write("No commits to write.\n")
        return 2

    try:
        on = date.fromisoformat(args.date)
    except ValueError:
        sys.stderr.write(f"error: --date must be YYYY-MM-DD (got {args.date!r})\n")
        return 1

    section, _ = render_section(
        commits,
        version=args.version,
        on=on,
        include_skipped=args.include_skipped,
        repo_url=args.repo_url,
    )

    if args.in_place:
        target = repo / "CHANGELOG.md"
        upsert_changelog(target, section)
        if not args.quiet:
            sys.stderr.write(f"Updated {target}\n")
    elif args.output and args.output != "-":
        Path(args.output).write_text(section, encoding="utf-8")
        if not args.quiet:
            sys.stderr.write(f"Wrote {args.output}\n")
    else:
        sys.stdout.write(section)

    return 0


if __name__ == "__main__":
    sys.exit(main())
