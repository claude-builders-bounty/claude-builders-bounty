import subprocess
import sys
from datetime import datetime

def get_git_tag():
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return tag
    except subprocess.CalledProcessError:
        return None

def get_commits(since_tag=None):
    cmd = ['git', 'log', '--format=%s']
    if since_tag:
        cmd = ['git', 'log', f'{since_tag}..HEAD', '--format=%s']
    try:
        log_output = subprocess.check_output(cmd).decode('utf-8')
        commits = log_output.strip().split('\n')
        return [c.strip() for c in commits if c.strip()]
    except subprocess.CalledProcessError:
        return []

def categorize_commits(commits):
    categories = {
        'Added': [],
        'Changed': [],
        'Fixed': [],
        'Removed': [],
        'Other': []
    }
    
    for commit in commits:
        lower_line = commit.lower()
        if lower_line.startswith('feat') or lower_line.startswith('add'):
            categories['Added'].append(commit)
        elif lower_line.startswith('fix'):
            categories['Fixed'].append(commit)
        elif lower_line.startswith('refactor') or lower_line.startswith('chore') or lower_line.startswith('change') or lower_line.startswith('update') or lower_line.startswith('docs') or lower_line.startswith('style') or lower_line.startswith('test'):
            categories['Changed'].append(commit)
        elif lower_line.startswith('remove') or lower_line.startswith('del'):
            categories['Removed'].append(commit)
        else:
            categories['Other'].append(commit)
    return categories

def generate_changelog(categories):
    today = datetime.today().strftime('%Y-%m-%d')
    changelog = f"# Changelog\n\n## {today}\n\n"
    for category, items in categories.items():
        if items:
            changelog += f"### {category}\n"
            for item in items:
                changelog += f"- {item}\n"
            changelog += "\n"
    return changelog

if __name__ == "__main__":
    tag = get_git_tag()
    commits = get_commits(tag)
    if not commits:
        print("No commits found.")
        sys.exit(0)
        
    categories = categorize_commits(commits)
    changelog_content = generate_changelog(categories)
    
    with open('CHANGELOG.md', 'w') as f:
        f.write(changelog_content)
    
    print("CHANGELOG.md generated successfully.")
