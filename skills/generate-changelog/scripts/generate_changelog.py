import subprocess
import re
import sys
from datetime import datetime
import argparse

def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_last_tag():
    return run_command("git describe --tags --abbrev=0")

def get_commits(since_tag=None):
    if since_tag:
        command = f'git log {since_tag}..HEAD --pretty=format:"%s"'
    else:
        command = 'git log --pretty=format:"%s"'
    
    output = run_command(command)
    if output:
        return output.split('\n')
    return []

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for commit in commits:
        lower_commit = commit.lower()
        if any(lower_commit.startswith(prefix) for prefix in ['feat:', 'add:', 'added:']):
            categories["Added"].append(commit)
        elif any(lower_commit.startswith(prefix) for prefix in ['fix:', 'fixed:', 'bugfix:']):
            categories["Fixed"].append(commit)
        elif any(lower_commit.startswith(prefix) for prefix in ['removed:', 'remove:', 'delete:']):
            categories["Removed"].append(commit)
        else:
            # Default to Changed for other types like refactor, docs, chore, etc.
            categories["Changed"].append(commit)
            
    return categories

def generate_markdown(categories, new_tag=None):
    today = datetime.now().strftime("%Y-%m-%d")
    version_header = f"[{new_tag}] - {today}" if new_tag else "[Unreleased]"
    
    lines = [f"# Changelog", ""]
    lines.append(f"## {version_header}")
    
    for cat, items in categories.items():
        if items:
            lines.append(f"### {cat}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
            
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate a CHANGELOG.md from git history.")
    parser.add_argument("--tag", help="New tag for this version (e.g., v1.0.0)")
    args = parser.parse_args()

    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    
    if not commits:
        print("No new commits found since last tag.")
        return

    categories = categorize_commits(commits)
    markdown = generate_markdown(categories, args.tag)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(markdown)
    
    print("CHANGELOG.md generated successfully.")

if __name__ == "__main__":
    main()
