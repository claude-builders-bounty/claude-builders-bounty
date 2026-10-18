#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Structured CHANGELOG from Git History
==============================================
Extracts git commits since the last tag, categorizes by standard Keep-a-Changelog
sections (Added, Fixed, Changed, Removed), and appends or writes CHANGELOG.md.
"""

import subprocess
import sys
import re
import os
import argparse
import datetime
from pathlib import Path

def run_git(cmd, cwd="."):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, cwd=cwd, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""

def get_last_tag(repo_dir="."):
    return run_git("git describe --tags --abbrev=0", cwd=repo_dir)

def get_commits_since_tag(tag="", repo_dir="."):
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    log_format = "%h|%s|%an|%ad"
    raw_log = run_git(f'git log {range_spec} --pretty=format:"{log_format}" --date=short', cwd=repo_dir)
    if not raw_log:
        return []
    
    commits = []
    for line in raw_log.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 2:
            commits.append({
                "hash": parts[0],
                "message": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else ""
            })
    return commits

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": []
    }
    
    patterns = {
        "Added": re.compile(r"^(?:feat|add|feature|new)(?:\(.*?\))?!?:?\s*(.+)", re.IGNORECASE),
        "Fixed": re.compile(r"^(?:fix|bug|hotfix|patch)(?:\(.*?\))?!?:?\s*(.+)", re.IGNORECASE),
        "Removed": re.compile(r"^(?:remove|rm|deprecate|delete)(?:\(.*?\))?!?:?\s*(.+)", re.IGNORECASE),
        "Changed": re.compile(r"^(?:refactor|perf|change|update|chore|docs|style|test|build|ci)(?:\(.*?\))?!?:?\s*(.+)", re.IGNORECASE)
    }
    
    for c in commits:
        msg = c["message"]
        matched = False
        for cat, pat in patterns.items():
            m = pat.match(msg)
            if m:
                clean_msg = m.group(1).strip()
                categories[cat].append((c["hash"], clean_msg))
                matched = True
                break
        if not matched:
            # Fallback simple keyword match
            lower = msg.lower()
            if "fix" in lower or "bug" in lower:
                categories["Fixed"].append((c["hash"], msg))
            elif "add" in lower or "feat" in lower:
                categories["Added"].append((c["hash"], msg))
            elif "remove" in lower or "delete" in lower:
                categories["Removed"].append((c["hash"], msg))
            else:
                categories["Changed"].append((c["hash"], msg))
                
    return categories

def build_changelog_markdown(categories, version="Unreleased", date_str=None):
    if not date_str:
        date_str = datetime.date.today().isoformat()
    
    lines = [f"## [{version}] - {date_str}"]
    has_any = False
    
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(cat, [])
        if items:
            has_any = True
            lines.append(f"\n### {cat}")
            for h, msg in items:
                lines.append(f"- {msg} (`{h}`)")
                
    if not has_any:
        lines.append("\n*No significant user-facing changes documented.*")
        
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--repo", default=".", help="Target Git repository path.")
    parser.add_argument("--version", default="Unreleased", help="Release version title.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without writing.")
    args = parser.parse_args()

    last_tag = get_last_tag(args.repo)
    commits = get_commits_since_tag(last_tag, args.repo)
    if not commits:
        print("ℹ️ No new commits found since last tag / root.")
        return

    cats = categorize_commits(commits)
    md_content = build_changelog_markdown(cats, version=args.version)

    if args.dry_run:
        print(md_content)
        return

    out_path = Path(args.repo) / args.output
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        # Check if header exists
        if "# Changelog" in existing:
            # Insert after the header
            parts = existing.split("# Changelog", 1)
            updated = f"# Changelog\n\n{md_content}\n{parts[1].lstrip()}"
        else:
            updated = f"# Changelog\n\n{md_content}\n\n{existing}"
    else:
        updated = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{md_content}"

    out_path.write_text(updated, encoding="utf-8")
    print(f"✅ Successfully updated {out_path.resolve()} ({len(commits)} commits processed).")

if __name__ == "__main__":
    main()
