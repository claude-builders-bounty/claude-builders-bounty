#!/usr/bin/env python3
"""
changelog.py - Auto-generate beautiful changelogs from git history.
Usage: python changelog.py [--since TAG] [--format markdown|json|html] [--output FILE]
"""
import subprocess, json, sys, os, re, argparse
from datetime import datetime
from collections import defaultdict

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        return r.stdout.strip() if r.returncode == 0 else ""
    except: return ""

def parse_conventional(msg):
    """Parse conventional commit: type(scope): description"""
    pat = r'^(\w+)(?:\(([^)]*)\))?:\s?(.+)$'
    m = re.match(pat, msg)
    if m:
        return m.group(1), m.group(2) or "", m.group(3)
    return "other", "", msg

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

def group_commits(commits):
    groups = defaultdict(list)
    order = ["feat", "fix", "docs", "refactor", "perf", "style", "test", "chore", "other"]
    for c in commits:
        typ, scope, desc = parse_conventional(c["message"])
        groups[typ].append({**c, "type": typ, "scope": scope, "description": desc})
    return groups, order

def render_markdown(commits, since):
    groups, order = group_commits(commits)
    labels = {"feat": "Added", "fix": "Fixed", "docs": "Documentation",
              "refactor": "Changed", "perf": "Performance", "style": "Style",
              "test": "Tests", "chore": "Chores", "other": "Other"}
    lines = [f"# Changelog\n", f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*"]
    if since: lines.append(f"*Since: `{since}`*\n")
    for t in order:
        if t not in groups: continue
        items = groups[t]
        lines.append(f"\n## {labels.get(t, t.capitalize())}")
        for c in items:
            scope = f" **{c['scope']}**:" if c["scope"] else ""
            lines.append(f"-{scope} {c['description']} ({c['hash']})")
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
h1 {{ border-bottom: 2px solid #eee; }}
pre {{ background: #f5f5f5; padding: 1em; border-radius: 4px; overflow-x: auto; }}
</style></head><body>
{body}
</body></html>"""
    return html

def main():
    ap = argparse.ArgumentParser(description="Generate changelog from git history")
    ap.add_argument("--since", help="Tag or commit to start from")
    ap.add_argument("--format", choices=["markdown", "json", "html"], default="markdown")
    ap.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = ap.parse_args()

    commits = get_commits(args.since)
    if not commits:
        print("No commits found. Are you in a git repo?", file=sys.stderr)
        sys.exit(1)

    renderers = {"markdown": render_markdown, "json": render_json, "html": render_html}
    output = renderers[args.format](commits, args.since)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Changelog written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
