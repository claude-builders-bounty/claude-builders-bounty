
import subprocess
import re
import os
import sys

def get_git_log():
    # Fetches all commit messages since the beginning of the history (no tags found)
    # --pretty=format:"%h%n%s%n%b" gets hash, subject, and body, separated by newline
    # -M finds renames, -C finds copies (disabled for simplicity, can add if needed)
    cmd = "git log --pretty=format:'%H%n%s%n%b%n---COMMIT-END---' --no-merges"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def parse_commits(log_output):
    commits_raw = log_output.split('---COMMIT-END---')
    commits = []
    for commit_block in commits_raw:
        if not commit_block.strip():
            continue
        parts = commit_block.strip().split('\n', 2)
        if len(parts) >= 2:
            sha = parts[0]
            subject = parts[1]
            body = parts[2] if len(parts) > 2 else ""
            commits.append({'sha': sha, 'subject': subject, 'body': body})
    return commits

def categorize_change(subject):
    subject_lower = subject.lower()
    if subject_lower.startswith("feat"):
        return "Added"
    elif subject_lower.startswith("fix"):
        return "Fixed"
    elif subject_lower.startswith("chore"):
        return "Changed" # Chores can be considered changes
    elif subject_lower.startswith("refactor"):
        return "Changed"
    elif subject_lower.startswith("docs"):
        return "Changed" # Documentation changes
    elif subject_lower.startswith("build"):
        return "Changed"
    elif subject_lower.startswith("ci"):
        return "Changed"
    elif subject_lower.startswith("perf"):
        return "Changed" # Performance improvements
    elif subject_lower.startswith("style"):
        return "Changed"
    elif subject_lower.startswith("revert"):
        return "Reverted"
    elif subject_lower.startswith("test"):
        return "Changed" # Test changes
    elif "remove" in subject_lower:
        return "Removed"
    elif "initial commit" in subject_lower:
        return "Added" # Initial commit adds everything
    else:
        return "Changed"

def generate_changelog(commits):
    changelog_content = "# Changelog\n\n"
    
    # Simple formatting: group by category
    categorized = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Reverted": [],
        "Other": []
    }

    for commit in reversed(commits): # Display newest commits first by reversing
        category = categorize_change(commit['subject'])
        formatted_entry = f"- {commit['subject']} ({commit['sha'][:7]})"
        if category in categorized:
            categorized[category].append(formatted_entry)
        else:
            categorized["Other"].append(formatted_entry)

    for category, entries in categorized.items():
        if entries:
            changelog_content += f"## {category}\n\n"
            changelog_content += "\n".join(entries) + "\n\n"
            
    return changelog_content

if __name__ == "__main__":
    try:
        log_output = get_git_log()
        commits = parse_commits(log_output)
        changelog = generate_changelog(commits)
        
        output_path = "CHANGELOG.md"
        with open(output_path, "w") as f:
            f.write(changelog)
        print(f"Generated {output_path} successfully.\n")
        print("--- CHANGELOG.md Content ---\n")
        print(changelog)
    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e}", file=sys.stderr)
        print(f"Stdout: {e.stdout}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        exit(1)
