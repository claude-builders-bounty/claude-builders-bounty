#!/usr/bin/env python3
"""
generate_changelog.py — build a structured CHANGELOG.md from git history.

Collects commits since the last git tag (or the full history if none), classifies
each into Added / Fixed / Changed / Removed using conventional-commit prefixes and
keyword heuristics, and writes a Keep-a-Changelog-style file.

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations
import argparse
import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path

SECTIONS = ("Added", "Fixed", "Changed", "Removed")

# ordered rules: first match wins
_RULES = [
    ("Added", re.compile(r"^(feat|feature|add)(\(|:|\!|$)|(^|\b)(add|added|adds|introduce|introduces|implement|implements)\b", re.I)),
    ("Fixed", re.compile(r"^(fix|bug|hotfix|patch)(\(|:|\!|$)|(^|\b)(fix|fixed|fixes|bug|patch|resolve|resolves|repair|repairs)\b", re.I)),
    ("Removed", re.compile(r"^(remove|removed|rm|delete|drop)(\(|:|\!|$)|(^|\b)(remove|removed|delete|deleted|drop|dropped)\b", re.I)),
]


def categorize(subject: str) -> str:
    """Classify a commit subject into one of SECTIONS (default: Changed)."""
    subject = (subject or "").strip()
    for name, rx in _RULES:
        if rx.search(subject):
            return name
    return "Changed"


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "git command failed")
    return out.stdout


def last_tag() -> str:
    out = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def collect_commits(since_tag: str):
    rng = f"{since_tag}..HEAD" if since_tag else "HEAD"
    raw = _git("log", rng, "--pretty=format:%h\x09%s")
    commits = []
    for line in raw.splitlines():
        if "\x09" in line:
            sha, subject = line.split("\x09", 1)
            commits.append((sha, subject))
    return commits


def build_changelog(commits, version: str, date: str, previous: str = "") -> str:
    buckets = {s: [] for s in SECTIONS}
    for sha, subject in commits:
        buckets[categorize(subject)].append(f"* {subject} ({sha})")
    lines = ["# Changelog", "", f"## [{version}] - {date}", ""]
    wrote = False
    for section in SECTIONS:
        if not buckets[section]:
            continue
        wrote = True
        lines.append(f"### {section}")
        lines.append("")
        lines.extend(buckets[section])
        lines.append("")
    if not wrote:
        lines.append(f"_No commits found since {previous or 'the beginning'}._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    ap.add_argument("output", nargs="?", default="CHANGELOG.md", help="output file (default: CHANGELOG.md)")
    ap.add_argument("--version", default=None, help="release version (default: last tag or 'unreleased')")
    ap.add_argument("--date", default=None, help="release date (default: today, YYYY-MM-DD)")
    args = ap.parse_args(argv)
    try:
        tag = last_tag()
    except RuntimeError:
        print("error: not inside a git repository", file=sys.stderr)
        return 1
    version = args.version or tag or "unreleased"
    date = args.date or _dt.date.today().isoformat()
    text = build_changelog(collect_commits(tag), version, date, previous=tag)
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output} (range: {tag + '..HEAD' if tag else 'HEAD'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
