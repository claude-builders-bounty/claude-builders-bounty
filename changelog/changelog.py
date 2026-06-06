#!/usr/bin/env python3
import subprocess
import sys
import os
import re

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip(), result.returncode

def get_latest_tag():
    # Lấy tag gần nhất
    stdout, code = run_cmd("git describe --tags --abbrev=0")
    if code != 0 or not stdout:
        return None
    return stdout

def get_commits_since(tag=None):
    if tag:
        # Lấy commits từ tag đến HEAD
        cmd = f'git log {tag}..HEAD --oneline --no-merges'
    else:
        # Nếu không có tag, lấy toàn bộ commits
        cmd = 'git log --oneline --no-merges'
    
    stdout, code = run_cmd(cmd)
    if code != 0 or not stdout:
        return []
    
    commits = []
    for line in stdout.split('\n'):
        if not line:
            continue
        parts = line.split(' ', 1)
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))
    return commits

def parse_commit_category(message):
    msg_lower = message.lower()
    
    # Conventional commits check
    conv_match = re.match(r'^([a-z]+)(\(.*\))?!?: (.*)', msg_lower)
    if conv_match:
        type_prefix = conv_match.group(1)
        if type_prefix in ['feat', 'add', 'new']:
            return 'Added'
        elif type_prefix in ['fix', 'bug', 'patch', 'hotfix']:
            return 'Fixed'
        elif type_prefix in ['docs', 'refactor', 'style', 'perf', 'build', 'ci', 'test', 'chore', 'update']:
            return 'Changed'
        elif type_prefix in ['remove', 'delete', 'deprecate']:
            return 'Removed'

    # Heuristic check
    if any(k in msg_lower for k in ['add', 'feat', 'create', 'new', 'implement', 'support']):
        return 'Added'
    elif any(k in msg_lower for k in ['fix', 'bug', 'solve', 'resolve', 'close', 'prevent', 'patch', 'hotfix']):
        return 'Fixed'
    elif any(k in msg_lower for k in ['remove', 'delete', 'deprecate', 'drop', 'clean']):
        return 'Removed'
    else:
        return 'Changed'

def main():
    print("Generating CHANGELOG.md...")
    
    # Check if git repo
    _, code = run_cmd("git rev-parse --is-inside-work-tree")
    if code != 0:
        print("Error: Not a git repository.")
        sys.exit(1)

    latest_tag = get_latest_tag()
    commits = get_commits_since(latest_tag)
    
    if not commits:
        print("No commits found since the last tag (or at all).")
        sys.exit(0)

    categories = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }

    for sha, message in commits:
        cat = parse_commit_category(message)
        categories[cat].append((sha, message))

    # Build Changelog markdown
    changelog = []
    
    # Title
    tag_info = f"since tag {latest_tag}" if latest_tag else "initial release"
    changelog.append(f"# Changelog ({tag_info})\n")
    
    has_content = False
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            has_content = True
            changelog.append(f"## {cat}")
            for sha, message in categories[cat]:
                # Format: - commit_message (sha)
                changelog.append(f"- {message} ({sha})")
            changelog.append("") # Empty line

    if not has_content:
        changelog.append("No notable changes.")

    changelog_content = "\n".join(changelog)
    
    # Write to CHANGELOG.md
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog_content)
        
    print("CHANGELOG.md successfully generated!")
    print(changelog_content)

if __name__ == "__main__":
    main()
