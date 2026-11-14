#!/usr/bin/env python3
"""
generate_changelog.py
Automatically generates a structured CHANGELOG.md from project git history.
Categorizes commits into Added / Fixed / Changed / Removed.
"""

import sys
import os
import subprocess
import re
from datetime import datetime
from collections import defaultdict

CATEGORIES = {
    "Added": [r"^feat(\(.*\))?:", r"^add(\(.*\))?:", r"\badd(ed|ing)?\b", r"\bnew\b", r"\bcreate(d)?\b"],
    "Fixed": [r"^fix(\(.*\))?:", r"^bug(\(.*\))?:", r"^hotfix(\(.*\))?:", r"^patch(\(.*\))?:", r"\bfix(ed|es)?\b", r"\bresolve(d|s)?\b"],
    "Removed": [r"^remove(\(.*\))?:", r"^delete(\(.*\))?:", r"^deprecate(\(.*\))?:", r"\bremove(d)?\b", r"\bdeprecat(ed|ion)\b"],
    "Changed": [r"^refactor(\(.*\))?:", r"^perf(\(.*\))?:", r"^docs(\(.*\))?:", r"^style(\(.*\))?:", r"^chore(\(.*\))?:", r"^build(\(.*\))?:", r"^ci(\(.*\))?:", r"\bupdate(d)?\b", r"\bchange(d)?\b", r"\brefactor(ed)?\b"]
}

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_latest_tag():
    tag = run_cmd(["git", "describe", "--tags", "--abbrev=0"])
    if not tag:
        tags = run_cmd(["git", "tag", "--sort=-creatordate"])
        if tags:
            tag = tags.splitlines()[0].strip()
    return tag

def get_commits_since_tag(tag):
    if tag:
        log_range = f"{tag}..HEAD"
        print(f"[*] Fetching commits since latest tag: {tag} ({log_range})")
    else:
        log_range = "HEAD"
        print("[*] No git tag found. Fetching all commits in repository history.")

    cmd = ["git", "log", log_range, "--pretty=format:%h%x09%s%x09%an"]
    raw_log = run_cmd(cmd)
    if not raw_log:
        return []

    commits = []
    for line in raw_log.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            sha = parts[0]
            subject = parts[1]
            author = parts[2] if len(parts) > 2 else "Unknown"
            commits.append({"sha": sha, "subject": subject, "author": author})
    return commits

def clean_subject(subject):
    cleaned = re.sub(r"^(feat|fix|refactor|perf|docs|chore|style|build|ci|add|remove)(\([^\)]+\))?!?:?\s*", "", subject, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned or subject

def categorize_commits(commits):
    categorized = defaultdict(list)
    for c in commits:
        subject = c["subject"]
        matched_cat = None
        for cat, patterns in CATEGORIES.items():
            for pat in patterns:
                if re.search(pat, subject, re.IGNORECASE):
                    matched_cat = cat
                    break
            if matched_cat:
                break
        
        if not matched_cat:
            matched_cat = "Changed"

        entry = f"{clean_subject(subject)} (`{c['sha']}` by @{c['author']})"
        categorized[matched_cat].append(entry)
    return categorized

def generate_markdown(categorized, tag_name="Unreleased"):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## [{tag_name}] - {today}\n"]

    order = ["Added", "Fixed", "Changed", "Removed"]
    has_entries = False
    for cat in order:
        if categorized.get(cat):
            has_entries = True
            lines.append(f"### {cat}")
            for item in categorized[cat]:
                lines.append(f"- {item}")
            lines.append("")

    if not has_entries:
        lines.append("*No notable changes in this release.*\n")

    return "\n".join(lines).strip() + "\n"

def update_changelog_file(new_section, output_path="CHANGELOG.md"):
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if content.startswith("# Changelog"):
            first_section_idx = content.find("## [")
            if first_section_idx != -1:
                updated_content = content[:first_section_idx] + new_section + "\n" + content[first_section_idx:]
            else:
                updated_content = content.rstrip() + "\n\n" + new_section
        else:
            updated_content = header + new_section + "\n" + content
    else:
        updated_content = header + new_section

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"[✔] Successfully updated {output_path}")

def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)
    
    if not commits:
        print("[!] No new commits found to generate changelog.")
        return

    print(f"[*] Found {len(commits)} commits to process.")
    categorized = categorize_commits(commits)
    section = generate_markdown(categorized)
    update_changelog_file(section, target_file)

if __name__ == "__main__":
    main()
