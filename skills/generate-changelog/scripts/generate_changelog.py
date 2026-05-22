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

def get_commits(since_tag=None, since_date=None):
    if since_tag:
        command = f'git log {since_tag}..HEAD --pretty=format:"%h %s"'
    elif since_date:
        command = f'git log --since="{since_date}" --pretty=format:"%h %s"'
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

def calculate_stability_rating(categories):
    """Calculate a stability score (0-100%) and risk level."""
    breaking = len(categories.get("Breaking Changes", []))
    fixes = len(categories.get("Fixed", []))
    total = sum(len(items) for items in categories.values())
    
    if total == 0:
        return 100, "STABLE"
        
    # Each breaking change takes 20% stability
    # Each fix takes 5% stability (indicates regressions or instability)
    penalty = (breaking * 20) + (fixes * 5)
    score = max(0, 100 - penalty)
    
    if breaking > 0 or score < 50:
        return score, "CAUTION"
    if score < 85:
        return score, "STABLE"
    return score, "EXCELLENT"

def generate_markdown(categories, repo_url=None, new_tag=None):
    today = datetime.now().strftime("%Y-%m-%d")
    version_header = f"[{new_tag}] - {today}" if new_tag else "[Unreleased]"
    score, level = calculate_stability_rating(categories)
    
    lines = [f"# Changelog", ""]
    lines.append(f"## {version_header}")
    lines.append("")
    lines.append(f"### 🚀 Release Summary")
    lines.append(f"- **Stability Rating**: {score}%")
    lines.append(f"- **Risk Level**: {level}")
    lines.append(f"- **Total Commits**: {sum(len(items) for items in categories.values())}")
    lines.append("")

    # Category Mapping with Icons
    ICON_MAP = {
        "Breaking Changes": "💥 Breaking Changes",
        "Added": "✨ Added",
        "Fixed": "🐛 Fixed",
        "Changed": "♻️ Changed",
        "Removed": "🗑️ Removed",
        "Documentation": "📝 Documentation",
        "Performance": "⚡ Performance",
        "Testing": "🧪 Testing",
        "Build": "📦 Build",
        "CI/CD": "⚙️ CI/CD",
        "Maintenance": "🔧 Maintenance"
    }
    
    for cat, items in categories.items():
        if items:
            lines.append(f"### {ICON_MAP.get(cat, cat)}")
            for h, subject in items:
                # Linkify PR numbers if repo_url is available
                if repo_url:
                    subject = re.sub(r'#(\d+)', rf'[#\1]({repo_url}/pull/\1)', subject)
                    lines.append(f"- {subject} ([{h}]({repo_url}/commit/{h}))")
                else:
                    lines.append(f"- {subject} ({h})")
            lines.append("")
            
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate a CHANGELOG.md from git history.")
    parser.add_argument("--tag", help="New tag for this version (e.g., v1.0.0)")
    parser.add_argument("--since", help="Fetch commits since this date (e.g., '2023-01-01' or '1 week ago')")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file name")
    args = parser.parse_args()

    last_tag = get_last_tag() if not args.since else None
    commits = get_commits(last_tag, args.since)
    repo_url = get_repo_url()
    
    if not commits:
        print(f"No new commits found{' since ' + args.since if args.since else ' since last tag'}.")
        return

    categories = categorize_commits(commits)
    markdown = generate_markdown(categories, repo_url, args.tag)
    
    with open(args.output, "w") as f:
        f.write(markdown)
    
    print(f"{args.output} generated successfully.")

if __name__ == "__main__":
    main()
