#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Categorizes commits into Added, Fixed, Changed, Removed (Keep a Changelog format).
Works across Windows, macOS, and Linux.
"""
import sys
import subprocess
import re
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_last_tag():
    """Returns the most recent git tag, or None if no tags exist."""
    try:
        res = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def get_git_commits(since_tag=None):
    """
    Fetches git commit logs since the last tag or full history.
    Format: hash|author|date|subject
    """
    cmd = ["git", "log", "--pretty=format:%h|%an|%ad|%s", "--date=short"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return lines
    except Exception as e:
        print(f"Error reading git commits: {e}", file=sys.stderr)
        return []

def categorize_commit(subject):
    """
    Categorizes a commit subject based on Conventional Commits standards.
    Categories: Added, Fixed, Changed, Removed
    """
    sub_lower = subject.lower()
    
    # Conventional commit prefixes: feat(scope): message or feat: message
    if re.match(r"^feat(\(.*\))?!?:", sub_lower) or any(sub_lower.startswith(w) for w in ["add:", "added:", "create:", "new:"]):
        clean = re.sub(r"^(feat(\(.*\))?!?:|add:|added:|create:|new:)\s*", "", subject, flags=re.I)
        return "Added", clean.strip()
    
    if re.match(r"^fix(\(.*\))?!?:", sub_lower) or any(sub_lower.startswith(w) for w in ["fix:", "fixed:", "bugfix:", "resolve:"]):
        clean = re.sub(r"^(fix(\(.*\))?!?:|fix:|fixed:|bugfix:|resolve:)\s*", "", subject, flags=re.I)
        return "Fixed", clean.strip()
        
    if re.match(r"^(remove|deprecate|revert)(\(.*\))?!?:", sub_lower) or any(sub_lower.startswith(w) for w in ["drop:", "delete:"]):
        clean = re.sub(r"^(remove|deprecate|revert|drop|delete)(\(.*\))?!?:?\s*", "", subject, flags=re.I)
        return "Removed", clean.strip()
        
    # Refactor, chore, docs, style, perf, test default to Changed
    if re.match(r"^(refactor|chore|docs|style|perf|test|build|ci)(\(.*\))?!?:", sub_lower):
        clean = re.sub(r"^(refactor|chore|docs|style|perf|test|build|ci)(\(.*\))?!?:?\s*", "", subject, flags=re.I)
        return "Changed", clean.strip()

    # Fallback heuristics
    if "fix" in sub_lower or "bug" in sub_lower or "patch" in sub_lower:
        return "Fixed", subject
    if "add" in sub_lower or "implement" in sub_lower or "support" in sub_lower:
        return "Added", subject
    if "remove" in sub_lower or "delete" in sub_lower or "deprecated" in sub_lower:
        return "Removed", subject
        
    return "Changed", subject

def build_changelog(version="Unreleased", since_tag=None, commits=None):
    """Generates the Markdown CHANGELOG string."""
    if commits is None:
        commits = get_git_commits(since_tag)
        
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for item in commits:
        parts = item.split("|", 3)
        if len(parts) >= 4:
            commit_hash, author, date, subject = parts
        else:
            commit_hash, author, date, subject = "", "", "", item
            
        cat, clean_msg = categorize_commit(subject)
        hash_badge = f"`{commit_hash}` " if commit_hash else ""
        categories[cat].append(f"- {hash_badge}{clean_msg}")
        
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}\n"
    if since_tag:
        header += f"*Changes since tag `{since_tag}`*\n\n"
    else:
        header += "*Initial release / Full history*\n\n"
        
    body = []
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat]
        if items:
            body.append(f"### {cat}\n")
            body.extend([f"{i}\n" for i in items])
            body.append("\n")
            
    if not any(categories.values()):
        body.append("_No commits found in this range._\n\n")
        
    return header + "".join(body).rstrip() + "\n"

def main():
    tag = get_last_tag()
    output_file = Path("CHANGELOG.md")
    new_entry = build_changelog(version="Unreleased", since_tag=tag)
    
    if output_file.exists():
        existing = output_file.read_text(encoding="utf-8")
        if "# Changelog" in existing:
            updated = existing.replace("# Changelog\n", f"# Changelog\n\n{new_entry}\n", 1)
        else:
            updated = f"# Changelog\n\n{new_entry}\n\n{existing}"
    else:
        updated = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n{new_entry}"
        
    output_file.write_text(updated, encoding="utf-8")
    print(f"✅ Successfully generated CHANGELOG.md (Range: {'since ' + tag if tag else 'all commits'})")
    print(new_entry)

if __name__ == "__main__":
    main()
