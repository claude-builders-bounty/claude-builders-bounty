"""Automated CHANGELOG generator from git commit history."""
import subprocess
import re
from datetime import datetime, timezone

def get_commits(limit=50):
    res = subprocess.run(["git", "log", f"-n{limit}", "--pretty=format:%h|%s|%an|%ad", "--date=short"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return []
    commits = []
    for line in res.stdout.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({"hash": parts[0], "message": parts[1], "author": parts[2], "date": parts[3]})
    return commits

def categorize_commits(commits):
    categories = {"Added": [], "Fixed": [], "Changed": [], "Other": []}
    for c in commits:
        msg = c["message"].lower()
        if re.search(r"\b(feat|add|feature|implement)\b", msg):
            categories["Added"].append(c)
        elif re.search(r"\b(fix|bug|patch|resolve)\b", msg):
            categories["Fixed"].append(c)
        elif re.search(r"\b(refactor|update|change|perf)\b", msg):
            categories["Changed"].append(c)
        else:
            categories["Other"].append(c)
    return categories

def generate_markdown_changelog(version="Unreleased", commits=None):
    if commits is None:
        commits = get_commits()
    cats = categorize_commits(commits)
    lines = [f"## [{version}] - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"]
    for cat, items in cats.items():
        if items:
            lines.append(f"\n### {cat}")
            for item in items:
                lines.append(f"- {item['message']} ([{item['hash']}]) - @{item['author']}")
    return "\n".join(lines)
