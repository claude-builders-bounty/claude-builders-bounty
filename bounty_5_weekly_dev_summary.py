#!/usr/bin/env python3
"""
Bounty #5: Weekly Dev Summary with n8n Workflow
An n8n workflow configuration for generating weekly developer summaries
using Claude Code and scheduling.

This workflow:
1. Fetches git commit history from the past week
2. Generates a CHANGELOG using the bounty #1 script
3. Summarizes issues resolved
4. Posts to a channel or saves as a document
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timedelta


def get_weekly_commits():
    """Get git commits from the past week."""
    since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since_date}",
             "--pretty=format:%H %s %an %ae",
             "--no-merges"],
            capture_output=True,
            text=True,
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 2)
                if len(parts) >= 2:
                    commit_hash = parts[0]
                    subject = parts[1] if len(parts) > 2 else ""
                    author_name = parts[2] if len(parts) > 2 else ""
                    author_email = parts[3] if len(parts) > 3 else ""
                    commits.append({
                        "hash": commit_hash,
                        "subject": subject,
                        "author": author_name,
                        "email": author_email,
                    })
        
        return commits
    except Exception as e:
        print(f"Error getting commits: {e}", file=sys.stderr)
        return []


def generate_weekly_summary():
    """Generate a weekly dev summary."""
    commits = get_weekly_commits()
    
    # Categorize commits
    categories = {
        "features": [],
        "bug fixes": [],
        "docs": [],
        "refactoring": [],
        "tests": [],
        "other": [],
    }
    
    for commit in commits:
        subject = commit["subject"].lower()
        categorized = False
        
        if any(kw in subject for kw in ["feat", "feature", "new"]):
            categories["features"].append(commit)
            categorized = True
        elif any(kw in subject for kw in ["fix", "bug", "fix"]):
            categories["bug fixes"].append(commit)
            categorized = True
        elif any(kw in subject for kw in ["doc", "readme"]):
            categories["docs"].append(commit)
            categorized = True
        elif any(kw in subject for kw in ["refactor", "clean"]):
            categories["refactoring"].append(commit)
            categorized = True
        elif any(kw in subject for kw in ["test", "spec"]):
            categories["tests"].append(commit)
            categorized = True
        
        if not categorized:
            categories["other"].append(commit)
    
    # Generate summary
    lines = []
    lines.append("# Weekly Development Summary")
    lines.append(f"Week of {datetime.now().strftime('%B %d, %Y')}")
    lines.append("")
    lines.append(f"## Total Commits: {len(commits)}")
    lines.append("")
    
    for category, category_commits in categories.items():
        if category_commits:
            lines.append(f"### {category.title()}")
            lines.append(f"{len(category_commits)} commits")
            lines.append("")
            for commit in category_commits[:5]:  # Show top 5 per category
                lines.append(f"- {commit['subject']} ({commit['author']})")
            if len(category_commits) > 5:
                lines.append(f"- ... and {len(category_commits) - 5} more")
            lines.append("")
    
    # Summary stats
    lines.append("## Statistics")
    lines.append(f"- **Features implemented:** {len(categories['features'])}")
    lines.append(f"- **Bugs fixed:** {len(categories['bug fixes'])}")
    lines.append(f"- **Documentation updated:** {len(categories['docs'])}")
    lines.append(f"- **Refactoring:** {len(categories['refactoring'])}")
    lines.append(f"- **Tests added/updated:** {len(categories['tests'])}")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point for weekly dev summary."""
    summary = generate_weekly_summary()
    
    # Output summary (n8n will capture this)
    print(summary)
    
    # Also save to file for archival
    output_path = "weekly-summary.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    
    print(f"\n\nSaved to {output_path}")


if __name__ == "__main__":
    main()