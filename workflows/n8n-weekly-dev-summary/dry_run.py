#!/usr/bin/env python3
"""Dry-run the weekly summary data pipeline without n8n (issue #5 verification)."""
import argparse
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone


def gh_get(path: str, token: str, params: dict | None = None) -> list | dict:
    q = ""
    if params:
        q = "&".join(f"{k}={v}" for k, v in params.items())
        q = "?" + q
    url = f"https://api.github.com{path}{q}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "neo-bounty-dry-run",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="owner/repo")
    p.add_argument("--language", default="EN", choices=["EN", "FR"])
    args = p.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN required")
    owner, repo = args.repo.split("/", 1)
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    commits = gh_get(f"/repos/{owner}/{repo}/commits", token, {"since": since, "per_page": "100"})
    issues = gh_get(
        f"/repos/{owner}/{repo}/issues",
        token,
        {"state": "closed", "since": since, "per_page": "100"},
    )
    prs_raw = gh_get(
        f"/repos/{owner}/{repo}/pulls",
        token,
        {"state": "closed", "sort": "updated", "direction": "desc", "per_page": "100"},
    )
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    issues_only = [i for i in issues if "pull_request" not in i]
    merged_prs = [
        pr for pr in prs_raw
        if pr.get("merged_at") and datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")) >= since_dt
    ]
    stats = {"commits": len(commits), "issues": len(issues_only), "prs": len(merged_prs)}
    print(json.dumps({"repo": args.repo, "since": since, "stats": stats}, indent=2))
    print("OK — pipeline fetched GitHub data successfully")


if __name__ == "__main__":
    main()
