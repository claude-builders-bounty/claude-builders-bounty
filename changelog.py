#!/usr/bin/env python3
# Windows: python changelog.py
# PowerShell: .\changelog.ps1
"""changelog.py — Generate structured CHANGELOG.md from git history.
Usage: python changelog.py [--repo PATH] [--output FILE] [--since TAG]
       python changelog.py                          # current directory
       python changelog.py --repo /path              # specific repo
       python changelog.py --output CHANGES.md       # custom output
"""

import argparse, subprocess, os, sys, re, textwrap
from datetime import date

CATEGORIES = [
    ("Added",     [r'^feat', r'^feature', r'^add', r'^new', r'^implement', r'^create']),
    ("Fixed",     [r'^fix', r'^bugfix', r'^hotfix', r'^patch', r'^correct', r'^repair', r'^bug']),
    ("Changed",   [r'^change', r'^update', r'^refactor', r'^modify', r'^improve',
                   r'^optimize', r'^redesign', r'^migrate', r'^upgrade', r'^chore']),
    ("Removed",   [r'^remove', r'^delete', r'^drop', r'^cleanup']),
    ("Deprecated",[r'^deprecat']),
    ("Security",  [r'^sec', r'^security', r'^vuln', r'^vulnerability']),
]

CONVENTIONAL_PREFIX = re.compile(r'^(feat|fix|chore|refactor|docs|style|test|perf|ci|build|revert|hotfix|remove|security)(\([^)]*\))?[!]?:\s*', re.IGNORECASE)
# KEYWORD_PREFIX is now combined above

_OTHER_PREFIX = re.compile(
    r'^(feat|fix|chore|refactor|docs|style|test|perf|ci|build|revert|hotfix)'
    r'(\([^)]*\))?[!]?:\s*', re.IGNORECASE
)

def run_git(cmd, cwd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""

def categorize(msg):
    for cat_name, patterns in CATEGORIES:
        for p in patterns:
            if re.search(p, msg, re.IGNORECASE):
                return cat_name
    return "Uncategorized"

def clean_message(msg):
    msg = CONVENTIONAL_PREFIX.sub('', msg)
    return msg.strip()

def get_remote_url(cwd):
    url = run_git(["git", "remote", "get-url", "origin"], cwd)
    url = re.sub(r'\.git$', '', url)
    url = re.sub(r'^git@([^:]+):', r'https://\1/', url)
    return url

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history")
    parser.add_argument("--repo", default=os.getcwd(), help="Path to git repository (default: current dir)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--since", default="", help="Starting tag/ref (default: latest tag)")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo)

    # Get since tag
    since = args.since or run_git(["git", "describe", "--tags", "--abbrev=0"], repo)

    if since:
        rev_range = f"{since}..HEAD"
        version = since
    else:
        rev_range = "--all"
        version = "0.1.0"

    # Get commits
    raw = run_git(
        ["git", "log", rev_range, "--pretty=format:%H||%s||%an||%ad",
         "--date=short", "--no-merges"],
        repo
    )

    if not raw:
        if since:
            print(f"No commits found after {since}. Showing full history instead.")
            raw = run_git(["git", "log", "--all", "--pretty=format:%H||%s||%an||%ad",
                          "--date=short", "--no-merges"], repo)
            version = "0.1.0"
        if not raw:
            print(f"No commits found.")
            return
        return

    today = date.today().isoformat()
    remote_url = get_remote_url(repo)

    # Parse and categorize commits
    categorized = {name: [] for name, _ in CATEGORIES}
    categorized["Uncategorized"] = []
    count = 0

    for line in raw.split('\n'):
        if not line.strip():
            continue
        parts = line.split('||', 3)
        if len(parts) < 2:
            continue
        hash_val = parts[0][:7]
        msg = parts[1] if len(parts) > 1 else ""
        # author = parts[2] if len(parts) > 2 else ""
        # author_date = parts[3] if len(parts) > 3 else ""

        clean = clean_message(msg)
        cat = categorize(msg)
        commit_url = f"{remote_url}/commit/{hash_val}" if remote_url else f"#{hash_val}"

        entry = f"  - {clean} ([{hash_val}]({commit_url}))"
        categorized[cat].append(entry)
        count += 1

    # Write output
    lines = ["# Changelog", "", f"## [{version}] - {today}", ""]
    has_content = False

    for cat_name, _ in CATEGORIES:
        entries = categorized.get(cat_name, [])
        if entries:
            lines.append(f"### {cat_name}")
            lines.append("")
            lines.extend(entries)
            lines.append("")
            has_content = True

    uncat = categorized.get("Uncategorized", [])
    if uncat:
        lines.append("### Uncategorized")
        lines.append("")
        lines.extend(uncat)
        lines.append("")

    if not has_content and not uncat:
        lines.append("No significant changes.")

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f"Generated: {os.path.join(os.getcwd(), args.output)}")
    print(f"Commits: {count}")

if __name__ == "__main__":
    main()
