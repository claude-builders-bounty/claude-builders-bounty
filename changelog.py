#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py              # since last tag
    python changelog.py v1.0.0       # since specific tag/commit
    python changelog.py HEAD~20      # since specific commit
"""
import subprocess, sys, os, re
from datetime import datetime
from collections import OrderedDict

CATEGORIES = OrderedDict([
    ("Added", ["feat", "add", "new", "introduce", "implement"]),
    ("Changed", ["refactor", "refactor", "improve", "update", "change", "upgrade", "enhance"]),
    ("Fixed", ["fix", "bugfix", "bug", "hotfix", "patch", "correct", "resolve"]),
    ("Removed", ["remove", "delete", "drop", "deprecate", "obsolete", "rm"]),
])

def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def get_commits(since=""):
    """Return list of (hash, subject, body) tuples."""
    range_spec = f"{since}..HEAD" if since else ""
    fmt = "--format=%H|||%s|||%b"
    cmd = f'git log {fmt} {range_spec}'
    raw = run(cmd) if range_spec else run(f'git log {fmt}')
    commits = []
    for line in raw.split("\n"):
        if "|||" not in line: continue
        h, s, b = line.split("|||", 2)
        commits.append((h[:7], s.strip(), (b or "").strip()))
    return commits

def categorize(subject, body=""):
    text = (subject + " " + body).lower()
    # Conventional commit prefix first
    if subject.startswith("feat") or subject.startswith("feat:") or subject.startswith("feat("):
        return "Added"
    if subject.startswith("fix") or subject.startswith("fix:") or subject.startswith("fix("):
        return "Fixed"
    if subject.startswith("refactor") or subject.startswith("refactor:"):
        return "Changed"
    if subject.startswith("chore") and "remove" in text:
        return "Removed"
    # Keyword scan
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if f"{kw}:" in text or f"{kw}(" in text or f" {kw} " in text or text.startswith(kw):
                return cat
    # Also check for "BREAKING CHANGE"
    if "breaking" in text and "change" in text:
        return "Changed"
    return "Changed"  # default

def format_entry(hash_, subject):
    # Strip conventional prefix for cleaner display
    cleaned = re.sub(r'^(feat|fix|refactor|chore|docs|style|test|perf|ci|build)\(?[^)]*\)?:\s*', '', subject, flags=re.I)
    return f"- {cleaned} ({hash_})"

def generate(since="", output="CHANGELOG.md", title="Changelog"):
    commits = get_commits(since)
    if not commits:
        print("No commits found."); return
    sections = {cat: [] for cat in CATEGORIES}
    for h, s, b in commits:
        cat = categorize(s, b)
        sections[cat].append(format_entry(h, s))
    # Build markdown
    lines = [f"# {title}", "", f"Generated on {datetime.now().strftime('%Y-%m-%d')}", ""]
    total = 0
    for cat, entries in sections.items():
        if not entries: continue
        total += len(entries)
        lines.append(f"## {cat}")
        lines.append("")
        lines.extend(entries)
        lines.append("")
    if total == 0:
        lines.append("*No changes found.*")
    md = "\n".join(lines)
    if output == "-":
        print(md)
    else:
        with open(output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Wrote {total} entries → {output}")

if __name__ == "__main__":
    since = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    # If no since arg, try last tag
    if not since:
        try:
            tags = run("git tag --sort=-creatordate").split("\n")
            if tags and tags[0]:
                since = tags[0]
                print(f"  Using last tag: {since}")
        except Exception: pass
    generate(since, out)
