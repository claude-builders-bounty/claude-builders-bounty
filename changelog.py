import subprocess
import datetime
import sys

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return ""

def get_commits():
    # Find the last tag
    last_tag = run_cmd("git describe --tags --abbrev=0")
    
    if last_tag:
        print(f"Found last tag: {last_tag}")
        git_log_cmd = f"git log {last_tag}..HEAD --pretty=format:\"%s\""
    else:
        print("No tags found. Fetching all commits.")
        git_log_cmd = "git log --pretty=format:\"%s\""
        
    log_output = run_cmd(git_log_cmd)
    if not log_output:
        print("No commits found.")
        sys.exit(0)
        
    return log_output.split('\n')

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Removed": [],
        "Changed": []
    }
    
    for commit in commits:
        commit_lower = commit.lower()
        if commit_lower.startswith(('add', 'feat', 'new', 'create')):
            categories["Added"].append(commit)
        elif commit_lower.startswith(('fix', 'bug', 'patch', 'resolve')):
            categories["Fixed"].append(commit)
        elif commit_lower.startswith(('remove', 'del', 'drop', 'rm')):
            categories["Removed"].append(commit)
        else:
            # Catch-all for chore, refactor, update, style, docs, etc.
            categories["Changed"].append(commit)
            
    return categories

def generate_changelog(categories):
    today = datetime.date.today().strftime("%Y-%m-%d")
    changelog_content = f"# Changelog\n\n## [Unreleased] - {today}\n\n"
    
    for category, items in categories.items():
        if items:
            changelog_content += f"### {category}\n"
            for item in items:
                changelog_content += f"- {item}\n"
            changelog_content += "\n"
            
    return changelog_content

if __name__ == "__main__":
    commits = get_commits()
    categorized = categorize_commits(commits)
    changelog = generate_changelog(categorized)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)
        
    print("Successfully generated CHANGELOG.md")
