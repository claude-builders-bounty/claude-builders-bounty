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
        command = f'git log {since_tag}..HEAD --pretty=format:"%h %s"'
    else:
        command = 'git log --pretty=format:"%h %s"'
    
    output = run_command(command)
    if output:
        return output.split('\n')
    return []

def categorize_commits(commits):
    categories = {
        "Breaking Changes": [],
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Documentation": [],
        "Performance": [],
        "Testing": [],
        "Build": [],
        "CI/CD": [],
        "Maintenance": []
    }
    
    for commit in commits:
        parts = commit.split(' ', 1)
        if len(parts) < 2:
            continue
        h, subject = parts
        lower_subject = subject.lower()
        
        # Check for breaking changes
        if '!' in subject.split(':')[0] or 'breaking change' in lower_subject:
            categories["Breaking Changes"].append((h, subject))
            continue
            
        # Strip conventional commit scope if present, e.g., feat(auth): -> feat:
        subject_for_prefix = re.sub(r'\(.*?\)', '', lower_subject)
        
        if any(subject_for_prefix.startswith(prefix) for prefix in ['feat', 'add']):
            categories["Added"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['fix', 'bugfix']):
            categories["Fixed"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['remove', 'delete']):
            categories["Removed"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['docs', 'doc']):
            categories["Documentation"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['perf', 'optimization']):
            categories["Performance"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['test', 'unit']):
            categories["Testing"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['build', 'deps']):
            categories["Build"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['ci', 'workflow', 'github-actions']):
            categories["CI/CD"].append((h, subject))
        elif any(subject_for_prefix.startswith(prefix) for prefix in ['chore', 'refactor', 'style']):
            categories["Maintenance"].append((h, subject))
        else:
            categories["Changed"].append((h, subject))
            
    return categories

def get_repo_url():
    url = run_command("git config --get remote.origin.url")
    if url:
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/").replace(".git", "")
        elif url.startswith("https://github.com/"):
            if url.endswith(".git"):
                url = url[:-4]
        return url
    return None

def generate_markdown(categories, repo_url=None, new_tag=None):
    today = datetime.now().strftime("%Y-%m-%d")
    version_header = f"[{new_tag}] - {today}" if new_tag else "[Unreleased]"
    
    lines = [f"# Changelog", ""]
    lines.append(f"## {version_header}")
    
    for cat, items in categories.items():
        if items:
            lines.append(f"### {cat}")
            for h, subject in items:
                if repo_url:
                    lines.append(f"- {subject} ([{h}]({repo_url}/commit/{h}))")
                else:
                    lines.append(f"- {subject} ({h})")
            lines.append("")
            
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate a CHANGELOG.md from git history.")
    parser.add_argument("--tag", help="New tag for this version (e.g., v1.0.0)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file name")
    args = parser.parse_args()

    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    repo_url = get_repo_url()
    
    if not commits:
        print("No new commits found since last tag.")
        return

    categories = categorize_commits(commits)
    markdown = generate_markdown(categories, repo_url, args.tag)
    
    with open(args.output, "w") as f:
        f.write(markdown)
    
    print(f"{args.output} generated successfully.")

if __name__ == "__main__":
    main()
