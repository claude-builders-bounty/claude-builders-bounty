#!/usr/bin/env python3
"""
claude-review — Claude Code PR review agent (CLI)

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr 123 --repo owner/repo
  claude-review --diff /path/to/diff.txt     # local diff file

Outputs structured Markdown review:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Requires: GITHUB_TOKEN env var (read-only repo access) and
ANTHROPIC_API_KEY (Claude API) — or run with --dry-run for a structural review
without AI.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from urllib.error import HTTPError

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def gh_api(url):
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def parse_pr_url(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)

def get_pr_diff(owner, repo, pr_num):
    """Fetch PR diff via GitHub API (diff format)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.diff")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def get_pr_meta(owner, repo, pr_num):
    d = gh_api(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}")
    return {
        "title": d.get("title", ""),
        "body": (d.get("body") or "")[:2000],
        "additions": d.get("additions", 0),
        "deletions": d.get("deletions", 0),
        "changed_files": d.get("changed_files", 0),
    }

def analyze_diff(diff):
    """Heuristic structural analysis of the diff (no AI needed)."""
    risks = []
    suggestions = []
    files_changed = []
    additions = deletions = 0

    # Pattern-based risk detection
    patterns = [
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded credential detected"),
        (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
        (r"eval\s*\(", "Use of eval() — code injection risk"),
        (r"exec\s*\(", "Use of exec() — code injection risk"),
        (r"innerHTML\s*=", "innerHTML assignment — XSS risk"),
        (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML — XSS risk"),
        (r"SELECT\s+\*", "SELECT * — consider explicit columns"),
        (r"DROP\s+TABLE", "DROP TABLE in diff — destructive SQL"),
        (r"DELETE\s+FROM\s+\w+(?!\s+WHERE)", "DELETE without WHERE — destructive SQL"),
        (r"console\.log\(", "Console.log left in code"),
        (r"TODO|FIXME|HACK", "TODO/FIXME/HACK marker left in code"),
        (r"\.env", "Environment file reference — check it's not committed"),
        (r"rm\s+-rf", "rm -rf in diff — destructive command"),
        (r"chmod\s+777", "chmod 777 — overly permissive"),
        (r"http://", "Insecure http:// URL (use https)"),
    ]
    for pat, msg in patterns:
        if re.search(pat, diff, re.IGNORECASE):
            risks.append(msg)

    # File-level stats
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files_changed.append(line[6:])
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        if line.startswith("-") and not line.startswith("---"):
            deletions += 1

    # Structural suggestions
    if additions > 500:
        suggestions.append(f"Large PR ({additions}+ lines added) — consider splitting into smaller reviewable units.")
    if len(files_changed) > 15:
        suggestions.append(f"Many files changed ({len(files_changed)}) — verify scope creep.")
    if not re.search(r"\+.*(test|spec)", diff, re.IGNORECASE):
        suggestions.append("No test files in diff — consider adding tests for the changed behavior.")

    return {
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "risks": risks,
        "suggestions": suggestions,
    }

def claude_review(meta, analysis):
    """Call Claude API for a narrative review. Falls back to heuristic if no key."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    prompt = f"""You are a senior code reviewer. Review this GitHub PR.

PR title: {meta['title']}
PR body: {meta['body'][:1000]}
Files changed: {', '.join(analysis['files_changed'][:20])}
Additions: {analysis['additions']}, Deletions: {analysis['deletions']}

Heuristic risks found: {analysis['risks']}

Write a concise structured review with:
1. Summary of changes (2-3 sentences)
2. Identified risks (bulleted list)
3. Improvement suggestions (bulleted list)
4. Confidence score (Low/Medium/High)
"""
    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
            return d["content"][0]["text"]
    except Exception as e:
        return f"*(Claude API call failed: {e})*"

def render_review(meta, analysis, ai_text):
    conf = "High" if analysis["risks"] else "Medium"
    lines = []
    lines.append(f"## PR Review: {meta['title']}")
    lines.append("")
    lines.append(f"**Files changed:** {len(analysis['files_changed'])} | "
                 f"**+{analysis['additions']}/-{analysis['deletions']}**")
    lines.append("")
    if ai_text:
        lines.append(ai_text)
        lines.append("")
    else:
        lines.append("### Summary of changes")
        lines.append(f"Modifies {len(analysis['files_changed'])} file(s) "
                     f"({analysis['additions']} additions, {analysis['deletions']} deletions).")
        lines.append("")
    lines.append("### Identified risks")
    if analysis["risks"]:
        for r in analysis["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("- None detected by static heuristics.")
    lines.append("")
    lines.append("### Improvement suggestions")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append(f"**Confidence score:** {conf}")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Claude Code PR review agent")
    ap.add_argument("--pr", help="PR URL: https://github.com/owner/repo/pull/123")
    ap.add_argument("--repo", help="owner/repo (with --pr <number>)")
    ap.add_argument("--diff", help="Path to local diff file")
    ap.add_argument("--dry-run", action="store_true", help="Heuristic only, no AI")
    args = ap.parse_args()

    if args.diff:
        with open(args.diff) as f:
            diff = f.read()
        meta = {"title": os.path.basename(args.diff), "body": "", "additions": 0, "deletions": 0, "changed_files": 0}
    elif args.pr and args.repo:
        owner, repo = args.repo.split("/")
        pr_num = args.pr
        diff = get_pr_diff(owner, repo, pr_num)
        meta = get_pr_meta(owner, repo, pr_num)
    elif args.pr and "github.com" in args.pr:
        owner, repo, pr_num = parse_pr_url(args.pr)
        diff = get_pr_diff(owner, repo, pr_num)
        meta = get_pr_meta(owner, repo, pr_num)
    else:
        ap.error("Provide --pr URL, --pr number with --repo, or --diff file")

    analysis = analyze_diff(diff)
    ai_text = None if args.dry_run else claude_review(meta, analysis)
    print(render_review(meta, analysis, ai_text))

if __name__ == "__main__":
    main()
