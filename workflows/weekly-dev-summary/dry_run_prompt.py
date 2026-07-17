#!/usr/bin/env python3
"""Dry-run the GitHub fetch + prompt build path used by the n8n workflow."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

OWNER = os.environ.get("GITHUB_OWNER", "claude-builders-bounty")
REPO = os.environ.get("GITHUB_REPO", "claude-builders-bounty")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
SINCE = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
SINCE_DAY = SINCE[:10]


def gh(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "n8n-weekly-dev-summary-dryrun",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    commits = gh(
        f"https://api.github.com/repos/{OWNER}/{REPO}/commits?since={urllib.parse.quote(SINCE)}&per_page=50"
    )
    issues = gh(
        f"https://api.github.com/repos/{OWNER}/{REPO}/issues?state=closed&since={urllib.parse.quote(SINCE)}&per_page=50"
    )
    q = urllib.parse.quote(
        f"repo:{OWNER}/{REPO} is:pr is:merged merged:>{SINCE_DAY}"
    )
    prs = gh(f"https://api.github.com/search/issues?q={q}&per_page=50")
    commit_lines = [
        f"- {(c.get('commit') or {}).get('message', '').splitlines()[0]} ({(c.get('sha') or '')[:7]})"
        for c in (commits if isinstance(commits, list) else [])
    ][:40]
    issue_lines = [
        f"- #{i.get('number')} {i.get('title')}"
        for i in (issues if isinstance(issues, list) else [])
        if not i.get("pull_request")
    ][:30]
    pr_items = prs.get("items") if isinstance(prs, dict) else []
    pr_lines = [f"- #{p.get('number')} {p.get('title')}" for p in pr_items][:30]
    prompt = "\n".join(
        [
            "You are an engineering manager writing a weekly repo narrative.",
            "Write the summary in English.",
            f"Repo: {OWNER}/{REPO}",
            f"Window since: {SINCE}",
            "## Commits",
            "\n".join(commit_lines) or "(none)",
            "## Closed issues",
            "\n".join(issue_lines) or "(none)",
            "## Merged PRs",
            "\n".join(pr_lines) or "(none)",
            "Write: 1) headline 2) what shipped 3) risks/follow-ups 4) metric counts. Keep under 400 words.",
        ]
    )
    out = {
        "repo": f"{OWNER}/{REPO}",
        "since": SINCE,
        "counts": {
            "commits": len(commit_lines),
            "issues": len(issue_lines),
            "prs": len(pr_lines),
        },
        "prompt_preview": prompt[:1500],
        "ok": True,
    }
    Path("dry_run_result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
