#!/usr/bin/env python3
"""Claude Code PR reviewer agent — structured Markdown review of a GitHub PR.

Usage:
  python3 pr_reviewer.py --pr https://github.com/owner/repo/pull/123
  python3 pr_reviewer.py --pr owner/repo#123
  python3 pr_reviewer.py --repo owner/repo --number 123

Reads GITHUB_TOKEN from the environment if present (higher rate limit).
Prints a Markdown review to stdout. Exit 0 on success.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

GITHUB_API = "https://api.github.com"


def _request(url: str, token: str | None) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-pr-reviewer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API {exc.code} for {url}: {body[:300]}") from exc


def parse_pr_ref(ref: str) -> tuple[str, int]:
    """Accept https://github.com/o/r/pull/N, o/r#N, or o/r N via --repo/--number."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref)
    if m:
        return f"{m.group(1)}/{m.group(2)}", int(m.group(3))
    m = re.match(r"([^/#]+)/([^/#]+)#(\d+)$", ref)
    if m:
        return f"{m.group(1)}/{m.group(2)}", int(m.group(3))
    raise SystemExit(f"Unrecognized PR reference: {ref}")


def fetch_pr(repo: str, number: int, token: str | None) -> dict:
    return _request(f"{GITHUB_API}/repos/{repo}/pulls/{number}", token)


def fetch_files(repo: str, number: int, token: str | None) -> list[dict]:
    return _request(f"{GITHUB_API}/repos/{repo}/pulls/{number}/files?per_page=100", token)


def classify_risks(pr: dict, files: list[dict]) -> list[str]:
    risks: list[str] = []
    title = (pr.get("title") or "").lower()
    body = pr.get("body") or ""
    paths = [f.get("filename", "") for f in files]

    if any(p.startswith(".github/workflows") or p.endswith(".yml") for p in paths):
        risks.append("Touches CI/workflow YAML — verify secrets and third-party actions are pinned.")
    if any(re.search(r"(auth|token|secret|password|credential)", p, re.I) for p in paths):
        risks.append("Modifies auth/credential-related paths — check for secret leakage and session handling.")
    if any(p.endswith(".sql") or "migration" in p.lower() for p in paths):
        risks.append("Includes migrations/SQL — confirm reversibility and data-loss risk.")
    if re.search(r"breaking|deprecat|remove api", title + body, re.I):
        risks.append("Mentions breaking/deprecation — call out versioning and changelog impact.")
    if any(f.get("deletions", 0) > 200 for f in files):
        risks.append("Large deletions (>200 lines in a file) — confirm tests still cover removed paths.")
    if not files:
        risks.append("No file changes returned by the API — PR may be empty or still loading.")
    if pr.get("draft"):
        risks.append("PR is marked draft — not ready for final merge review.")
    return risks


def suggestions_for(files: list[dict]) -> list[str]:
    tips: list[str] = []
    names = [f.get("filename", "") for f in files]
    if any(n.endswith((".ts", ".tsx", ".js", ".py", ".go", ".rs")) for n in names):
        tips.append("Confirm unit/integration tests run in CI for every touched module.")
    if any("README" in n or n.endswith(".md") for n in names):
        tips.append("Docs changed — ensure examples match the final public API.")
    if any(n.endswith("package.json") or n == "go.mod" or n == "Cargo.toml" for n in names):
        tips.append("Dependency manifest changed — review lockfile and license compatibility.")
    if not tips:
        tips.append("Request a short before/after description from the author for reviewers.")
    tips.append("Check diff for debug prints, TODOs, and accidental generated files.")
    return tips


def confidence(pr: dict, files: list[dict]) -> str:
    score = 0
    if (pr.get("additions") or 0) + (pr.get("deletions") or 0) < 200:
        score += 2
    if len(files) <= 10:
        score += 1
    if (pr.get("body") or "").strip():
        score += 1
    if pr.get("draft"):
        score -= 2
    if any(f.get("deletions", 0) > 500 for f in files):
        score -= 1
    if score >= 3:
        return "High"
    if score >= 1:
        return "Medium"
    return "Low"


def render_markdown(pr: dict, files: list[dict], repo: str, number: int) -> str:
    risks = classify_risks(pr, files)
    tips = suggestions_for(files)
    conf = confidence(pr, files)
    changed = ", ".join(f"`{f.get('filename')}` (+{f.get('additions')}/-{f.get('deletions')})" for f in files[:12])
    if len(files) > 12:
        changed += f" … +{len(files) - 12} more"

    lines = [
        f"## PR Review: {repo}#{number}",
        "",
        f"**Title:** {pr.get('title', '')}  ",
        f"**Author:** {pr.get('user', {}).get('login', '')}  ",
        f"**Base → Head:** `{pr.get('base', {}).get('ref', '')}` → `{pr.get('head', {}).get('ref', '')}`  ",
        f"**Size:** +{pr.get('additions', 0)} / -{pr.get('deletions', 0)} in {pr.get('changed_files', len(files))} file(s)  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "### Summary of changes",
        "",
        (pr.get("body") or "_No description provided._").strip()[:800],
        "",
        "### Files",
        "",
        changed or "_none_",
        "",
        "### Identified risks",
        "",
        *([f"- {r}" for r in risks] if risks else ["- None flagged by heuristics."]),
        "",
        "### Improvement suggestions",
        "",
        *[f"- {s}" for s in tips],
        "",
        f"### Confidence: **{conf}**",
        "",
        f"Link: {pr.get('html_url', f'https://github.com/{repo}/pull/{number}')}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structured GitHub PR review")
    parser.add_argument("--pr", help="PR URL or owner/repo#number")
    parser.add_argument("--repo", help="owner/repo")
    parser.add_argument("--number", type=int, help="PR number")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.pr:
        repo, number = parse_pr_ref(args.pr)
    elif args.repo and args.number:
        repo, number = args.repo, args.number
    else:
        parser.error("Provide --pr URL/ref or --repo and --number")

    pr = fetch_pr(repo, number, token)
    files = fetch_files(repo, number, token)
    print(render_markdown(pr, files, repo, number))
    return 0


if __name__ == "__main__":
    sys.exit(main())
