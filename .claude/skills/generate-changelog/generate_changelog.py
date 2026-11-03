#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from Conventional Commits since the last tag.

Stdlib only; portable on Windows, Linux and macOS. Usage:

    python generate_changelog.py [REPO] [-o CHANGELOG.md] [--since REF]
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

TITLE = "# Changelog"
INTRO = (
    "\nAll notable changes to this project are documented in this file.\n"
    "Generated from Conventional Commits by `generate_changelog.py`.\n"
)
SECTIONS = ("Breaking Changes", "Added", "Fixed", "Changed", "Removed")

RE_CONVENTIONAL = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()]*)\))?(?P<bang>!)?: (?P<desc>.+)$"
)
# shortcut: removal verbs in the description decide the Removed category;
# upgrade to a `remove:` type convention if false positives show up.
RE_REMOVAL = re.compile(r"^(?:remov|delet|drop)(?:e|es|ing|ed)?\b", re.IGNORECASE)


def git(repo, *args, check=True):
    proc = subprocess.run(
        ("git", *args), cwd=repo, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if check and proc.returncode:
        sys.exit(f"error: git {' '.join(args)} failed: {proc.stderr.strip()}")
    # strip() would eat \x1f/\x1e record separators (Python treats them as space)
    return proc.stdout.strip("\r\n ")


def latest_tag(repo):
    return git(repo, "describe", "--tags", "--abbrev=0", check=False) or None


def read_commits(repo, rev_range):
    raw = git(repo, "log", rev_range, "--pretty=format:%h%x1f%s%x1f%b%x1e")
    commits = []
    for record in raw.split("\x1e"):
        record = record.strip("\n ")
        if not record:
            continue
        short, subject, body = record.split("\x1f", 2)
        commits.append((short.strip(), subject.strip(), body))
    return commits


def categorize(commit_type, desc, breaking):
    if breaking:
        return "Breaking Changes"
    if commit_type == "fix":
        return "Fixed"
    if RE_REMOVAL.match(desc):
        return "Removed"
    if commit_type == "feat":
        return "Added"
    return "Changed"


def build_section(commits, base):
    groups = {name: [] for name in SECTIONS}
    for short, subject, body in commits:
        match = RE_CONVENTIONAL.match(subject)
        breaking = bool(match and match["bang"]) or "BREAKING CHANGE" in body
        if match:
            desc = match["desc"]
            text = f"**{match['scope']}**: {desc}" if match["scope"] else desc
            cat = categorize(match["type"], desc, breaking)
        else:
            text, cat = subject, ("Breaking Changes" if breaking else "Changed")
        groups[cat].append(f"- {text} (`{short}`)")
    note = f"since `{base}`" if base else "from the beginning of repository history"
    lines = [f"## [Unreleased] - {date.today().isoformat()}", "", f"_All commits {note}._", ""]
    for name in SECTIONS:
        if groups[name]:
            lines += [f"### {name}", "", *groups[name], ""]
    return "\n".join(lines).rstrip() + "\n"


def merge(existing, section):
    """Prepend the new section below the existing title; keep older sections."""
    if not existing.strip():
        return f"{TITLE}\n{INTRO}\n{section}"
    idx = existing.find("\n## ")
    head = existing if idx == -1 else existing[:idx].rstrip()
    tail = "" if idx == -1 else existing[idx + 1:]
    joined = f"{head}\n\n{section}" + (f"\n{tail}" if tail.strip() else "")
    return joined.rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Generate a CHANGELOG from git history.")
    ap.add_argument("repo", nargs="?", default=".", help="git repository path (default: cwd)")
    ap.add_argument("-o", "--output", help="write/merge result into this file, e.g. CHANGELOG.md")
    ap.add_argument("--since", metavar="REF", help="start of range (default: latest tag, else full history)")
    args = ap.parse_args()

    base = args.since or latest_tag(args.repo)
    rev_range = f"{base}..HEAD" if base else "HEAD"
    commits = read_commits(args.repo, rev_range)
    if not commits:
        sys.exit(f"error: no commits found in range {rev_range}")

    section = build_section(commits, base)
    if args.output:
        out = Path(args.output)
        existing = out.read_text(encoding="utf-8") if out.exists() else ""
        out.write_text(merge(existing, section), encoding="utf-8")
        print(f"wrote {out} ({len(commits)} commits)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(merge("", section))


if __name__ == "__main__":
    main()
