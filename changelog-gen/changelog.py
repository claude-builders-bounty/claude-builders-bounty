#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Auto-categorizes commits into Added/Fixed/Changed/Removed sections
based on Conventional Commits prefixes.

Usage:
    python3 changelog.py
    python3 changelog.py --since v1.0.0
    python3 changelog.py --output RELEASE_NOTES.md
"""

import subprocess
import re
import sys
from datetime import datetime
from pathlib import Path

CATEGORY_MAP = {
    "feat": "Added", "add": "Added", "new": "Added",
    "fix": "Fixed", "bug": "Fixed", "hotfix": "Fixed",
    "change": "Changed", "refactor": "Changed", "perf": "Changed",
    "remove": "Removed", "revert": "Removed", "drop": "Removed",
}
DEFAULT_CATEGORY = "Changed"

def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ""

def get_last_tag() -> str | None:
    tag = run(["git", "describe", "--tags", "--abbrev=0"]).strip()
    return tag if tag else None

def get_commits_since(tag: str | None) -> list[tuple[str, str]]:
    range_spec = f"{tag}..HEAD" if tag else ""
    fmt = "--format=%H%x00%s"
    output = run(["git", "log", range_spec, fmt, "--no-merges"])
    commits = []
    for block in output.strip().split("\n"):
        if "\x00" in block:
            sha, msg = block.split("\x00", 1)
            commits.append((sha, msg.strip()))
    return commits

def categorize(message: str) -> str:
    match = re.match(r"^(?:\w+)(?:\(.*?\))?[:!]\s", message)
    if match:
        prefix = match.group(0).rstrip(":!").rstrip(")").split("(")[0].lower()
        return CATEGORY_MAP.get(prefix, DEFAULT_CATEGORY)
    return DEFAULT_CATEGORY

def clean_message(message: str) -> str:
    return re.sub(r"^(?:\w+)(?:\(.*?\))?[:!]\s+", "", message, count=1)

def generate(tag: str | None = None, since: str | None = None) -> str:
    if since:
        tag = since
    elif tag is None:
        tag = get_last_tag()
    commits = get_commits_since(tag)
    sections: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for sha, msg in commits:
        cat = categorize(msg)
        clean = clean_message(msg)
        if not clean:
            clean = msg
        short = sha[:7]
        sections[cat].append(f"- {clean} ({short})")
    tag_label = tag if tag else "Unreleased"
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Changelog\n\n## [{tag_label}] - {today}\n"]
    for section_name in ["Added", "Fixed", "Changed", "Removed"]:
        items = sections[section_name]
        if items:
            lines.append(f"\n### {section_name}\n")
            lines.extend(f"{item}\n" for item in items)
    return "".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since", help="Starting tag or commit ref")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file path")
    args = parser.parse_args()
    output = generate(since=args.since)
    Path(args.output).write_text(output, encoding="utf-8")
    print(output)
    print(f"\nWrote {len(output)} bytes to {args.output}")

if __name__ == "__main__":
    main()
