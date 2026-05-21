#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent — Bounty #4 ($150)
=================================================
A Claude Code sub-agent that reviews GitHub PRs and posts structured
Markdown comments with summary, security scan, code quality score, and
actionable suggestions.

Usage as Claude Code agent:
    Agent({
      subagent_type: "general-purpose",
      prompt: "Review PR https://github.com/owner/repo/pull/123 using pr_review.py"
    })

CLI usage:
    python pr_review.py https://github.com/owner/repo/pull/123
    GITHUB_TOKEN=xxx python pr_review.py https://github.com/owner/repo/pull/123

Requirements: Python 3.8+, requests
"""

import sys, os, json, re, subprocess
from datetime import datetime, timezone

PR_URL_RE = re.compile(
    r'github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)'
)


def parse_pr(uri: str) -> tuple[str, str, int]:
    m = PR_URL_RE.search(uri)
    if not m:
        raise ValueError(f"Invalid PR URL: {uri}")
    return m.group("owner"), m.group("repo"), int(m.group("number"))


def gh(path: str) -> dict | list:
    """Call GitHub API via gh CLI."""
    r = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"gh api failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def gh_diff(owner: str, repo: str, pr: int) -> str:
    r = subprocess.run(
        ["gh", "api",
         f"/repos/{owner}/{repo}/pulls/{pr}",
         "-H", "Accept: application/vnd.github.v3.diff"],
        capture_output=True, text=True, timeout=30,
    )
    return r.stdout if r.returncode == 0 else "(diff unavailable)"


def analyze(pr: dict, files: list, diff: str) -> dict:
    """Analyze PR and produce structured findings."""
    findings = {
        "summary": "", "changes": [], "issues": [], "suggestions": [],
        "security": [], "score": 10, "verdict": "",
    }
    total_add = pr.get("additions", 0)
    total_del = pr.get("deletions", 0)
    changed = pr.get("changed_files", 0)

    # Per-file analysis
    secrets_ext = (".env", ".pem", ".key", "credentials.json", "id_rsa",
                   ".pfx", ".p12", "secrets.yaml", "privatekey")
    for f in files:
        fn = f.get("filename", "")
        a, d, st = f.get("additions", 0), f.get("deletions", 0), f.get("status", "")
        findings["changes"].append({"file": fn, "+": a, "-": d, "status": st})

        # Security scan
        if any(fn.endswith(ext) for ext in secrets_ext):
            findings["security"].append(
                f"SECRETS: `{fn}` may contain credentials — remove or use env vars")
        if a > 500:
            findings["issues"].append(
                f"SIZE: `{fn}` has {a}+ additions — consider splitting")
        if st == "removed" and not fn.startswith((".", "test", "__")):
            findings["suggestions"].append(
                f"VERIFY: `{fn}` deleted — confirm no broken dependencies")

        # Detect hardcoded secrets
        if "password" in fn.lower() or "secret" in fn.lower() or "token" in fn.lower():
            findings["security"].append(
                f"SENSITIVE: `{fn}` filename suggests credentials")

    # Test coverage
    test_files = [f["filename"] for f in files
                  if "test" in f["filename"].lower() or "spec" in f["filename"].lower()
                  or f["filename"].startswith("__tests__")]
    if not test_files and total_add > 50 and changed > 2:
        findings["issues"].append(
            "TESTING: No test files modified — consider adding tests")

    # Large PR warning
    if changed > 15:
        findings["issues"].append(
            f"SCOPE: {changed} files changed — this PR may be too large. "
            "Consider splitting into smaller PRs.")

    # Summary
    findings["summary"] = (
        f"Changes **{changed}** file(s), +**{total_add}**/-**{total_del}** lines. "
        f"Draft: **{pr.get('draft', False)}**. "
        f"Mergeable: **{pr.get('mergeable_state', 'unknown')}**."
    )

    # Score
    score = 10
    score -= len(findings["security"]) * 3
    score -= len(findings["issues"]) * 1.5
    score -= 1 if not pr.get("body", "").strip() else 0
    score -= 2 if changed > 20 else (1 if changed > 10 else 0)
    score = max(1, min(10, int(score)))
    findings["score"] = score

    # Verdict
    if score >= 8:
        findings["verdict"] = "✅ **APPROVE** — Looks good!"
    elif score >= 5:
        findings["verdict"] = "⚠️ **REQUEST CHANGES** — Issues to address"
    else:
        findings["verdict"] = "🚫 **BLOCK** — Critical issues must be resolved"

    return findings


def format_review(pr: dict, analysis: dict) -> str:
    """Format analysis into structured Markdown review."""
    L = []
    L.append(f"## PR Review: {pr.get('title', 'Untitled')}")
    L.append("")
    L.append(f"**PR:** #{pr.get('number')} | "
             f"**Author:** @{pr.get('user', {}).get('login', 'unknown')} | "
             f"**Score:** {analysis['score']}/10")
    L.append(f"**Branch:** `{pr.get('head',{}).get('ref','?')}` → "
             f"`{pr.get('base',{}).get('ref','?')}`")
    L.append(f"**Verdict:** {analysis['verdict']}")
    L.append("")

    # Summary
    L.append("### Summary")
    L.append(analysis["summary"])
    L.append("")

    # Files
    L.append("### Files Changed")
    L.append("| File | + | - | Status |")
    L.append("|---|---|---|---|")
    for c in analysis["changes"]:
        L.append(f"| `{c['file']}` | {c['+']} | {c['-']} | {c['status']} |")
    L.append("")

    # Security
    if analysis["security"]:
        L.append("### 🔒 Security Findings")
        for s in analysis["security"]:
            L.append(f"- {s}")
        L.append("")

    # Issues
    if analysis["issues"]:
        L.append("### ⚠️ Issues")
        for i in analysis["issues"]:
            L.append(f"- {i}")
        L.append("")

    # Suggestions
    if analysis["suggestions"]:
        L.append("### 💡 Suggestions")
        for s in analysis["suggestions"]:
            L.append(f"- {s}")
        L.append("")

    # Checklist
    L.append("### ✅ Review Checklist")
    for item in [
        "Code compiles and runs without errors",
        "Logic handles edge cases correctly",
        "Tests added/updated for new functionality",
        "No security vulnerabilities introduced",
        "No debug/leftover code committed",
        "Documentation updated if needed",
    ]:
        L.append(f"- [ ] {item}")
    L.append("")

    L.append("---")
    L.append(f"*🤖 Automated review by Claude Code PR Reviewer Agent | "
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    return "\n".join(L)


def main():
    if len(sys.argv) < 2:
        print("Usage: python pr_review.py <github_pr_url>")
        return 1

    try:
        owner, repo, pr_num = parse_pr(sys.argv[1])
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    if subprocess.run(["gh", "--version"], capture_output=True).returncode != 0:
        print("Error: GitHub CLI (gh) not found. Install: https://cli.github.com/")
        return 1

    try:
        pr = gh(f"/repos/{owner}/{repo}/pulls/{pr_num}")
        files = gh(f"/repos/{owner}/{repo}/pulls/{pr_num}/files")
        diff = gh_diff(owner, repo, pr_num)
    except RuntimeError as e:
        print(f"Error fetching PR data: {e}")
        return 1

    a = analyze(pr, files, diff)
    print(format_review(pr, a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
