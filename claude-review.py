#!/usr/bin/env python3
"""claude-review.py — Analyze a GitHub PR and emit a structured Markdown review.

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --pr 123 --repo owner/repo

Outputs a structured review (Summary / Risks / Suggestions / Confidence).
Uses only the GitHub API (no Claude call required, so it runs offline);
the "analysis" is heuristic so it is deterministic and testable.
"""
import sys
import os
import re
import json
import urllib.request
import urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"


def _get(path):
    req = urllib.request.Request(f"{API}{path}", headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review/1.0",
    })
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode())


def parse_pr(pr_arg):
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_arg)
    if m:
        return f"{m.group(1)}/{m.group(2)}", int(m.group(3))
    repo_m = re.search(r"([^/]+)/([^/]+)", pr_arg)
    num = re.search(r"(\d+)", pr_arg)
    if repo_m and num:
        return repo_m.group(1) + "/" + repo_m.group(2), int(num.group(1))
    raise SystemExit("Cannot parse PR argument. Use --pr URL or --pr owner/repo#123")


def review(repo, num):
    pr = _get(f"/repos/{repo}/pulls/{num}")
    files = _get(f"/repos/{repo}/pulls/{num}/files?per_page=100")
    commits = _get(f"/repos/{repo}/pulls/{num}/commits?per_page=100")

    added = sum(f.get("additions", 0) for f in files)
    removed = sum(f.get("deletions", 0) for f in files)
    risk_files = [f["filename"] for f in files if any(
        k in f["filename"] for k in ("security", "auth", "migrat", "schema", "config"))]
    big = [f["filename"] for f in files if f.get("changes", 0) > 300]

    risks = []
    if risk_files:
        risks.append(f"Touches sensitive areas: {', '.join(risk_files)}")
    if big:
        risks.append(f"Very large diffs (>{300} lines): {', '.join(big)}")
    if added > 500:
        risks.append("Large net addition — higher chance of undetected bugs.")
    if not risks:
        risks.append("No high-risk areas detected by heuristics.")

    suggestions = []
    langs = set()
    for f in files:
        if f["filename"].endswith((".ts", ".tsx", ".js")): langs.add("TypeScript/JS")
        if f["filename"].endswith(".py"): langs.add("Python")
    if "Python" in langs and not any("test" in f["filename"].lower() for f in files):
        suggestions.append("Add tests for the Python changes.")
    if any(f["filename"].endswith((".yml", ".yaml")) for f in files):
        suggestions.append("Validate CI/YAML syntax.")
    if not suggestions:
        suggestions.append("LGTM — consider a quick manual smoke test.")

    # Confidence heuristic
    if added + removed < 100 and not risk_files:
        conf = "High"
    elif added + removed < 400:
        conf = "Medium"
    else:
        conf = "Low"

    summary = (f"PR #{num} \"{pr.get('title','')}\" by {pr.get('user',{}).get('login','?')} "
               f"modifies {len(files)} file(s), +{added}/-{removed} across "
               f"{len(commits)} commit(s). State: {pr.get('state')}.")

    return f"""## PR Review — #{num}

**Summary**
{summary}

**Identified Risks**
{chr(10).join('- ' + r for r in risks)}

**Improvement Suggestions**
{chr(10).join('- ' + s for s in suggestions)}

**Confidence:** {conf}
"""


def main():
    args = sys.argv[1:]
    if "--pr" not in args:
        raise SystemExit("Usage: claude-review.py --pr <url-or-repo#num>")
    pr_arg = args[args.index("--pr") + 1]
    repo, num = parse_pr(pr_arg)
    print(review(repo, num))


if __name__ == "__main__":
    main()
