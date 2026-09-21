#!/usr/bin/env python3
"""Dry-run the weekly summary data pull (stdlib). Optional Claude call."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

def gh(path: str, token: str | None):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "n8n-weekly-summary-dryrun",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPO", "expressjs/express"))
    p.add_argument("--lang", default=os.environ.get("SUMMARY_LANG", "EN"))
    p.add_argument("--call-claude", action="store_true")
    args = p.parse_args()
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    commits = gh(f"/repos/{args.repo}/commits?since={since}&per_page=30", token)
    issues = gh(f"/repos/{args.repo}/issues?state=closed&since={since}&per_page=30", token)
    prs = gh(f"/repos/{args.repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30", token)
    since_ts = dt.datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
    closed_issues = [i for i in issues if "pull_request" not in i][:20]
    merged = [p for p in prs if p.get("merged_at") and dt.datetime.fromisoformat(p["merged_at"].replace("Z", "+00:00")).timestamp() >= since_ts][:20]
    commit_rows = [{"sha": c["sha"][:7], "message": c["commit"]["message"].split("\n")[0]} for c in commits[:20]]
    lang_line = "Rédige le résumé en français." if args.lang.upper() == "FR" else "Write the summary in English."
    prompt = (
        f"Weekly narrative for {args.repo}. {lang_line}\n"
        f"COMMITS={json.dumps(commit_rows)}\n"
        f"ISSUES={json.dumps([{'number':i['number'],'title':i['title']} for i in closed_issues])}\n"
        f"MERGED={json.dumps([{'number':p['number'],'title':p['title']} for p in merged])}\n"
    )
    print(f"repo={args.repo} since={since} commits={len(commits)} issues={len(closed_issues)} merged={len(merged)}")
    print("--- prompt preview ---")
    print(prompt[:2000])
    out = {
        "repo": args.repo,
        "since": since,
        "counts": {"commits": len(commits), "issues": len(closed_issues), "mergedPrs": len(merged)},
        "prompt_chars": len(prompt),
    }
    Path = __import__("pathlib").Path
    (Path(__file__).resolve().parents[1] / "examples" / "dry-run-result.json").write_text(json.dumps(out, indent=2) + "\n")
    if args.call_claude and os.environ.get("ANTHROPIC_API_KEY"):
        body = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        print("--- claude ---")
        print(text[:1500])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
