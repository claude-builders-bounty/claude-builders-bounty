#!/usr/bin/env python3
"""generate_changelog.py — Structured CHANGELOG.md Generator

A zero-dependency Python script that generates a structured CHANGELOG.md
from a project's git history using conventional commits.

Usage:
  python scripts/generate_changelog.py              # output to CHANGELOG.md
  python scripts/generate_changelog.py --stdout      # print to stdout
"""
import subprocess, sys, os, re
from datetime import date
from collections import defaultdict

CATEGORIES = [
    ("Added", "🚀"),
    ("Fixed", "🐛"),
    ("Changed", "🔧"),
    ("Removed", "🔥"),
    ("Documentation", "📖"),
    ("Performance", "⚡"),
    ("Testing", "🧪"),
    ("Security", "🔒"),
    ("Dependencies", "📦"),
    ("Miscellaneous", "🔮"),
]

CONVENTIONAL_MAP = {
    "feat": "Added", "feature": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed",
    "refactor": "Changed", "style": "Changed", "chore": "Changed",
    "docs": "Documentation", "documentation": "Documentation",
    "perf": "Performance", "performance": "Performance",
    "test": "Testing", "testing": "Testing",
    "security": "Security",
    "deps": "Dependencies", "dependencies": "Dependencies",
    "build": "Dependencies", "ci": "Dependencies",
    "revert": "Removed", "remove": "Removed",
    "deprecate": "Removed", "delete": "Removed",
}

def parse_conventional_commit(msg):
    m = re.match(r"^([a-zA-Z_-]+)(\([^)]*\))?!?\s*:\s*(.*)", msg.strip())
    if not m:
        return "Miscellaneous", msg.strip()
    ctype, scope, desc = m.group(1), m.group(2) or "", m.group(3).strip()
    cat = CONVENTIONAL_MAP.get(ctype, "Miscellaneous")
    if scope:
        desc = f"**{scope.strip('()')}:** {desc}"
    return cat, desc

def get_latest_tag():
    try:
        r = subprocess.run(["git", "tag", "--sort=-version:refname"],
                          capture_output=True, text=True, check=False)
        tags = [t for t in r.stdout.strip().split("\n") if t]
        return tags[0] if tags else None
    except: return None

def get_commits(range_spec):
    try:
        r = subprocess.run(["git", "log", range_spec, "--format=%s||%h",
                           "--no-merges"], capture_output=True, text=True, check=False)
        entries = [l for l in r.stdout.strip().split("\n") if "||" in l]
        result = []
        for e in entries:
            msg, sha = e.split("||", 1)
            result.append((msg.strip(), sha.strip()[:7]))
        return result
    except: return []

def generate_changelog(output_file=None, no_emoji=False):
    tag = get_latest_tag()
    if tag:
        commits = get_commits(f"{tag}..HEAD")
        base_ref = tag
    else:
        commits = get_commits("HEAD")
        base_ref = "initial"

    groups = defaultdict(list)
    for msg, sha in commits:
        cat, desc = parse_conventional_commit(msg)
        groups[cat].append((desc, sha))

    lines = []
    lines.append("# Changelog\n")
    lines.append("## [Unreleased]\n")
    if tag:
        lines.append(f"## [{tag}] - {date.today().isoformat()}\n")

    counter = 0
    for cat_name, emoji in CATEGORIES:
        items = groups.get(cat_name, [])
        if not items: continue
        counter += len(items)
        icon = f"{emoji} " if not no_emoji else ""
        lines.append(f"### {icon}{cat_name}\n")
        for desc, sha in items:
            lines.append(f"- {desc} (`{sha}`)")
        lines.append("")

    if counter == 0:
        lines.append("_No changes_\n")

    output = "\n".join(lines)

    if output_file:
        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(output)
            f.write("\n")
        print(f"[✓] CHANGELOG generated: {output_file}")
        print(f"    {counter} change(s) since {base_ref}")
    else:
        print(output)

def main():
    import argparse
    p = argparse.ArgumentParser(description="Generate structured CHANGELOG.md")
    p.add_argument("--stdout", action="store_true", help="Print to stdout")
    p.add_argument("--no-emoji", action="store_true", help="Disable emoji icons")
    p.add_argument("--output", default="CHANGELOG.md", help="Output file")
    args = p.parse_args()
    generate_changelog(None if args.stdout else args.output, args.no_emoji)

if __name__ == "__main__":
    main()
