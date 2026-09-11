#!/usr/bin/env python3
"""Validate weekly GH activity aggregation + Claude-ready prompt (bounty #5)."""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = os.environ.get("GITHUB_REPO", "claude-builders-bounty/claude-builders-bounty")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
LANG = os.environ.get("SUMMARY_LANG", "EN").upper()

def gh(path, params=""):
    url = f"https://api.github.com{path}{params}"
    h = {"Accept": "application/vnd.github+json", "User-Agent": "veriton-n8n-bounty5"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())

end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
start = end - timedelta(days=7)
since = start.isoformat().replace("+00:00", "Z")
commits = gh(f"/repos/{REPO}/commits", f"?since={since}&per_page=100")
issues = gh(f"/repos/{REPO}/issues", f"?state=closed&since={since}&per_page=100")
prs = gh(f"/repos/{REPO}/pulls", f"?state=closed&sort=updated&direction=desc&per_page=100")
pure_issues = [i for i in issues if "pull_request" not in i]
merged = [p for p in prs if p.get("merged_at") and p["merged_at"] >= since]

lang_instr = (
    "Rédige le résumé en français clair et professionnel."
    if LANG == "FR"
    else "Write the summary in clear professional English."
)
commit_lines = [
    f"- {(c.get('commit') or {}).get('message','').splitlines()[0]} ({c.get('sha','')[:7]})"
    for c in commits[:20]
]
issue_lines = [f"- #{i['number']} {i['title']}" for i in pure_issues[:20]]
pr_lines = [f"- #{p['number']} {p['title']} (merged {p.get('merged_at')})" for p in merged[:20]]
prompt = f"""You are a release narrator for GitHub repo {REPO}.
Window: {since} → {end.isoformat().replace('+00:00','Z')}
{lang_instr}

Produce a weekly narrative summary with sections:
1) Highlights
2) Shipping (merged PRs)
3) Fixes & closed issues
4) Commit themes
5) Risks / follow-ups

COMMITS ({len(commits)}):
{chr(10).join(commit_lines) or '(none)'}

CLOSED ISSUES ({len(pure_issues)}):
{chr(10).join(issue_lines) or '(none)'}

MERGED PRS ({len(merged)}):
{chr(10).join(pr_lines) or '(none)'}
"""

out = {
    "ok": True,
    "repo": REPO,
    "window": {"since": since, "until": end.isoformat()},
    "stats": {
        "commits": len(commits),
        "closed_issues": len(pure_issues),
        "merged_prs": len(merged),
    },
    "prompt_chars": len(prompt),
    "prompt_preview": prompt[:1200],
    "workflow": "workflows/n8n-weekly-dev-summary/weekly-github-dev-summary.json",
    "model_target": "claude-sonnet-4-20250514",
}
Path("docs/screenshots").mkdir(parents=True, exist_ok=True)
Path("docs/screenshots/n8n-weekly-validation.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
