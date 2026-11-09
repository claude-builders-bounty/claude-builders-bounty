#!/usr/bin/env python3
"""generate-changelog: structured CHANGELOG.md from git history.

Reads the commits since the last git tag (or a range you choose),
auto-categorizes each commit into Added / Fixed / Changed / Removed,
and renders a Keep-a-Changelog-formatted Markdown section.

Usage:
    python3 changelog.py                      # since last tag, to stdout
    python3 changelog.py --version 1.4.0      # title the section 1.4.0
    python3 changelog.py --tag v1.2.0         # start from a specific tag
    python3 changelog.py --tag v1.2.0 --to v1.3.0   # a release range
    python3 changelog.py --prepend CHANGELOG.md     # insert into a file
    python3 changelog.py --output section.md        # write to a file

Categorization is deterministic:
  1. A leading remove/delete/drop verb in the subject -> Removed
     (even in "fix: remove ...", the removal is the notable change).
  2. Conventional Commits type: feat -> Added, fix -> Fixed,
     everything else (refactor, perf, docs, chore, ...) -> Changed.
  3. Imperative keyword in the first word: add/introduce/create/
     implement -> Added; fix/resolve/correct/patch -> Fixed.
  4. A commit that only deletes files -> Removed.
  5. Default -> Changed.

Standard library only; requires git on PATH (it is a git-history tool).
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

REMOVE_VERBS = {"remove", "removes", "removed", "delete", "deletes",
                "deleted", "drop", "drops", "dropped"}
ADD_VERBS = {"add", "adds", "added", "introduce", "introduces",
             "introducing", "create", "creates", "created", "implement",
             "implements", "implemented", "new"}
FIX_VERBS = {"fix", "fixes", "fixed", "resolve", "resolves", "resolved",
             "correct", "corrects", "corrected", "patch", "patches",
             "patched", "hotfix"}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<rest>.*)$"
)


def git(repo: str, *args: str) -> str:
    """Run a git command in `repo` and return stdout (stripped)."""
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip("\n")


def last_tag(repo: str) -> str | None:
    """Most recent tag reachable from HEAD, or None if there are none."""
    try:
        return git(repo, "describe", "--tags", "--abbrev=0") or None
    except subprocess.CalledProcessError:
        return None


def read_commits(repo: str, since: str | None, until: str) -> list[dict]:
    """Commits in (since, until] with subjects and per-file statuses."""
    rev_range = f"{since}..{until}" if since else until
    raw = git(
        repo, "log", rev_range, "--no-merges",
        "--name-status", "--pretty=format:COMMIT%x1f%h%x1f%s",
    )
    commits = []
    current = None
    for line in raw.splitlines():
        if line.startswith("COMMIT\x1f"):
            _, short, subject = line.split("\x1f", 2)
            current = {"hash": short, "subject": subject.strip(),
                       "statuses": []}
            commits.append(current)
        elif line.strip() and current is not None:
            # name-status lines look like "A\tpath" or "R100\told\tnew"
            current["statuses"].append(line.split("\t", 1)[0])
    return commits


def categorize(subject: str, statuses: list[str]) -> tuple[str, str, str | None]:
    """Return (category, cleaned_subject, scope) for one commit."""
    scope = None
    rest = subject.strip()
    conv_type = None
    m = CONVENTIONAL_RE.match(rest)
    if m:
        conv_type = m.group("type").lower()
        scope = m.group("scope")
        rest = m.group("rest").strip() or rest

    first_word = re.split(r"[\s:]", rest, maxsplit=1)[0].lower().strip(".,")

    # 1. An explicit removal verb is the notable change.
    if first_word in REMOVE_VERBS:
        return "Removed", _clean(rest), scope
    # 2. Conventional Commits type.
    if conv_type == "feat":
        return "Added", _clean(rest), scope
    if conv_type == "fix":
        return "Fixed", _clean(rest), scope
    if conv_type is not None:
        return "Changed", _clean(rest), scope
    # 3. Imperative keyword fallback.
    if first_word in ADD_VERBS:
        return "Added", _clean(rest), scope
    if first_word in FIX_VERBS:
        return "Fixed", _clean(rest), scope
    # 4. A commit whose only effect is deleting files.
    if statuses and all(s.startswith("D") for s in statuses):
        return "Removed", _clean(rest), scope
    # 5. Default.
    return "Changed", _clean(rest), scope


def _clean(text: str) -> str:
    text = text.strip().rstrip(".")
    if text:
        text = text[0].upper() + text[1:]
    return text


def render_section(version: str, date: str, grouped: dict[str, list[str]]) -> str:
    lines = [f"## [{version}] - {date}", ""]
    wrote_any = False
    for cat in CATEGORIES:
        entries = grouped.get(cat) or []
        if not entries:
            continue
        wrote_any = True
        lines.append(f"### {cat}")
        lines.append("")
        for entry in entries:
            lines.append(f"- {entry}")
        lines.append("")
    if not wrote_any:
        lines.append("_No notable changes._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_section(repo: str, since: str | None, until: str,
                  version: str, date: str) -> str:
    if since is None:
        since = last_tag(repo)  # None again only when the repo has no tags
    commits = read_commits(repo, since, until)
    grouped: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    for commit in commits:
        category, text, scope = categorize(commit["subject"],
                                           commit["statuses"])
        entry = f"**{scope}:** {text}" if scope else text
        grouped[category].append(entry)
    return render_section(version, date, grouped)


def prepend_to_file(path: str, section: str) -> None:
    """Insert `section` into an existing CHANGELOG before its first entry."""
    if not os.path.exists(path):
        header = ("# Changelog\n\nAll notable changes to this project are "
                  "documented in this file.\n\n")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header + section)
        return
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    lines = content.splitlines(keepends=True)
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("## "):
            insert_at = i
            break
    new = "".join(lines[:insert_at]) + section + "\n" + "".join(lines[insert_at:])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG section from git history.")
    parser.add_argument("--repo", default=".",
                        help="Path to the git repository (default: cwd)")
    parser.add_argument("--tag", default=None,
                        help="Start tag/ref (default: the last git tag)")
    parser.add_argument("--to", default="HEAD",
                        help="End ref (default: HEAD)")
    parser.add_argument("--version", default="Unreleased",
                        help="Version label for the section (default: Unreleased)")
    parser.add_argument("--date", default=datetime.date.today().isoformat(),
                        help="Release date, YYYY-MM-DD (default: today)")
    parser.add_argument("--output", default=None,
                        help="Write the section to this file instead of stdout")
    parser.add_argument("--prepend", default=None, metavar="CHANGELOG",
                        help="Insert the section at the top of this CHANGELOG file")
    args = parser.parse_args(argv)

    try:
        git(args.repo, "rev-parse", "--git-dir")
    except subprocess.CalledProcessError:
        print(f"error: {args.repo} is not a git repository", file=sys.stderr)
        return 2

    since = args.tag if args.tag is not None else last_tag(args.repo)
    section = build_section(args.repo, since, args.to, args.version, args.date)

    if args.prepend:
        prepend_to_file(args.prepend, section)
        print(f"Inserted [{args.version}] section into {args.prepend}")
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(section)
        print(f"Wrote [{args.version}] section to {args.output}")
    else:
        sys.stdout.write(section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
