#!/usr/bin/env python3
"""Generate structured CHANGELOG.md from git history since the last tag."""
import subprocess, sys, re, os
from datetime import datetime, timezone
from collections import defaultdict

CATEGORIES = {
    "Added":    [r"\bfeat\b", r"\badd\b"],
    "Fixed":    [r"\bfix\b", r"\bbug\b", r"\bpatch\b"],
    "Changed":  [r"\bchange\b", r"\bupdate\b", r"\brefactor\b", r"\bperf\b"],
    "Removed":  [r"\bremove\b", r"\bdeprecat\b", r"\bdrop\b"],
}

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def get_latest_tag():
    tags = run("git tag --sort=-creatordate").split("\n")
    return tags[0] if tags and tags[0] else None

def get_commits_since(tag):
    if tag:
        log = run(f'git log {tag}..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short')
    else:
        log = run('git log --pretty=format:"%h|%s|%an|%ad" --date=short')
    commits = []
    for line in log.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append({"hash": parts[0], "subject": parts[1], "author": parts[2], "date": parts[3]})
    return commits

def categorize(subject):
    sl = subject.lower()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, sl):
                return cat
    return "Changed"

def generate(commits, repo_name, tag):
    grouped = defaultdict(list)
    for c in commits:
        cat = categorize(c["subject"])
        grouped[cat].append(c)

    lines = []
    lines.append(f"# Changelog")
    lines.append("")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if tag:
        lines.append(f"## [{today}] — {tag}..HEAD")
    else:
        lines.append(f"## [{today}] — Initial release")
    lines.append("")

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        entries = grouped.get(cat, [])
        if not entries:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        for c in entries:
            msg = c["subject"].strip()
            # Remove conventional commit prefix
            msg = re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", msg)
            lines.append(f"- {msg} ({c['hash'][:7]}, @{c['author']})")
        lines.append("")

    return "\n".join(lines)

def main():
    os.chdir(run("git rev-parse --show-toplevel") if run("git rev-parse --show-toplevel") else ".")
    tag = get_latest_tag()
    commits = get_commits_since(tag)
    if not commits:
        print("No commits found since last tag.")
        sys.exit(0)

    repo = os.path.basename(os.getcwd())
    changelog = generate(commits, repo, tag)

    output_file = "CHANGELOG.md"
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing = f.read()
        # Prepend new content after the header
        header_end = existing.find("\n## ")
        if header_end > 0:
            new_content = existing[:header_end] + "\n" + changelog.split("\n", 2)[-1] + "\n" + existing[header_end:]
        else:
            new_content = changelog + "\n\n" + existing
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(changelog)

    print(changelog)
    print(f":: Written to {output_file}")

if __name__ == "__main__":
    main()