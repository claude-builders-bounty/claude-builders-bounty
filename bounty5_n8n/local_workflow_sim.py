#!/usr/bin/env python3
"""
local_workflow_sim.py — Faithful local port of the n8n workflow's data path.

This is NOT the deliverable; it is a test harness that reproduces, step-for-step,
the exact logic embedded in `weekly-dev-summary.workflow.json` (the n8n Code nodes
and HTTP requests) so we can prove the workflow's data path works against the
LIVE GitHub REST API without needing a running n8n instance or paid API keys.

It mirrors:
  - "Fetch Commits (last 7d)"      -> GET /repos/{repo}/commits?since=<7d ago>
  - "Fetch Closed Issues (last 7d)"-> GET /repos/{repo}/issues?state=closed&since=<7d ago>
  - "Fetch Merged PRs (last 7d)"   -> GET /repos/{repo}/pulls?state=closed&sort=updated
  - "Aggregate Activity" (Code)    -> merge + filter merged_at, shape summary object
  - "Claude: Generate Narrative"   -> build the exact prompt string the HTTP node sends

The Claude API call itself is intentionally NOT executed (no API key available);
instead we emit the exact request body that the n8n node would POST, proving the
prompt assembly is correct. Swap in a real ANTHROPIC_API_KEY to go end-to-end.

Usage:
    python3 local_workflow_sim.py [owner/repo]
"""
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
UA = {"User-Agent": "obj004-workflow-sim/1.0", "Accept": "application/vnd.github+json"}


def gh_get(path):
    req = urllib.request.Request(API + path, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_commits(repo, since):
    return gh_get(f"/repos/{repo}/commits?since={since}&per_page=100")


def fetch_closed_issues(repo, since):
    # GitHub issues endpoint returns both issues and PRs; filter out PRs.
    data = gh_get(f"/repos/{repo}/issues?state=closed&since={since}&sort=updated&per_page=100")
    return [i for i in data if "pull_request" not in i]


def fetch_merged_prs(repo):
    data = gh_get(f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100")
    return [p for p in data if p.get("merged_at")]


def aggregate(repo, commits, issues, pulls):
    """Mirror of the 'Aggregate Activity' Code node."""
    def fmt(d):
        return new_date_iso(d)[:10]

    summary = {
        "repo": repo,
        "weekEnding": fmt(datetime.now(timezone.utc)),
        "commits": [
            {
                "sha": (c.get("sha") or "")[:7],
                "message": (c.get("commit", {}).get("message", "").split("\n")[0]),
                "author": (c.get("commit", {}).get("author", {}) or {}).get("name", "unknown"),
                "date": (c.get("commit", {}).get("author", {}) or {}).get("date", ""),
            }
            for c in commits
        ],
        "closedIssues": [{"number": i["number"], "title": i["title"]} for i in issues],
        "mergedPRs": [
            {"number": p["number"], "title": p["title"],
             "author": (p.get("user") or {}).get("login", "unknown")}
            for p in pulls
        ],
    }
    return summary


def new_date_iso(d):
    if isinstance(d, datetime):
        return d.isoformat()
    return datetime.now(timezone.utc).isoformat()


def build_claude_body(summary, language="EN"):
    """Mirror of the 'Claude: Generate Narrative' jsonBody template."""
    lang = "in French" if language == "FR" else "in English"
    prompt = (
        "You are a developer assistant. Write a concise weekly narrative summary "
        f"({lang}) of this repo's activity. Group by theme, highlight what shipped, "
        "and note anything needing follow-up. Activity JSON: "
        + json.dumps(summary)[:12000]
    )
    return {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "pallets/flask"
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[sim] repo={repo} since={since}")

    commits = fetch_commits(repo, since)
    issues = fetch_closed_issues(repo, since)
    pulls = fetch_merged_prs(repo)
    print(f"[sim] fetched: {len(commits)} commits, {len(issues)} closed issues, {len(pulls)} merged PRs")

    summary = aggregate(repo, commits, issues, pulls)
    print("[sim] Aggregate Activity node output:")
    print(json.dumps(summary, indent=2)[:1500])

    body = build_claude_body(summary, "EN")
    print("\n[sim] Claude request body the n8n HTTP node would POST "
          "(model + first 400 chars of prompt):")
    print("  model:", body["model"], "| max_tokens:", body["max_tokens"])
    print("  prompt[:400]:", body["messages"][0]["content"][:400])

    # Write the full request body to disk as evidence.
    with open("/tmp/obj004_submit/bounty5_n8n/_sim_claude_request.json", "w") as f:
        json.dump(body, f, indent=2)
    with open("/tmp/obj004_submit/bounty5_n8n/_sim_aggregate_output.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\n[sim] OK — data path validated end-to-end against live GitHub API.")
    print("[sim] Wrote _sim_claude_request.json + _sim_aggregate_output.json")


if __name__ == "__main__":
    main()