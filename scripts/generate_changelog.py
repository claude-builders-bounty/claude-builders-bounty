#!/usr/bin/env python3
"""
generate_changelog.py — Cross-platform CHANGELOG generator from git history.
Works on Windows, macOS, and Linux without external dependencies.
"""

import subprocess
import datetime
import re
import os
import sys

def get_git_output(args):
    try:
        res = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def generate_changelog(output_path="CHANGELOG.md", target_repo=None):
    # 1. Get last tag
    last_tag = get_git_output(['describe', '--tags', '--abbrev=0'])
    today = datetime.date.today().isoformat()

    if last_tag:
        git_range = f"{last_tag}..HEAD"
        version_header = f"Unreleased (since {last_tag})"
    else:
        git_range = "HEAD"
        version_header = f"Initial Release ({today})"

    # 2. Get commits
    cmd = ['log', git_range, '--pretty=format:%s|%h|%an']
    raw_log = get_git_output(cmd)
    if not raw_log:
        print(f"No commits found in range {git_range}.")
        return

    lines = raw_log.splitlines()
    categories = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }

    for line in lines:
        if '|' not in line:
            continue
        parts = line.split('|', 2)
        if len(parts) < 3:
            continue
        subject, commit_hash, author = parts[0].strip(), parts[1].strip(), parts[2].strip()
        
        # Clean conventional commit prefix
        clean_subject = re.sub(r'^[a-zA-Z]+(\([a-zA-Z0-9_\-]+\))?!?: *', '', subject)
        entry = f"- {clean_subject} (`{commit_hash}`) — @{author}"

        lower = subject.lower()
        if re.match(r'^(feat|add|new)', lower):
            categories['Added'].append(entry)
        elif re.match(r'^(fix|bug|patch|resolve)', lower):
            categories['Fixed'].append(entry)
        elif re.match(r'^(remove|deprecate|delete|drop)', lower):
            categories['Removed'].append(entry)
        else:
            categories['Changed'].append(entry)

    # 3. Build section
    section = [f"## [{version_header}] - {today}\n"]
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            section.append(f"### {cat}")
            section.extend(categories[cat])
            section.append("")

    section_text = "\n".join(section) + "\n"

    # 4. Write/Prepend to file
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
            existing = f.read()
        if existing.startswith("# Changelog"):
            # Insert after header
            parts = existing.split("\n\n", 2)
            if len(parts) >= 2:
                new_content = parts[0] + "\n\n" + parts[1] + "\n\n" + section_text + (parts[2] if len(parts) > 2 else "")
            else:
                new_content = header + section_text + existing
        else:
            new_content = header + section_text + existing
    else:
        new_content = header + section_text

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Generated {output_path} successfully ({len(lines)} commits categorized).")

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    generate_changelog(out)
