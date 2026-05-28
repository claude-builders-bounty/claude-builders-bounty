#!/usr/bin/env python3
"""
changelog.py — Auto-generate beautiful changelogs from git history.
Usage: python changelog.py [--tag TAG] [--output FILE] [--format markdown|json|html]
"""
import subprocess, json, sys, os, re, argparse
from datetime import datetime
from collections import defaultdict

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        return r.stdout.strip() if r.returncode == 0 else ""
    except: return ""

# Conventional commit → bounty category mapping
CATEGORY_MAP = {
    "feat": "Added", "feature": "Added", "add": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "bug": "Fixed", "hotfix": "Fixed",
    "refactor": "Changed", "perf": "Changed", "performance": "Changed",
    "style": "Changed", "docs": "Changed", "documentation": "Changed",
    "test": "Changed", "tests": "Changed", "chore": "Changed",
    "remove": "Removed", "removed": "Removed", "delete": "Removed", "deprecate": "Removed",
    "security": "Security", "sec": "Security",
    "deprecated": "Deprecated", "deprecation": "Deprecated",
    "other": "Changed"
}
CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed", "Security", "Deprecated"]

def parse_conventional(msg):
    """Parse conventional commit: type(scope): description"""
    pat = r'^(\w+)(?:\(([^)]*)\))?:\s?(.+)$'
    m = re.match(pat, msg)
    if m:
        return m.group(1), m.group(2) or "", m.group(3)
    return "other", "", msg

def get_last_tag():
    """Get the most recent git tag, if any."""
    return run(["git", "describe", "--tags", "--abbrev=0"])

def get_commits(since=None):
    args = ["git", "log", "--pretty=format:%H||%an||%ae||%ai||%s"]
    if since:
        args.insert(2, f"{since}..HEAD")
    out = run(args)
    if not out:
        return []
    commits = []
    for line in out.split("\n"):
        parts = line.split("||", 4)
        if len(parts) == 5:
            commits.append({
                "hash": parts[0][:7],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })
    return commits

def group_by_category(commits):
    """Group commits into Added/Fixed/Changed/Removed/Security/Deprecated."""
    groups = defaultdict(list)
    for c in commits:
        typ, scope, desc = parse_conventional(c["message"])
        category = CATEGORY_MAP.get(typ, "Changed")
        groups[category].append({**c, "type": typ, "scope": scope, "description": desc})
    return groups

def render_markdown(commits, since):
    groups = group_by_category(commits)
    tag_str = f" [{since}]" if since else ""
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## Changelog{tag_str} - {date_str}\n"]
    
    if since:
        lines.append(f"*Commits since `{since}`*\n")
    
    for cat in CATEGORY_ORDER:
        if cat not in groups: continue
        items = groups[cat]
        lines.append(f"### {cat}")
        for c in items:
            scope = f"**{c['scope']}:** " if c["scope"] else ""
            lines.append(f"- {scope}{c['description']} ([{c['hash']}]({c['hash']}))")
        lines.append("")
    return "\n".join(lines)

def render_json(commits, since):
    return json.dumps({"since": since or "all", "generated": datetime.now().isoformat(), "commits": commits}, indent=2)

def render_html(commits, since):
    md = render_markdown(commits, since)
    body = (md
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('\n', '<br>'))
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Changelog</title><style>
body {{ font-family: system-ui; max-width: 800px; margin: auto; padding: 2em; }}
h2 {{ border-bottom: 2px solid #eee; color: #333; }}
h3 {{ color: #555; margin-top: 1.5em; }}
pre, code {{ background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }}
pre {{ padding: 1em; overflow-x: auto; }}
</style></head><body>
{body}
</body></html>"""
    return html

def main():
    ap = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    ap.add_argument("--tag", "--since", help="Tag or commit to start from (default: auto-detect last tag)")
    ap.add_argument("--format", choices=["markdown", "json", "html"], default="markdown",
                    help="Output format (default: markdown)")
    ap.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = ap.parse_args()

    # Auto-detect last tag if --tag not provided
    tag = args.tag or get_last_tag()
    
    commits = get_commits(tag)
    if not commits:
        print("No commits found. Are you in a git repo?", file=sys.stderr)
        sys.exit(1)

    renderers = {"markdown": render_markdown, "json": render_json, "html": render_html}
    output = renderers[args.format](commits, tag)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✓ Changelog written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
