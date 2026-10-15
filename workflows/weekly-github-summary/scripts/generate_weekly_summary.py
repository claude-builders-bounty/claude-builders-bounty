#!/usr/bin/env python3
"""
Stand-alone / n8n Helper Script for Weekly GitHub Narrative Generation
Fetches weekly repository activity and invokes Claude API to generate a narrative dev summary.
Supports multi-language output (English and French).
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.error

def fetch_github_activity(repo: str, days: int = 7, token: str = None) -> dict:
    since_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    headers = {"User-Agent": "Weekly-Dev-Summary-Generator", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get(url):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return []

    commits = get(f"https://api.github.com/repos/{repo}/commits?since={since_date}")
    issues = get(f"https://api.github.com/repos/{repo}/issues?state=closed&since={since_date}")
    prs = get(f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=50")

    merged_prs = [p for p in prs if p.get("merged_at") and p.get("merged_at") >= since_date]
    pure_issues = [i for i in issues if not i.get("pull_request")]

    return {
        "repo": repo,
        "commits": [{"msg": c["commit"]["message"], "author": c["commit"]["author"]["name"]} for c in commits[:20]],
        "closed_issues": [{"title": i["title"], "number": i["number"]} for i in pure_issues[:20]],
        "merged_prs": [{"title": p["title"], "number": p["number"], "author": p["user"]["login"]} for p in merged_prs[:20]]
    }

def generate_summary_with_claude(activity: dict, language: str = "EN", api_key: str = None) -> str:
    lang_label = "French" if language.upper() == "FR" else "English"
    prompt = f"""You are a Principal Engineering Lead. Write a concise, narrative weekly dev summary in {lang_label} for repository {activity['repo']}.
Activity:
- Commits ({len(activity['commits'])}): {json.dumps(activity['commits'], indent=2)}
- Closed Issues ({len(activity['closed_issues'])}): {json.dumps(activity['closed_issues'], indent=2)}
- Merged PRs ({len(activity['merged_prs'])}): {json.dumps(activity['merged_prs'], indent=2)}

Format with:
1. 🚀 Executive Summary (2 sentences)
2. ✨ Key Accomplishments & Merged PRs
3. 🐛 Solved Bugs & Closed Issues
4. 📈 Velocity & Highlights"""

    if not api_key:
        return f"## 🚀 Weekly Developer Summary ({activity['repo']})\n\nDuring this week, {len(activity['merged_prs'])} PR(s) were merged and {len(activity['closed_issues'])} issue(s) resolved across {len(activity['commits'])} commit(s).\n\n*(Anthropic API Key required for real-time narrative synthesis)*"

    req_body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=req_body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode("utf-8"))
        return res["content"][0]["text"]

def main():
    parser = argparse.ArgumentParser(description="Weekly Dev Summary Generator")
    parser.add_argument("--repo", type=str, required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--lang", type=str, default="EN", choices=["EN", "FR"], help="Summary language")
    parser.add_argument("--token", type=str, default=os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT"))
    parser.add_argument("--api-key", type=str, default=os.getenv("ANTHROPIC_API_KEY"))

    args = parser.parse_args()
    data = fetch_github_activity(args.repo, token=args.token)
    summary = generate_summary_with_claude(data, language=args.lang, api_key=args.api_key)
    print(summary)

if __name__ == "__main__":
    main()
