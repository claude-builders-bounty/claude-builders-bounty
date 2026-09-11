#!/usr/bin/env python3
"""
Automated Structured CHANGELOG Generator
Extracts git history since the latest tag, categorizes by Conventional Commits,
and formats into Keep a Changelog standard Markdown.
"""

import subprocess
import sys
import os
import re
from datetime import date

def run_git(args, cwd=None):
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        return None

def get_latest_tag(cwd=None):
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    return tag

def get_commits_since_tag(latest_tag=None, cwd=None):
    if latest_tag:
        rev_range = f"{latest_tag}..HEAD"
    else:
        rev_range = "HEAD"

    log_format = "%h|%an|%s"
    output = run_git(["log", f"--format={log_format}", rev_range], cwd=cwd)
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "message": parts[2].strip()
            })
    return commits

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        msg = c["message"]
        # Match conventional commit patterns: feat:, fix:, refactor:, chore:, etc.
        m = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?!?:?\s*(.+)$", msg)
        if m:
            prefix = m.group(1).lower()
            scope = m.group(2)
            content = m.group(3)
            formatted = f"**{scope}**: {content}" if scope else content
            formatted_entry = f"{formatted} ([`{c['hash']}`])"

            if prefix in ["feat", "feature", "add"]:
                categories["Added"].append(formatted_entry)
            elif prefix in ["fix", "bug", "patch"]:
                categories["Fixed"].append(formatted_entry)
            elif prefix in ["remove", "deprecate", "drop"]:
                categories["Removed"].append(formatted_entry)
            else: # refactor, perf, docs, style, chore
                categories["Changed"].append(formatted_entry)
        else:
            # Fallback based on keywords
            lower = msg.lower()
            formatted_entry = f"{msg} ([`{c['hash']}`])"
            if any(w in lower for w in ["add", "feat", "new", "implement"]):
                categories["Added"].append(formatted_entry)
            elif any(w in lower for w in ["fix", "bug", "patch", "resolve"]):
                categories["Fixed"].append(formatted_entry)
            elif any(w in lower for w in ["remove", "delete", "deprecate"]):
                categories["Removed"].append(formatted_entry)
            else:
                categories["Changed"].append(formatted_entry)

    return categories

def build_changelog_markdown(categories, version="Unreleased", release_date=None):
    today = release_date or date.today().isoformat()
    lines = [f"## [{version}] - {today}"]

    has_content = False
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat]
        if items:
            has_content = True
            lines.append(f"\n### {cat}")
            for item in items:
                lines.append(f"- {item}")

    if not has_content:
        lines.append("\n- No significant user-facing changes recorded.")

    return "\n".join(lines) + "\n"

def update_changelog_file(new_section, file_path="CHANGELOG.md"):
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    existing_content = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # Remove existing header if present
    existing_body = re.sub(r"^# Changelog\s+.*?\n\n", "", existing_content, flags=re.DOTALL)

    full_output = header + new_section + "\n" + existing_body.strip() + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_output)
    return full_output

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    output_file = os.path.join(target_dir, "CHANGELOG.md")

    latest_tag = get_latest_tag(cwd=target_dir)
    commits = get_commits_since_tag(latest_tag, cwd=target_dir)

    print(f"Generating changelog for repository at: {target_dir}")
    print(f"Latest tag detected: {latest_tag or 'None (parsing from root)'}")
    print(f"Total commits processed: {len(commits)}")

    categories = categorize_commits(commits)
    changelog_section = build_changelog_markdown(categories, version="Unreleased")
    update_changelog_file(changelog_section, output_file)

    print(f"✅ Successfully updated {output_file}!")
    print("\n--- Preview ---\n" + changelog_section)

if __name__ == "__main__":
    main()
