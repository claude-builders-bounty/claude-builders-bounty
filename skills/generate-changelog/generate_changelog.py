#!/usr/bin/env python3
"""
Cross-platform Changelog Generator
Extracts git history and updates CHANGELOG.md adhering to Keep-a-Changelog.
"""

import os
import sys
import re
import subprocess
from datetime import datetime


def get_git_output(cmd_args: list) -> str:
    try:
        res = subprocess.run(["git"] + cmd_args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    latest_tag = get_git_output(["describe", "--tags", "--abbrev=0"])
    
    if latest_tag:
        commit_range = f"{latest_tag}..HEAD"
        release_title = f"[Unreleased] - {today} (since {latest_tag})"
    else:
        commit_range = "HEAD"
        release_title = f"[v0.1.0] - {today}"

    raw_log = get_git_output(["log", "--oneline", "--no-merges", commit_range])
    if not raw_log:
        print("No new commits found.")
        return

    added, fixed, changed, removed = [], [], [], []

    for line in raw_log.splitlines():
        if not line.strip():
            continue
        parts = line.strip().split(" ", 1)
        commit_hash = parts[0]
        msg = parts[1] if len(parts) > 1 else ""

        lmsg = msg.lower()
        if re.match(r"^(feat|add|feature|new)(\(.*\))?:", lmsg):
            clean = re.sub(r"^(feat|add|feature|new)(\(.*\))?:\s*", "", msg, flags=re.I)
            added.append(f"- {clean} (`{commit_hash}`)")
        elif re.match(r"^(fix|bug|patch|resolve)(\(.*\))?:", lmsg):
            clean = re.sub(r"^(fix|bug|patch|resolve)(\(.*\))?:\s*", "", msg, flags=re.I)
            fixed.append(f"- {clean} (`{commit_hash}`)")
        elif re.match(r"^(remove|deprecate|delete|rm)(\(.*\))?:", lmsg):
            clean = re.sub(r"^(remove|deprecate|delete|rm)(\(.*\))?:\s*", "", msg, flags=re.I)
            removed.append(f"- {clean} (`{commit_hash}`)")
        else:
            changed.append(f"- {msg} (`{commit_hash}`)")

    section_lines = [f"## {release_title}\n"]
    if added:
        section_lines.append("### Added\n" + "\n".join(added) + "\n")
    if fixed:
        section_lines.append("### Fixed\n" + "\n".join(fixed) + "\n")
    if changed:
        section_lines.append("### Changed\n" + "\n".join(changed) + "\n")
    if removed:
        section_lines.append("### Removed\n" + "\n".join(removed) + "\n")

    new_section = "\n".join(section_lines)

    target_file = "CHANGELOG.md"
    existing_content = ""
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Skip top 4 header lines if present
            if len(lines) > 4 and lines[0].startswith("# Changelog"):
                existing_content = "".join(lines[4:]).strip()
            else:
                existing_content = "".join(lines).strip()

    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    )

    final_content = header + new_section.strip() + "\n\n" + existing_content
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(final_content.strip() + "\n")

    print(f"✅ Successfully generated {target_file}")


if __name__ == "__main__":
    main()
