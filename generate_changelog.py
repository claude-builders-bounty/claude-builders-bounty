#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Complies with Keep a Changelog (https://keepachangelog.com/) and Conventional Commits.
"""

import os
import subprocess
import sys
import re
from datetime import datetime

CATEGORIES = {
    "Added": ["feat", "add", "new", "feature"],
    "Fixed": ["fix", "bug", "patch"],
    "Changed": ["refactor", "perf", "update", "change", "chore", "style", "build", "ci"],
    "Removed": ["remove", "deprecate", "delete", "drop"]
}

def get_git_bin():
    import shutil
    found = shutil.which("git")
    if found:
        return found
    fallback = r"C:\Users\hfauz\.gemini\antigravity\scratch\git\cmd\git.exe"
    if os.path.exists(fallback):
        return fallback
    return "git"

def run_git_cmd(cmd):
    git_bin = get_git_bin()
    if cmd and cmd[0] == "git":
        cmd[0] = git_bin
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_latest_tag():
    # Returns latest tag or empty string if no tags
    return run_git_cmd(["git", "describe", "--tags", "--abbrev=0"])

def get_commits_since_tag(tag=""):
    git_range = f"{tag}..HEAD" if tag else "HEAD"
    # Format: hash | author | date | subject
    raw_logs = run_git_cmd(["git", "log", git_range, "--pretty=format:%h|%an|%ad|%s", "--date=short"])
    if not raw_logs:
        return []

    commits = []
    for line in raw_logs.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "date": parts[2],
                "subject": parts[3].strip()
            })
    return commits

def parse_conventional_commit(subject):
    # Matches type(scope)?: message or type: message
    match = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?:\s*(.+)$", subject)
    if match:
        c_type = match.group(1).lower()
        scope = match.group(2)
        desc = match.group(3)
        return c_type, scope, desc
    return None, None, subject

def categorize_commits(commits):
    buckets = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        subj = c["subject"]
        if subj.startswith("Merge ") or subj.startswith("Merge pull request") or subj.startswith("Merge branch"):
            continue

        c_type, scope, desc = parse_conventional_commit(subj)
        categorized = False

        if c_type:
            for cat, triggers in CATEGORIES.items():
                if c_type in triggers:
                    formatted = f"**{scope}**: {desc}" if scope else desc
                    buckets[cat].append(f"{formatted} ([{c['hash']}])")
                    categorized = True
                    break

        if not categorized:
            # Fallback to simple keyword heuristics
            lower_s = subj.lower()
            if any(k in lower_s for k in ["fix", "bug", "issue", "resolve"]):
                buckets["Fixed"].append(f"{subj} ([{c['hash']}])")
            elif any(k in lower_s for k in ["add", "new", "feat", "support"]):
                buckets["Added"].append(f"{subj} ([{c['hash']}])")
            elif any(k in lower_s for k in ["remove", "deprecat", "delete"]):
                buckets["Removed"].append(f"{subj} ([{c['hash']}])")
            else:
                buckets["Changed"].append(f"{subj} ([{c['hash']}])")

    return buckets

def generate_markdown(buckets, version="Unreleased"):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"## [{version}] - {today}",
        ""
    ]

    has_entries = False
    for cat in ["Added", "Changed", "Fixed", "Removed"]:
        items = buckets[cat]
        if items:
            has_entries = True
            lines.append(f"### {cat}")
            for it in items:
                lines.append(f"- {it}")
            lines.append("")

    if not has_entries:
        lines.append("- No documented changes since last release.")
        lines.append("")

    return "\n".join(lines)

def main():
    latest_tag = get_latest_tag()
    target_version = "Unreleased" if not latest_tag else f"Next ({latest_tag}..HEAD)"
    
    commits = get_commits_since_tag(latest_tag)
    if not commits:
        print("[!] No new commits found since last tag/initial commit.")
        sys.exit(0)

    print(f"[*] Found {len(commits)} commits to process (since: {latest_tag or 'initial commit'}).")
    buckets = categorize_commits(commits)
    changelog_snippet = generate_markdown(buckets, target_version)

    # Prepend or create CHANGELOG.md
    output_file = "CHANGELOG.md"
    existing_content = ""
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

    # Idempotent replacement: if an [Unreleased] block already exists at the top, replace it
    unreleased_pattern = r"## \[(?:Unreleased|Next)[^\]]*\] - \d{4}-\d{2}-\d{2}[\s\S]*?(?=(## \[|$))"
    if re.search(unreleased_pattern, existing_content):
        new_content = re.sub(unreleased_pattern, changelog_snippet + "\n", existing_content, count=1)
    elif "# Changelog" in existing_content:
        parts = existing_content.split("# Changelog\n\n", 1)
        new_content = f"# Changelog\n\n{changelog_snippet}\n" + (parts[1] if len(parts) > 1 else "")
    else:
        new_content = f"# Changelog\n\n{changelog_snippet}\n\n" + existing_content

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[+] Successfully updated {output_file}!")
    print("\nGenerated Changelog Preview:\n")
    print(changelog_snippet)

if __name__ == "__main__":
    main()
