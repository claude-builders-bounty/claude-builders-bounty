import os
import subprocess
import re
import argparse
import sys
from datetime import datetime

CATEGORIES = {
    "Added": ["feat", "add", "new"],
    "Fixed": ["fix", "bug", "patch", "resolved"],
    "Changed": ["refactor", "perf", "update", "style", "chore", "build", "ci", "docs"],
    "Removed": ["remove", "deprecate", "drop"]
}

def run_git_command(args):
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def get_latest_tag():
    return run_git_command(["describe", "--tags", "--abbrev=0"])

def get_commits_since_tag(tag=None):
    if tag:
        cmd = ["log", f"{tag}..HEAD", "--pretty=format:%h%x09%s%x09%an%x09%ad", "--date=short"]
    else:
        cmd = ["log", "--pretty=format:%h%x09%s%x09%an%x09%ad", "--date=short"]
    
    output = run_git_command(cmd)
    if not output:
        return []
    
    commits = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    return commits

def categorize_commit(subject):
    match = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?:\s*(.*)$", subject)
    if match:
        c_type, scope, desc = match.groups()
        c_type = c_type.lower()
        formatted_desc = f"**{scope}**: {desc}" if scope else desc
        
        for cat, prefixes in CATEGORIES.items():
            if c_type in prefixes:
                return cat, formatted_desc
        return "Changed", formatted_desc
    
    sub_lower = subject.lower()
    for cat, prefixes in CATEGORIES.items():
        for prefix in prefixes:
            if sub_lower.startswith(prefix):
                return cat, subject
    
    return "Changed", subject

def generate_changelog(version="Unreleased", tag=None):
    latest_tag = tag or get_latest_tag()
    commits = get_commits_since_tag(latest_tag)
    
    categorized = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for c in commits:
        cat, desc = categorize_commit(c["subject"])
        categorized[cat].append(f"- {desc} ([`{c['hash']}`])")
    
    today = datetime.now().strftime("%Y-%m-%d")
    md_lines = [f"## [{version}] - {today}\n"]
    if latest_tag:
        md_lines.append(f"> Changes since tag `{latest_tag}`\n")
    
    has_entries = False
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categorized[cat]
        if items:
            has_entries = True
            md_lines.append(f"### {cat}\n")
            for item in items:
                md_lines.append(item)
            md_lines.append("")
            
    if not has_entries:
        md_lines.append("- No new commit entries recorded.\n")
        
    return "\n".join(md_lines)

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history")
    parser.add_argument("--version", default="Unreleased", help="Version header for changelog")
    parser.add_argument("--tag", default=None, help="Target git tag (defaults to latest tag)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without writing file")
    
    args = parser.parse_args()
    content = generate_changelog(args.version, args.tag)
    
    if args.dry_run:
        print(content)
        return
        
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
    
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing.startswith("# Changelog"):
            parts = existing.split("\n\n", 2)
            if len(parts) >= 3:
                new_changelog = parts[0] + "\n\n" + parts[1] + "\n\n" + content + "\n\n" + parts[2]
            else:
                new_changelog = existing + "\n\n" + content
        else:
            new_changelog = header + content + "\n\n" + existing
    else:
        new_changelog = header + content
        
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(new_changelog)
        
    print(f"SUCCESS: Generated changelog for [{args.version}] into {args.output}")

if __name__ == "__main__":
    main()
