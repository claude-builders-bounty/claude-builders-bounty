#!/usr/bin/env python3
import subprocess
import sys
import re
from datetime import datetime

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_latest_tag():
    try:
        return run_command(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None

def get_commits(since_tag=None):
    if since_tag:
        range_spec = f"{since_tag}..HEAD"
    else:
        range_spec = "HEAD"
    
    # Format: hash|date|subject
    log_format = "%H|%ai|%s"
    cmd = ["git", "log", range_spec, f"--format={log_format}"]
    output = run_command(cmd)
    
    if not output:
        return []
    
    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0],
                "date": parts[1],
                "subject": parts[2]
            })
    return commits

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Docs": [],
        "Other": []
    }
    
    patterns = {
        "Added": r"^(feat|add|new):",
        "Fixed": r"^(fix|bugfix):",
        "Changed": r"^(refactor|update|perf|change):",
        "Removed": r"^(remove|delete|deprecate):",
        "Docs": r"^(docs|readme):"
    }
    
    for commit in commits:
        subject = commit["subject"].lower()
        matched = False
        for cat, pattern in patterns.items():
            if re.match(pattern, subject):
                categories[cat].append(commit)
                matched = True
                break
        if not matched:
            categories["Other"].append(commit)
            
    return categories

def determine_version_bump(categories):
    """Suggests a SemVer bump based on commit history."""
    has_feat = len(categories["Added"]) > 0
    has_fix = len(categories["Fixed"]) > 0
    
    # Check for breaking changes in any category
    has_breaking = False
    for cat in categories.values():
        for commit in cat:
            if "!" in commit["subject"].split(":")[0] or "breaking change" in commit["subject"].lower():
                has_breaking = True
                break
                
    if has_breaking: return "MAJOR"
    if has_feat: return "MINOR"
    if has_fix: return "PATCH"
    return "NONE"

def generate_markdown(categories, tag_name=None):
    now = datetime.now().strftime("%Y-%m-%d")
    version = tag_name if tag_name else "Unreleased"
    bump = determine_version_bump(categories)
    
    lines = [f"# CHANGELOG", f"\n## [{version}] - {now}"]
    if bump != "NONE":
        lines.append(f"> **💡 Suggested Version Bump:** {bump}")
        
    for cat, items in categories.items():
        if items:
            lines.append(f"\n### {cat}")
            for item in items:
                short_hash = item["hash"][:7]
                lines.append(f"- {item['subject']} ({short_hash})")
                
    return "\n".join(lines)

def main():
    try:
        latest_tag = get_latest_tag()
        commits = get_commits(latest_tag)
        
        if not commits:
            print("No new commits found since last tag.")
            return

        categories = categorize_commits(commits)
        markdown = generate_markdown(categories, "v" + datetime.now().strftime("%Y.%m.%d") if not latest_tag else None)
        
        output_file = "CHANGELOG.md"
        with open(output_file, "w") as f:
            f.write(markdown)
            
        print(f"Successfully generated {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
