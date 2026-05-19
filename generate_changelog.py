import subprocess
import re
import sys
from collections import defaultdict
from datetime import datetime

def get_git_logs():
    """Fetches git commit logs with hash, subject, and body."""
    try:
        cmd = ["git", "log", "--pretty=format:%H%n%s%n%b%n---COMMIT-END---"]
        result = subprocess.check_output(cmd, encoding="utf-8")
        return result.split("---COMMIT-END---")
    except Exception as e:
        print(f"Error reading git logs: {e}")
        return []

def parse_commits(logs):
    """Categorizes commits based on Conventional Commits standards."""
    categories = defaultdict(list)
    patterns = {
        "Features": r"feat(?:\(.*\))?:",
        "Bug Fixes": r"fix(?:\(.*\))?:",
        "Documentation": r"docs(?:\(.*\))?:",
        "Performance": r"perf(?:\(.*\))?:",
        "Refactoring": r"refactor(?:\(.*\))?:",
        "Security": r"security:",
        "CI/CD": r"ci(?:\(.*\))?:|chore(?:\(.*\))?:"
    }

    for log in logs:
        lines = log.strip().split("\n")
        if len(lines) < 2:
            continue
        
        commit_hash = lines[0][:8]
        subject = lines[1]
        
        matched = False
        for cat, pattern in patterns.items():
            if re.match(pattern, subject, re.IGNORECASE):
                # Clean up the subject line
                clean_subject = re.sub(pattern, "", subject, flags=re.IGNORECASE).strip()
                categories[cat].append(f"- {clean_subject} ([{commit_hash}])")
                matched = True
                break
        
        if not matched:
            categories["Other"].append(f"- {subject} ([{commit_hash}])")
            
    return categories

def generate_changelog(categories):
    """Formats the categories into a markdown CHANGELOG."""
    output = [f"# CHANGELOG\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    
    # Priority order
    order = ["Features", "Bug Fixes", "Security", "Performance", "Refactoring", "Documentation", "CI/CD", "Other"]
    
    for cat in order:
        if cat in categories and categories[cat]:
            output.append(f"## {cat}")
            output.extend(categories[cat])
            output.append("")
            
    return "\n".join(output)

if __name__ == "__main__":
    logs = get_git_logs()
    if not logs:
        print("No git history found.")
        sys.exit(1)
        
    categories = parse_commits(logs)
    changelog_content = generate_changelog(categories)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(changelog_content)
        
    print("[SUCCESS] CHANGELOG.md has been generated.")
