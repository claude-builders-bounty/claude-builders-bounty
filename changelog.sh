#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history.

Usage:
    python3 changelog.sh                    # auto from last tag (or last 30 days)
    python3 changelog.sh --since v1.0.0
    python3 changelog.sh --output CHANGELOG.md
"""

import subprocess, sys, re, os
from datetime import datetime, timedelta
from collections import OrderedDict

SECTIONS = OrderedDict([
    ("feat", ("Added", "🚀 Added")),
    ("fix", ("Fixed", "🐛 Fixed")),
    ("changed", ("Changed", "🔄 Changed")),
    ("refactor", ("Refactored", "♻️ Refactored")),
    ("perf", ("Performance", "⚡ Performance")),
    ("docs", ("Documentation", "📚 Documentation")),
    ("test", ("Tests", "🧪 Tests")),
    ("chore", ("Maintenance", "🔧 Maintenance")),
    ("ci", ("CI/CD", "👷 CI/CD")),
    ("revert", ("Reverted", "⏪ Reverted")),
    ("removed", ("Removed", "🗑️ Removed")),
    ("security", ("Security", "🔒 Security")),
])

PREFIX_MAP = {
    "feat": "feat", "feature": "feat", "add": "feat",
    "fix": "fix", "bugfix": "fix", "hotfix": "fix",
    "refactor": "refactor", "refact": "refactor",
    "perf": "perf", "performance": "perf", "speed": "perf",
    "docs": "docs", "doc": "docs", "documentation": "docs",
    "test": "test", "tests": "test",
    "chore": "chore",
    "ci": "ci",
    "revert": "revert", "revert": "revert",
    "remove": "removed", "delete": "removed", "drop": "removed",
    "security": "security", "sec": "security",
}


def run_git(*args):
    try:
        return subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_last_tag():
    tag = run_git("describe", "--tags", "--abbrev=0")
    if tag and tag != "fatal:" and not tag.startswith("fatal"):
        return tag
    return None


def get_commits(since_ref=None):
    cmd = ["log", "--oneline", "--format=%H|%ai|%s", "--no-merges"]
    if since_ref:
        cmd += [f"{since_ref}..HEAD"]
    else:
        since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cmd += [f"--since={since}"]

    output = run_git(*cmd)
    if not output:
        return []

    commits = []
    for line in output.strip().split("\n"):
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0][:7], "date": parts[1], "subject": parts[2]})
    return commits


def classify(commits):
    """Classify commits into sections."""
    categories = OrderedDict((k, []) for k in SECTIONS)
    others = []

    for c in commits:
        subject = c["subject"]
        match = re.match(r"^(\w+)\s*(?:\(([^)]*)\))?[:\!]?\s*(.*)", subject)
        if match:
            prefix = match.group(1).lower()
            scope = match.group(2) or ""
            message = match.group(3) or subject
            mapped = PREFIX_MAP.get(prefix, PREFIX_MAP.get(prefix.rstrip("s"), None))
            if mapped and mapped in categories:
                line = f"{c['hash']}" + (f" *({scope}):*" if scope else ":") + f" {message}"
                categories[mapped].append(line)
                continue

        # Try "Added"/"Fixed"/"Changed" style
        for key, prefixes in [("feat", ["add", "new", "implement"]),
                              ("fix", ["fix", "correct", "prevent"]),
                              ("changed", ["change", "update", "upgrade"])]:
            if any(subject.lower().startswith(p) for p in prefixes):
                categories[key].append(f"{c['hash']}: {subject}")
                break
        else:
            others.append(f"{c['hash']}: {subject}")

    return categories, others


def format_changelog(commits, categories, others, tag_info):
    lines = []
    lines.append("# Changelog\n")

    if tag_info:
        tag, timestamp = tag_info
        lines.append(f"## [{tag}] - {timestamp[:10] if timestamp else 'Unreleased'}\n")
    else:
        lines.append("## [Unreleased]\n")

    any_content = False
    for key, (section_id, section_title) in SECTIONS.items():
        items = categories.get(key, [])
        if items:
            any_content = True
            lines.append(f"### {section_title}\n")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    if others:
        any_content = True
        lines.append("### 📦 Other\n")
        for item in others:
            lines.append(f"- {item}")
        lines.append("")

    if not any_content:
        lines.append("_No significant changes._\n")

    total = len(commits)
    lines.append("---\n")
    lines.append(f"*{total} commit{'s' if total != 1 else ''}*\n")

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    output_file = None
    since_ref = None
    to_stdout = False

    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            output_file = args[i + 1]
        elif a in ("--stdout",):
            to_stdout = True
        elif a.startswith("--since="):
            since_ref = a.split("=", 1)[1]
        elif a.startswith("--since"):
            if i + 1 < len(args):
                since_ref = args[i + 1]
        elif a in ("--help", "-h"):
            print(__doc__)
            return

    if not since_ref:
        tag = get_last_tag()
        if tag:
            since_ref = tag
        # otherwise None — will fall back to 30 days

    commits = get_commits(since_ref)
    if not commits:
        print("No commits found.")
        return

    categories, others = classify(commits)

    tag_info = None
    if since_ref:
        tag_date = run_git("log", "-1", "--format=%ai", since_ref)
        tag_info = (since_ref, tag_date)

    changelog = format_changelog(commits, categories, others, tag_info)

    if output_file:
        # Check if there's an existing CHANGELOG to prepend
        old = ""
        if os.path.exists(output_file):
            with open(output_file) as f:
                old = f.read()
            # Keep entries before the first ## heading (header area)
            parts = re.split(r"^## ", old, maxsplit=1, flags=re.MULTILINE)
            header = parts[0] if len(parts) > 1 else ""
            old_entries = ("## " + parts[1]) if len(parts) > 1 else parts[0] if parts else ""
            changelog = changelog + "\n\n" + old_entries if old_entries else changelog

        with open(output_file, "w") as f:
            f.write(changelog)
        print(f"✅ Written to {output_file}")
    elif to_stdout:
        print(changelog)
    else:
        print(changelog)

    # Show sample output notice
    print(f"\n# Sample output from {run_git('log','-1','--format=%H')[:7] or 'HEAD'} — {len(commits)} commits")


if __name__ == "__main__":
    main()
