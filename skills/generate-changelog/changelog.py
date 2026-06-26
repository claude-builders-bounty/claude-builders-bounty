#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history since the last tag."""

import subprocess
import sys
from datetime import date
from pathlib import Path


CATEGORIES = {
    "Added":   ["add", "feat", "new", "implement", "introduce", "create", "support"],
    "Fixed":   ["fix", "bug", "patch", "resolve", "correct", "repair", "revert"],
    "Changed": ["update", "change", "refactor", "improve", "perf", "optimis", "optimiz",
                "bump", "upgrade", "tweak", "adjust", "move", "rename", "migrate"],
    "Removed": ["remove", "delete", "drop", "deprecate", "disable", "eliminate"],
}

CONVENTIONAL = {
    "feat":     "Added",
    "fix":      "Fixed",
    "perf":     "Changed",
    "refactor": "Changed",
    "chore":    "Changed",
    "docs":     "Changed",
    "style":    "Changed",
    "revert":   "Fixed",
    "remove":   "Removed",
    "drop":     "Removed",
}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def get_latest_tag(repo):
    return run(["git", "describe", "--tags", "--abbrev=0"], cwd=repo)


def get_commits_since(repo, tag):
    ref = f"{tag}..HEAD" if tag else "HEAD"
    out = run(["git", "log", ref, "--no-merges", "--format=%H%x00%s%x00%an%x00%ad", "--date=short"], cwd=repo)
    if not out:
        return []
    entries = []
    for line in out.splitlines():
        parts = line.split("\x00", 3)
        if len(parts) == 4:
            entries.append({"sha": parts[0][:7], "subject": parts[1],
                            "author": parts[2], "date": parts[3]})
    return entries


def categorize(subject):
    s = subject.lower().strip()

    # Conventional commit prefix: "feat(scope): description" or "feat: description"
    if ":" in s:
        prefix = s.split(":")[0].split("(")[0].strip()
        if prefix in CONVENTIONAL:
            return CONVENTIONAL[prefix]

    for cat, keywords in CATEGORIES.items():
        if any(s.startswith(kw) or f" {kw}" in s for kw in keywords):
            return cat

    return "Changed"  # default bucket


def build_changelog(repo_path, output_path=None):
    repo = Path(repo_path).resolve()
    if not (repo / ".git").is_dir():
        print(f"Error: {repo} is not a git repository", file=sys.stderr)
        sys.exit(1)

    tag = get_latest_tag(repo)
    commits = get_commits_since(repo, tag)

    if not commits:
        print("No commits found since last tag (or no commits at all).", file=sys.stderr)
        sys.exit(0)

    # Bucket commits
    buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for c in commits:
        cat = categorize(c["subject"])
        buckets[cat].append(c)

    # Determine version header
    version = "Unreleased"
    since_label = f"since `{tag}`" if tag else "all commits (no tags found)"

    lines = []
    lines.append(f"# Changelog\n")
    lines.append(f"## [{version}] — {date.today().isoformat()}\n")
    lines.append(f"*Changes {since_label}*\n")

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = buckets[cat]
        if not items:
            continue
        lines.append(f"\n### {cat}\n")
        for c in items:
            lines.append(f"- {c['subject']}  (`{c['sha']}` — {c['date']})")

    lines.append("")
    content = "\n".join(lines)

    out = Path(output_path) if output_path else repo / "CHANGELOG.md"
    out.write_text(content)
    print(f"Written: {out}")
    print(f"  {len(commits)} commits categorized across {sum(len(v) for v in buckets.values() if v)} entries")
    if tag:
        print(f"  Since tag: {tag}")
    for cat, items in buckets.items():
        if items:
            print(f"  {cat}: {len(items)}")
    return content


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("repo", nargs="?", default=".", help="Path to git repo (default: .)")
    p.add_argument("-o", "--output", default=None, help="Output file (default: CHANGELOG.md in repo)")
    p.add_argument("--preview", action="store_true", help="Print to stdout instead of writing file")
    args = p.parse_args()

    if args.preview:
        content = build_changelog(args.repo, "/dev/stdout")
    else:
        build_changelog(args.repo, args.output)
