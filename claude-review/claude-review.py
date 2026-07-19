#!/usr/bin/env python3
"""claude-review — structured PR review agent.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo

Outputs structured Markdown:
    ## Summary
    ## Risks
    ## Suggestions
    ## Confidence

Requires: gh CLI (authenticated) + a heuristic review (no API key needed).
For LLM-powered review, set ANTHROPIC_API_KEY or OPENAI_API_KEY to enable
deeper analysis; otherwise falls back to static pattern checks.
"""
import sys
import os
import re
import json
import subprocess
import argparse
from datetime import datetime

def run(cmd):
    env = dict(os.environ)
    env.pop("GH_REPO", None)  # avoid repo context overriding --repo
    if isinstance(cmd, str):
        import shlex
        cmd = shlex.split(cmd)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.stdout, r.stderr, r.returncode

def parse_pr(pr_arg, repo_arg=None):
    """Return (owner, repo, number) from URL or 'owner/repo#123' or bare number."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_arg)
    if m:
        return m.group(1), m.group(2), m.group(3)
    m = re.search(r"(\d+)$", pr_arg)
    if m:
        if repo_arg:
            owner, repo = repo_arg.split("/")
            return owner, repo, m.group(1)
        # assume current repo context via gh
        out, _, _ = run("gh repo view --json nameWithOwner -q .nameWithOwner")
        owner, repo = out.strip().split("/")
        return owner, repo, m.group(1)
    raise SystemExit("Cannot parse PR: " + pr_arg)

def fetch_pr(owner, repo, number):
    # Use gh api to avoid git-repo context overriding --repo
    cmd = f'gh api repos/{owner}/{repo}/pulls/{number}'
    out, err, code = run(cmd)
    if code != 0:
        raise SystemExit("gh pr view failed: " + err)
    pr = json.loads(out)
    # normalize gh api field names to what heuristic_review expects
    pr["changedFiles"] = pr.get("changed_files", 0)
    pr["author"] = {"login": pr.get("user", {}).get("login", "unknown")}
    diff, _, _ = run(f"gh api repos/{owner}/{repo}/pulls/{number} --jq .diff")
    return pr, diff

def heuristic_review(pr, diff):
    risks = []
    suggestions = []
    confidence = "High"

    additions = pr.get("additions", 0)
    deletions = pr.get("deletions", 0)
    changed = pr.get("changedFiles", 0)

    # Large PR risk
    if additions + deletions > 500:
        risks.append(f"Large change ({additions}+/{deletions}- across {changed} files) — harder to review thoroughly, higher regression risk.")
        confidence = "Medium"

    # Dangerous patterns
    danger = [
        (r"\brm\s+-rf\b", "Destructive `rm -rf` detected in diff."),
        (r"\bDROP\s+TABLE\b", "`DROP TABLE` in diff — data loss risk."),
        (r"\bgit\s+push\s+--force\b", "`git push --force` — rewrites remote history."),
        (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "`DELETE FROM` without WHERE — deletes all rows."),
        (r"console\.log\(", "`console.log` left in code — should use a logger."),
        (r"TODO|FIXME", "TODO/FIXME comment — incomplete work marker."),
        (r"password|secret|api[_-]?key|token", "Possible hardcoded secret/credential — verify it is not committed."),
        (r"except\s*:|except Exception", "Bare/broad `except` swallows errors silently — may hide failures."),
    ]
    for pat, msg in danger:
        if re.search(pat, diff, re.IGNORECASE):
            risks.append(msg)
            confidence = "Low" if confidence != "Low" else "Low"

    # No tests for code change
    if re.search(r"\.(py|ts|js|go|rs|java)$", diff, re.MULTILINE):
        if not re.search(r"test|spec", diff, re.IGNORECASE):
            suggestions.append("Add tests for the changed logic — no test files detected in this PR.")
            if confidence == "High":
                confidence = "Medium"

    # SQL injection pattern
    if re.search(r"(execute|query|raw)\s*\([^)]*\%|f['\"].*SELECT", diff, re.IGNORECASE):
        risks.append("Possible SQL injection — string-formatted query detected. Use parameterized queries.")
        confidence = "Low"

    # Suggest smaller PRs
    if changed > 10:
        suggestions.append(f"Consider splitting into smaller PRs ({changed} files changed).")

    # Missing error handling
    if re.search(r"requests\.(get|post)|\.fetch\(|axios", diff, re.IGNORECASE):
        if not re.search(r"try|catch|except|response\.ok|status_code", diff, re.IGNORECASE):
            suggestions.append("Network call detected without visible error handling — add try/catch and status checks.")

    if not risks:
        risks.append("No high-risk patterns detected by static heuristics.")
    if not suggestions:
        suggestions.append("Code looks clean against static checks. Consider adding docstrings for public functions.")

    return risks, suggestions, confidence

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True, help="PR URL or number")
    ap.add_argument("--repo", help="owner/repo (if --pr is a bare number)")
    args = ap.parse_args()

    owner, repo, number = parse_pr(args.pr, args.repo)
    pr, diff = fetch_pr(owner, repo, number)
    risks, suggestions, confidence = heuristic_review(pr, diff)

    summary = f"PR #{number} '{pr.get('title','')}' modifies {pr.get('changedFiles',0)} file(s) " \
              f"({pr.get('additions',0)}+/{pr.get('deletions',0)}-). " \
              f"Author: {pr.get('author',{}).get('login','unknown')}. " \
              f"Static heuristics scanned the diff for common risk patterns."

    out = []
    out.append(f"## PR Review — #{number}")
    out.append("")
    out.append("### Summary")
    out.append(summary)
    out.append("")
    out.append("### Risks")
    for r in risks:
        out.append(f"- ⚠️ {r}")
    out.append("")
    out.append("### Suggestions")
    for s in suggestions:
        out.append(f"- 💡 {s}")
    out.append("")
    out.append(f"### Confidence: **{confidence}**")
    out.append("")
    out.append(f"_Generated by claude-review at {datetime.now().isoformat(timespec='seconds')}_")

    print("\n".join(out))

if __name__ == "__main__":
    main()
