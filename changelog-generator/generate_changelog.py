import os
import sys
import subprocess
from datetime import datetime

def get_commits_since_last_tag():
    # Try to get the last tag
    try:
        last_tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        print(f"Found last tag: {last_tag}")
        revision_range = f"{last_tag}..HEAD"
    except subprocess.CalledProcessError:
        print("No tags found. Fetching all commits.")
        last_tag = "Initial"
        revision_range = "HEAD"

    # Get commits: format "%h||%s" -> hash||subject
    cmd = ['git', 'log', revision_range, '--pretty=format:%h||%s']
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        print("Failed to get git log. Is this a git repository?")
        sys.exit(1)
        
    if not output:
        return last_tag, []
        
    commits = []
    for line in output.split('\n'):
        if '||' in line:
            h, s = line.split('||', 1)
            commits.append({"hash": h.strip(), "subject": s.strip()})
    
    return last_tag, commits

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": []
    }
    
    for commit in commits:
        subject = commit["subject"].lower()
        if subject.startswith("feat") or subject.startswith("add"):
            categories["Added"].append(commit)
        elif subject.startswith("fix") or subject.startswith("bug"):
            categories["Fixed"].append(commit)
        elif subject.startswith("refactor") or subject.startswith("chore") or subject.startswith("update") or subject.startswith("change") or subject.startswith("perf"):
            categories["Changed"].append(commit)
        elif subject.startswith("remove") or subject.startswith("delete") or subject.startswith("drop"):
            categories["Removed"].append(commit)
        else:
            categories["Other"].append(commit)
            
    return categories

def generate_changelog(last_tag, categories, output_file="CHANGELOG.md"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_version = "Unreleased"
    
    content = f"# Changelog\n\n## [{new_version}] - {date_str}\n\n"
    if last_tag != "Initial":
        content += f"Changes since tag: `{last_tag}`\n\n"
    
    for cat in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        if categories[cat]:
            content += f"### {cat}\n"
            for commit in categories[cat]:
                # Capitalize the first letter of the subject for neatness
                subj = commit["subject"][0].upper() + commit["subject"][1:] if commit["subject"] else ""
                content += f"- {subj} ({commit['hash']})\n"
            content += "\n"
            
    # Prepend to existing CHANGELOG if exists, otherwise create new
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            existing = f.read()
            # Remove the "# Changelog\n\n" from existing if present so we don't duplicate
            if existing.startswith("# Changelog\n\n"):
                existing = existing[len("# Changelog\n\n"):]
            elif existing.startswith("# Changelog\n"):
                existing = existing[len("# Changelog\n"):]
        
        with open(output_file, "w") as f:
            f.write(content + "---\n\n" + existing)
    else:
        with open(output_file, "w") as f:
            f.write(content)
            
    print(f"Successfully generated/updated {output_file}")

if __name__ == "__main__":
    tag, commits = get_commits_since_last_tag()
    if not commits:
        print("No new commits found since last tag.")
        sys.exit(0)
        
    cats = categorize_commits(commits)
    generate_changelog(tag, cats)
