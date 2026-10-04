#!/usr/bin/env python3
"""Generate a structured CHANGELOG from conventional commit messages.
Usage:
  python changelog_generator.py <git_repo_path> [--output CHANGELOG.md]
"""
import argparse, subprocess, re, sys, os

def get_commits(repo_path):
    try:
        out = subprocess.check_output([
            "git", "-C", repo_path, "log", "--pretty=format:%H%n%s%n%b%n---END---"
        ], text=True)
        entries = out.strip().split("---END---\n")
        commits = []
        for e in entries:
            lines = e.strip().split("\n")
            if not lines:
                continue
            commit_hash = lines[0]
            subject = lines[1] if len(lines) > 1 else ""
            body = "\n".join(lines[2:]) if len(lines) > 2 else ""
            commits.append({"hash": commit_hash, "subject": subject, "body": body})
        return commits
    except subprocess.CalledProcessError as err:
        sys.stderr.write(f"Git error: {err}\n")
        return []

def categorize(commits):
    categories = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Performance": [],
        "Refactoring": [],
        "Tests": [],
        "Other": []
    }
    for c in commits:
        subj = c["subject"].lower()
        if subj.startswith("feat"):
            categories["Features"].append(c)
        elif subj.startswith("fix"):
            categories["Bug Fixes"].append(c)
        elif subj.startswith("docs"):
            categories["Documentation"].append(c)
        elif subj.startswith("perf"):
            categories["Performance"].append(c)
        elif subj.startswith("refactor"):
            categories["Refactoring"].append(c)
        elif subj.startswith("test"):
            categories["Tests"].append(c)
        else:
            categories["Other"].append(c)
    return categories

def format_changelog(cats):
    lines = ["# CHANGELOG", ""]
    for cat, items in cats.items():
        if not items:
            continue
        lines.append(f"## {cat}")
        for c in items:
            lines.append(f"- {c['subject']} ({c['hash'][:7]})")
        lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.")
    parser.add_argument("repo_path", help="Path to the git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file")
    args = parser.parse_args()
    if not os.path.isdir(args.repo_path):
        sys.exit("Repository path does not exist.")
    commits = get_commits(args.repo_path)
    cats = categorize(commits)
    changelog = format_changelog(cats)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog)
    print(f"CHANGELOG written to {args.output}")

if __name__ == "__main__":
    main()
