#!/usr/bin/env python3
"""Dry-run weekly summary logic using live GitHub API (bounty #5 evidence)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from submit_bounty_pr import load_env_file, require_env

OUT = Path(__file__).resolve().parent / "samples" / "dry-run-execution.md"


def gh_get(url: str, token: str) -> list | dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "weekly-summary-dry-run",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    load_env_file(ROOT / "env.txt")
    token = require_env("GITHUB_TOKEN")

    repo = os.environ.get("GITHUB_REPO", "claude-builders-bounty/claude-builders-bounty")
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")

    commits = gh_get(
        f"https://api.github.com/repos/{repo}/commits?since={since}&per_page=30",
        token,
    )
    issues = gh_get(
        f"https://api.github.com/repos/{repo}/issues?state=closed&since={since}&per_page=30",
        token,
    )
    pulls = gh_get(
        f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30",
        token,
    )
    merged = [p for p in pulls if p.get("merged_at")]

    lines = [
        "# Weekly dev summary — dry-run execution log",
        "",
        f"- **Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Repo:** `{repo}`",
        f"- **Window:** since `{since}`",
        f"- **Method:** Same GitHub API calls as n8n workflow nodes (no n8n UI on CI host)",
        "",
        "## Fetched counts",
        f"- Commits: {len(commits)}",
        f"- Closed issues: {len(issues)}",
        f"- Merged PRs (filtered): {len(merged)}",
        "",
        "## Sample commits",
    ]
    for c in commits[:8]:
        msg = (c.get("commit", {}).get("message", "") or "").split("\n")[0]
        lines.append(f"- {msg[:80]}")

    lines += ["", "## Sample merged PRs"]
    for p in merged[:8]:
        lines.append(f"- #{p['number']} {p['title'][:70]}")

    lines += [
        "",
        "## Narrative preview (template — Claude node uses same inputs)",
        "",
        f"Over the past week, `{repo}` had {len(commits)} commits, "
        f"{len(issues)} closed issues, and {len(merged)} merged PRs. "
        "The n8n workflow passes this payload to `claude-sonnet-4-20250514` "
        "and posts the result to `DELIVERY_WEBHOOK_URL`.",
        "",
        "## n8n manual test checklist",
        "1. Import `n8n-weekly-dev-summary.workflow.json`",
        "2. Set env: GITHUB_REPO, ANTHROPIC_API_KEY, DELIVERY_WEBHOOK_URL, SUMMARY_LANGUAGE",
        "3. Execute workflow once — screenshot execution panel for maintainer",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
