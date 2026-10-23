#!/usr/bin/env python3
"""Generate a structured changelog from Git commits since the nearest tag."""
import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path
import re
import subprocess
import sys

HEADINGS = ("Added", "Fixed", "Changed", "Removed")
PREFIXES = {"feat": "Added", "fix": "Fixed", "perf": "Changed", "refactor": "Changed", "revert": "Removed", "remove": "Removed", "docs": "Changed", "chore": "Changed", "build": "Changed", "ci": "Changed", "test": "Changed", "style": "Changed"}
PATTERN = re.compile(r"^(?P<kind>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?:!)?:\s*(?P<text>.*)$")

def git(*args, cwd=None):
    p = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if p.returncode:
        raise ValueError(p.stderr.strip() or "Git command failed")
    return p.stdout.strip()

def entries(repo):
    git("rev-parse", "--is-inside-work-tree", cwd=repo)
    nearest = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "HEAD"], cwd=repo, text=True, capture_output=True, check=False)
    start = nearest.stdout.strip() if nearest.returncode == 0 else None
    span = f"{start}..HEAD" if start else "HEAD"
    raw = git("log", "--no-merges", "--pretty=format:%h%x1f%s%x1e", span, cwd=repo)
    result = defaultdict(list)
    for item in raw.split("\x1e"):
        if "\x1f" not in item:
            continue
        sha, subject = item.strip().split("\x1f", 1)
        subject = subject.strip().replace("\n", " ")
        if not subject:
            continue
        match = PATTERN.match(subject)
        if match:
            category = PREFIXES.get(match["kind"].lower(), "Changed")
            desc = match["text"].strip() or subject
            if match["scope"]:
                desc = f'{match["scope"]}: {desc}'
        else:
            desc = subject
            category = "Removed" if re.match(r"^(remove|delete|drop)\b", desc, re.I) else "Fixed" if re.match(r"^(fix|repair)\b", desc, re.I) else "Added" if re.match(r"^(add|introduce)\b", desc, re.I) else "Changed"
        result[category].append(f"- {desc} (`{sha}`)")
    return start, result

def render(start, grouped, today=None):
    today = today or date.today().isoformat()
    lines = ["# Changelog", "", "All notable changes since the latest reachable Git tag are listed below.", "", f"## [Unreleased] - {today}", ""]
    if start:
        lines.extend([f"Changes since `{start}`.", ""])
    for heading in HEADINGS:
        if grouped[heading]:
            lines.extend([f"### {heading}", "", *grouped[heading], ""])
    if not any(grouped.values()):
        lines.extend(["No new commits since the latest tag.", ""])
    return "\n".join(lines).rstrip() + "\n"

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path to Git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path within repo or absolute path")
    parser.add_argument("--stdout", action="store_true", help="Preview without writing CHANGELOG.md")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        tag, groups = entries(repo)
        target = Path(args.output)
        if not target.is_absolute():
            target = repo / target
        content = render(tag, groups)
        if args.stdout:
            print(content, end="")
        else:
            target.write_text(content, encoding="utf-8")
            print(f"Wrote {target} ({sum(len(x) for x in groups.values())} commits)")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
