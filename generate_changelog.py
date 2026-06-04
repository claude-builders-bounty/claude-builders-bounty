#!/usr/bin/env python3
import subprocess
import sys
import os
import re

def run_command(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def main():
    # 1. Check if git repository is initialized
    if not os.path.exists(".git"):
        print("Error: The current directory is not a Git repository. Initialize git first.")
        sys.exit(1)

    # 2. Find the last git tag
    last_tag = run_command("git describe --tags --abbrev=0")
    
    # 3. Retrieve commits since the last tag or retrieve all if no tag is found
    if last_tag:
        print(f"Sourcing commits since last tag: {last_tag}...")
        log_command = f'git log {last_tag}..HEAD --pretty=format:"%h|%s"'
    else:
        print("No git tags found. Sourcing all commits...")
        log_command = 'git log --pretty=format:"%h|%s"'
        
    git_log_output = run_command(log_command)
    
    if not git_log_output:
        print("No commits found in the repository since last tag/start.")
        sys.exit(0)
        
    commit_lines = git_log_output.split('\n')
    
    # 4. Categorization bins
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    # Classification rules
    added_patterns = [r'^feat', r'^add', r'^new', r'added', r'created']
    fixed_patterns = [r'^fix', r'^bug', r'fixed', r'resolve', r'patch']
    removed_patterns = [r'^remove', r'^delete', r'^deprecate', r'removed', r'deleted']
    changed_patterns = [r'^refactor', r'^change', r'^perf', r'^update', r'^chore', r'updated', r'changed']

    for line in commit_lines:
        if not line.strip() or '|' not in line:
            continue
        commit_hash, commit_msg = line.split('|', 1)
        commit_msg_lower = commit_msg.lower()
        
        # Categorize using pattern matching
        if any(re.search(pat, commit_msg_lower) for pat in added_patterns):
            categories["Added"].append((commit_msg, commit_hash))
        elif any(re.search(pat, commit_msg_lower) for pat in fixed_patterns):
            categories["Fixed"].append((commit_msg, commit_hash))
        elif any(re.search(pat, commit_msg_lower) for pat in removed_patterns):
            categories["Removed"].append((commit_msg, commit_hash))
        else:
            # All other commits fall under "Changed" (updates, chores, refactors)
            categories["Changed"].append((commit_msg, commit_hash))

    # 5. Format the CHANGELOG.md content
    changelog_lines = [
        "# Changelog\n",
        "All notable changes to this project will be documented in this file.\n",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n",
        "## [Unreleased]\n"
    ]
    
    has_content = False
    for cat, commits in categories.items():
        if commits:
            has_content = True
            changelog_lines.append(f"### {cat}\n")
            for msg, commit_hash in commits:
                changelog_lines.append(f"- {msg} ({commit_hash})\n")
            changelog_lines.append("") # blank line separator

    if not has_content:
        changelog_lines.append("No changes recorded.\n")

    # 6. Write out CHANGELOG.md
    output_path = "CHANGELOG.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(changelog_lines)
        
    print(f"SUCCESS: Generated formatted {output_path} successfully in the current directory.")

if __name__ == "__main__":
    main()
