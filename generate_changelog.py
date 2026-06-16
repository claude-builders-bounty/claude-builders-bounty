import subprocess
import re
from collections import defaultdict

def get_commits():
    try:
        # Get the last tag
        last_tag_process = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        )
        
        if last_tag_process.returncode != 0:
            # If no tags, get all commits
            git_log_cmd = ["git", "log", "--pretty=format:%s"]
        else:
            last_tag = last_tag_process.stdout.strip()
            git_log_cmd = ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%s"]
            
        log_process = subprocess.run(git_log_cmd, capture_output=True, text=True, check=True)
        return log_process.stdout.splitlines()
    except Exception as e:
        print(f"Error fetching commits: {e}")
        return []

def categorize_commit(message):
    message = message.lower()
    if any(word in message for word in ["add", "feat", "new", "create"]):
        return "Added"
    if any(word in message for word in ["fix", "bug", "resolve", "patch"]):
        return "Fixed"
    if any(word in message for word in ["change", "update", "modify", "refactor"]):
        return "Changed"
    if any(word in message for word in ["remove", "delete", "drop"]):
        return "Removed"
    return "Other"

def generate_markdown():
    commits = get_commits()
    if not commits:
        print("No commits found since last tag.")
        return
        
    categories = defaultdict(list)
    for msg in commits:
        cat = categorize_commit(msg)
        categories[cat].append(msg)
        
    # Order of categories
    order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write("# Changelog\n\n")
        for cat in order:
            if categories[cat]:
                f.write(f"## {cat}\n")
                for msg in categories[cat]:
                    f.write(f"- {msg}\n")
                f.write("\n")
    
    print("CHANGELOG.md generated successfully.")

if __name__ == "__main__":
    generate_markdown()
