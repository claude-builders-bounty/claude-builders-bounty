import subprocess
import re
import os

def get_last_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.STDOUT).decode("utf-8").strip()
        return tag
    except:
        return None

def get_commits(since_tag=None):
    cmd = ["git", "log", "--pretty=format:%s"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    commits = subprocess.check_output(cmd).decode("utf-8").split("\n")
    return [c for c in commits if c.strip()]

def categorize_commits(commits):
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    
    # 关键字匹配逻辑
    patterns = {
        "Added": r"^(feat|add|new|create)",
        "Fixed": r"^(fix|bug|patch|resolve)",
        "Changed": r"^(upd|change|mod|refactor|perf)",
        "Removed": r"^(rm|del|remove|deprecate)",
    }
    
    for msg in commits:
        found = False
        for cat, pattern in patterns.items():
            if re.search(pattern, msg, re.I):
                categories[cat].append(msg)
                found = True
                break
        if not found:
            categories["Other"].append(msg)
    return categories

def generate_markdown(categories, version="[Unreleased]"):
    from datetime import date
    today = date.today().isoformat()
    lines = [f"# CHANGELOG\n\n## {version} - {today}\n"]
    
    for cat, msgs in categories.items():
        if msgs:
            lines.append(f"### {cat}")
            for msg in msgs:
                lines.append(f"- {msg}")
            lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    categories = categorize_commits(commits)
    content = generate_markdown(categories)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(content)
    print("✅ CHANGELOG.md generated successfully.")
