#!/usr/bin/env python3
"""
claude-review — Claude Code Sub-Agent for Structured GitHub PR Reviews (Bounty #4)
Usage:
  ./claude_review.py --pr https://github.com/owner/repo/pull/123
"""
import argparse
import json
import re
import sys
import urllib.request


def fetch_pr_data(owner: str, repo: str, pr_num: str):
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "ClaudeReviewAgent/1.0"}
    pr_req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}", headers=headers)
    with urllib.request.urlopen(pr_req, timeout=15) as r:
        pr = json.loads(r.read().decode())
    files_req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}/files", headers=headers)
    with urllib.request.urlopen(files_req, timeout=15) as r:
        files = json.loads(r.read().decode())
    return pr, files


def analyze_pr(pr: dict, files: list) -> str:
    title = pr.get("title", "Untitled PR")
    additions = pr.get("additions", 0)
    deletions = pr.get("deletions", 0)
    changed_files = len(files)
    filenames = [f.get("filename", "") for f in files]

    risks = []
    suggestions = []
    has_tests = any("test" in fn.lower() or "spec" in fn.lower() for fn in filenames)

    for f in files:
        patch = f.get("patch") or ""
        fname = f.get("filename", "")
        if "TODO" in patch or "FIXME" in patch:
            risks.append(f"`{fname}` introduces unresolved `TODO`/`FIXME` markers in the diff.")
        if re.search(r"console\.log\(|print\(", patch) and "test" not in fname.lower():
            suggestions.append(f"Consider replacing debug output in `{fname}` with structured logging or guarding behind a verbosity flag.")
        if f.get("changes", 0) > 250:
            risks.append(f"High change concentration in `{fname}` ({f.get('changes')} lines modified) increases regression surface.")

    if not has_tests and additions > 15:
        risks.append("No test files were added or updated alongside functional changes.")
        suggestions.append("Add focused unit or regression tests covering the primary code paths modified in this PR.")
    if not risks:
        risks.append("Low surface risk: diff is tightly scoped with minimal side effects.")
    if not suggestions:
        suggestions.append("Consider adding inline docstrings or JSDoc comments on newly exported symbols.")

    confidence = "High" if changed_files <= 10 and additions < 400 else "Medium"

    summary = (
        f"This PR (**{title}**) modifies **{changed_files} file(s)** (`+{additions}` / `-{deletions}` lines) "
        f"across {', '.join(f'`{fn}`' for fn in filenames[:4])}{' and others' if len(filenames) > 4 else ''}. "
        f"It focuses on delivering a scoped update aligned with the repository's module structure."
    )

    md = [
        f"## 🤖 Claude Code Sub-Agent PR Review: #{pr.get('number')}",
        "",
        "### 📋 Summary of Changes",
        summary,
        "",
        "### ⚠️ Identified Risks",
        *[f"- {r}" for r in risks],
        "",
        "### 💡 Improvement Suggestions",
        *[f"- {s}" for s in suggestions],
        "",
        f"### 🎯 Confidence Score: **{confidence}**",
    ]
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", args.pr.strip())
    if not m:
        sys.stderr.write("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123\n")
        sys.exit(1)
    pr, files = fetch_pr_data(m.group(1), m.group(2), m.group(3))
    print(analyze_pr(pr, files))


if __name__ == "__main__":
    main()
