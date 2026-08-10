#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude-review.py — Analyze a GitHub PR and output a structured Markdown review.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --repo owner/repo --pr 123

Output: structured Markdown with Summary / Risks / Suggestions / Confidence.
Requires: a GitHub token (env GH_TOKEN) for private repos; works without for public.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")

# --- risk heuristics -------------------------------------------------------
RISK_PATTERNS = [
    (re.compile(r"(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{8,}", re.IGNORECASE),
     "Hardcoded credential-like literal (password/secret/token) in code"),
    (re.compile(r"print\(|console\.log|printf\(|System\.out\.print", re.IGNORECASE),
     "Debug output left in production code"),
    (re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
     "Unresolved TODO/FIXME marker in the diff"),
    (re.compile(r"\bexcept\s*(Exception|BaseException)?\s*:\s*pass", re.IGNORECASE),
     "Bare except with pass — silently swallows errors"),
    (re.compile(r"(DROP\s+TABLE|TRUNCATE\s+|DELETE\s+FROM\s+\w+\s*;?\s*$)", re.IGNORECASE),
     "Destructive SQL operation in the diff"),
    (re.compile(r"\.gitignore|\.env[^.]", re.IGNORECASE),
     "Sensitive config file (.env/.gitignore) appears in the PR"),
    (re.compile(r"eval\(|exec\(|subprocess\.(run|call|Popen)\([^)]*shell=True", re.IGNORECASE),
     "Unsafe eval/exec or shell=True subprocess"),
]
IMPROVEMENT_PATTERNS = [
    (re.compile(r"\.py$", re.IGNORECASE), "Add unit tests for the new logic"),
    (re.compile(r"\.(md|rst)$", re.IGNORECASE), "Consider adding usage examples to the docs"),
    (re.compile(r"\.(ts|tsx|js|jsx)$", re.IGNORECASE), "Add TypeScript types / PropTypes for new props"),
]

def gh(path):
    r = urllib.request.Request(f"{API}{path}", headers={
        "User-Agent": "claude-review", "Accept": "application/vnd.github+json",
        **({"Authorization": f"token {TOKEN}"} if TOKEN else {})})
    try:
        with urllib.request.urlopen(r, timeout=45, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.read().decode(errors='replace')[:200]}")

def parse_pr(arg):
    m = re.match(r"https?://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)", arg)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise SystemExit("Invalid PR URL — expected https://github.com/owner/repo/pull/N")

def main():
    ap = argparse.ArgumentParser(description="Structured PR review")
    ap.add_argument("--pr", required=True, help="PR URL or owner/repo#N")
    ap.add_argument("--output", default="review.md", help="Output file (default: review.md)")
    args = ap.parse_args()

    if "/pull/" in args.pr:
        owner, repo, num = parse_pr(args.pr)
    else:
        m = re.match(r"([\w.-]+)/([\w.-]+)#(\d+)", args.pr)
        if not m:
            raise SystemExit("Use --pr https://github.com/owner/repo/pull/N or owner/repo#N")
        owner, repo, num = m.groups()
        num = int(num)

    pr = gh(f"/repos/{owner}/{repo}/pulls/{num}")
    files = gh(f"/repos/{owner}/{repo}/pulls/{num}/files?per_page=100")
    total_added = sum(f.get("additions", 0) for f in files)
    total_deleted = sum(f.get("deletions", 0) for f in files)
    diff_text = "\n".join(f.get("patch", "") for f in files)

    # Collect risks + suggestions
    risks, suggestions = [], []
    for pat, msg in RISK_PATTERNS:
        if pat.search(diff_text):
            risks.append(msg)
    for f in files:
        fn = f.get("filename", "")
        if fn.endswith(".py") and f.get("additions", 0) > 20 and "test" not in fn.lower():
            suggestions.append("Add unit tests for the new Python logic")
            break
        if fn.lower().endswith((".md", ".rst")) and f.get("additions", 0) > 30:
            suggestions.append("Consider adding usage examples to the documentation")
            break
    if len(files) > 10:
        risks.append(f"Large PR: {len(files)} files changed — consider splitting for easier review")

    confidence = "High" if total_added <= 300 and total_deleted <= 100 else ("Medium" if total_added <= 800 else "Low")

    out = []
    out.append(f"## 🔍 PR Review: {owner}/{repo}#{num}")
    out.append("")
    title = pr.get("title", "")
    body = (pr.get("body") or "").replace("\n", " ")[:200]
    out.append(f"**Summary:** \"{title}\" — {total_added} additions, {total_deleted} deletions across {len(files)} files. {body}")
    out.append("")
    out.append("### ⚠️ Identified Risks")
    if risks:
        for r in risks:
            out.append(f"- {r}")
    else:
        out.append("- None detected by static heuristics.")
    out.append("")
    out.append("### 💡 Improvement Suggestions")
    if suggestions:
        for s in suggestions:
            out.append(f"- {s}")
    else:
        out.append("- None — the change is well-scoped.")
    out.append("")
    out.append(f"### 🎯 Confidence Score: **{confidence}**")
    out.append("")
    out.append(f"*Generated by claude-review (rule-based heuristics). Checked {len(files)} files.*")

    text = "\n".join(out)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
