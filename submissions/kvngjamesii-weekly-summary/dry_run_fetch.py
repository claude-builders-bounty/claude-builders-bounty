#!/usr/bin/env python3
"""Dry-run: fetch 7d GitHub activity and write a local summary stub (no n8n required)."""
from __future__ import annotations
import json, os, urllib.request
from datetime import datetime, timedelta, timezone

OWNER = os.environ.get("GITHUB_OWNER", "cli")
REPO = os.environ.get("GITHUB_REPO", "cli")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

def get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "kvngjamesii-weekly-summary",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

commits = get(f"https://api.github.com/repos/{OWNER}/{REPO}/commits?since={since}&per_page=100")
issues = [i for i in get(f"https://api.github.com/repos/{OWNER}/{REPO}/issues?state=closed&since={since}&per_page=100") if "pull_request" not in i]
prs = get(f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=50")
merged = [p for p in prs if p.get("merged_at") and p["merged_at"] >= since]

out = {
  "repo": f"{OWNER}/{REPO}",
  "since": since,
  "stats": {"commits": len(commits), "closed_issues": len(issues), "merged_prs": len(merged)},
  "commit_subjects": [(c.get("commit") or {}).get("message", "").split("\n")[0] for c in commits[:15]],
  "merged_pr_titles": [p["title"] for p in merged[:15]],
}
path = os.path.join(os.path.dirname(__file__), "assets", "dry-run-fetch.json")
with open(path, "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out["stats"]))
print("wrote", path)
