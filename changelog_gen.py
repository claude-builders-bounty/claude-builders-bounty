#!/usr/bin/env python3
import subprocess
import re
from collections import defaultdict
from datetime import datetime
import sys
from pathlib import Path

def get_git_logs():
    """Fetch git logs in a format easy to parse: hash|subject|date"""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H|%s|%ad", "--date=short"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError as e:
        print(f"Error fetching git logs: {e}")
        sys.exit(1)

def parse_commits(logs):
    """Group commits by type according to Conventional Commits."""
    categories = {
        "feat": "🚀 Features",
        "fix": "🐛 Bug Fixes",
        "docs": "📚 Documentation",
        "perf": "⚡ Performance Improvements",
        "refactor": "♻️ Code Refactoring",
        "chore": "🔧 Maintenance",
        "style": "🎨 Style",
        "test": "✅ Tests",
    }
    grouped = defaultdict(list)
    
    for line in logs:
        if not line: continue
        parts = line.split('|')
        if len(parts) < 3: continue
        
        subject = parts[1]
        date = parts[2]
        
        # Regex for Conventional Commits: type(scope): subject
        match = re.match(r'^(\w+)(?:\(([^)]+)\))?:\s*(.*)$', subject)
        if match:
            ctype, scope, msg = match.groups()
            category = categories.get(ctype, "📦 Other")
            scope_prefix = f"**{scope}**: " if scope else ""
            grouped[category].append(f"{scope_prefix}{msg} ({date})")
        else:
            grouped["📦 Other"].append(f"{subject} ({date})")
            
    return grouped

def generate_markdown(grouped_commits):
    """Format the grouped commits into a Markdown CHANGELOG."""
    if not grouped_commits:
        return "No commits found to generate a changelog."
        
    lines = ["# Changelog\n", f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    
    # Sort categories to ensure consistent order
    order = ["🚀 Features", "🐛 Bug Fixes", "⚡ Performance Improvements", "♻️ Code Refactoring", "📚 Documentation", "✅ Tests", "🎨 Style", "🔧 Maintenance", "📦 Other"]
    
    for cat in order:
        if cat in grouped_commits:
            lines.append(f"## {cat}")
            for commit in grouped_commits[cat]:
                lines.append(f"- {commit}")
            lines.append("")
            
    return "\n".join(lines)

def main():
    logs = get_git_logs()
    if not logs:
        print("No git history found in this directory.")
        return
    
    grouped = parse_commits(logs)
    changelog = generate_markdown(grouped)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)
    
    print("Successfully generated CHANGELOG.md")

if __name__ == "__main__":
    main()
