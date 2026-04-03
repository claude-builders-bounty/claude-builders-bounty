#!/usr/bin/env python3
"""
Structured CHANGELOG generator from git history.
Reads git log, categorizes by conventional commit type, outputs markdown.
"""

import subprocess
import sys
import re
from datetime import datetime
from collections import defaultdict

CATEGORIES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "style": "Style",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Tests",
    "build": "Build",
    "ci": "CI/CD",
    "chore": "Chores",
    "revert": "Reverts",
}

BREAKING_LABEL = "BREAKING CHANGES"


def run_git(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"git error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_commits(from_ref=None, to_ref="HEAD"):
    log_format = "%H%n%s%n%b%n---END---"
    args = ["log", f"--format={log_format}"]
    if from_ref:
        args.append(f"{from_ref}..{to_ref}")
    else:
        args.append("--all")

    output = run_git(args)
    if not output:
        return []

    commits = []
    for block in output.split("---END---"):
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        sha = lines[0].strip()
        subject = lines[1].strip()
        body = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""
        commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def parse_commit(commit):
    subject = commit["subject"]
    body = commit["body"]

    # Skip merge commits
    if subject.startswith("Merge "):
        return None

    # Parse conventional commit: type(scope): description
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$", subject)
    if not match:
        return {"type": "chore", "scope": "", "desc": subject, "breaking": False}

    ctype = match.group(1).lower()
    scope = match.group(2) or ""
    desc = match.group(3)
    breaking = "BREAKING CHANGE" in body or desc.endswith("!")

    return {"type": ctype, "scope": scope, "desc": desc, "breaking": breaking}


def get_tag_date(ref="HEAD"):
    try:
        output = run_git(["log", "-1", "--format=%ai", ref])
        return datetime.strptime(output[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def generate_changelog(from_ref=None, to_ref="HEAD"):
    commits = get_commits(from_ref, to_ref)
    if not commits:
        print("No commits found.", file=sys.stderr)
        return "# Changelog\n\nNo changes found.\n"

    parsed = []
    for c in commits:
        p = parse_commit(c)
        if p:
            p["sha"] = c["sha"][:7]
            parsed.append(p)

    grouped = defaultdict(list)
    breaking = []
    for p in parsed:
        if p["breaking"]:
            breaking.append(p)
        cat = CATEGORIES.get(p["type"], "Other")
        grouped[cat].append(p)

    date = get_tag_date(to_ref)
    version = to_ref if to_ref != "HEAD" else "Unreleased"

    lines = [f"# Changelog\n", f"## {version} ({date})\n"]

    if breaking:
        lines.append(f"### {BREAKING_LABEL}\n")
        for b in breaking:
            scope = f"**{b['scope']}**: " if b["scope"] else ""
            lines.append(f"- {scope}{b['desc']} ({b['sha']})")
        lines.append("")

    for cat in CATEGORIES.values():
        items = grouped.get(cat)
        if not items:
            continue
        lines.append(f"### {cat}\n")
        for item in items:
            scope = f"**{item['scope']}**: " if item["scope"] else ""
            lines.append(f"- {scope}{item['desc']} ({item['sha']})")
        lines.append("")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--from", dest="from_ref", help="Starting ref (tag/commit)")
    parser.add_argument("--to", default="HEAD", help="Ending ref (default: HEAD)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    changelog = generate_changelog(args.from_ref, args.to)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog)
        print(f"Changelog written to {args.output}", file=sys.stderr)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
