#!/usr/bin/env python3
"""dry-run.py — standalone harness for the n8n Weekly Dev Summary pipeline (stdlib only).

Steps (mirrors workflow.json):
  1. GitHub commits since `since` (no key needed; optional GH_TOKEN raises limit)
  2. GitHub closed issues + PRs since `since`
  3. (optional) Claude API narrative summary if ANTHROPIC_API_KEY is set
  4. (optional) Slack/Discord webhook deliver if webhook URL is set

Usage:
  python3 dry-run.py --repo vercel/next.js --since 2026-09-01          # fetch only
  python3 dry-run.py --repo vercel/next.js --since 2026-09-01 --claude # + Claude summary
  python3 dry-run.py --repo vercel/next.js --since 2026-09-01 --claude --slack # + deliver
"""
import argparse, json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

GITHUB_API = "https://api.github.com"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

def http_get(url, token=None):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'weekly-dev-summary/1.0',
        'Accept': 'application/vnd.github+json'
    })
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def http_post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def fetch_github(repo, since, token, per_page=100):
    commits = http_get(f"{GITHUB_API}/repos/{repo}/commits?since={since}&per_page={per_page}", token)
    issues = http_get(f"{GITHUB_API}/repos/{repo}/issues?state=closed&since={since}&per_page={per_page}&sort=updated", token)
    return commits or [], issues or []

def aggregate(commits, issues, repo, since, until, language):
    prs = [i for i in issues if i.get('pull_request') and i['pull_request'].get('merged_at')]
    issues_only = [i for i in issues if not i.get('pull_request')]
    return {
        "repo": repo,
        "period": {"since": since, "until": until},
        "language": language,
        "stats": {"commits": len(commits), "closed_issues": len(issues_only), "merged_prs": len(prs)},
        "commits": [{"sha": c['sha'][:7], "message": c['commit']['message'].split('\n')[0],
                     "author": c['commit']['author']['name'] if c['commit']['author'] else 'unknown',
                     "date": c['commit']['author']['date']} for c in commits[:30]],
        "issues": [{"number": i['number'], "title": i['title'],
                    "labels": [l['name'] for l in i.get('labels', [])],
                    "closed_at": i['closed_at']} for i in issues_only[:20]],
        "prs": [{"number": p['number'], "title": p['title'],
                 "author": p['user']['login'], "merged_at": p['pull_request']['merged_at']} for p in prs[:20]]
    }

def call_claude(summary, api_key, language):
    lang = 'French' if language == 'FR' else 'English'
    data = json.dumps(summary, indent=2)
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": f"You are a release narrator for GitHub repo {summary['repo']}.\n"
                       f"Window: {summary['period']['since']} to {summary['period']['until']}\n"
                       f"Write the summary in clear professional {lang}.\n\n"
                       f"Produce a weekly narrative summary with sections:\n"
                       f"1) Highlights\n2) Shipping (merged PRs)\n3) Fixes & closed issues\n"
                       f"4) Commit themes\n5) Risks / follow-ups\n\n"
                       f"DATA (JSON):\n{data}"
        }]
    }
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    return http_post(ANTHROPIC_API, payload, headers)

def deliver_slack(summary, webhook_url):
    repo = summary['repo']
    period = summary['period']
    payload = {
        "text": f"*Weekly Dev Summary: {repo}* ({period['since']} to {period['until']})\n{summary.get('summary', '')}",
        "blocks": [{"type": "section", "text": {"type": "mrkdwn",
            "text": f"*Weekly Dev Summary: {repo}* ({period['since']} to {period['until']})\n{summary.get('summary', '')}"}}]
    }
    return http_post(webhook_url, payload, {'Content-Type': 'application/json'})

def deliver_discord(summary, webhook_url):
    repo = summary['repo']
    period = summary['period']
    payload = {"content": f"**Weekly Dev Summary: {repo}** ({period['since']} to {period['until']})\n{summary.get('summary', '')}"}
    return http_post(webhook_url, payload, {'Content-Type': 'application/json'})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, help='owner/repo')
    ap.add_argument('--since', required=True, help='YYYY-MM-DD')
    ap.add_argument('--until', default=datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    ap.add_argument('--lang', default='EN', choices=['EN', 'FR'])
    ap.add_argument('--claude', action='store_true')
    ap.add_argument('--slack', action='store_true')
    ap.add_argument('--discord', action='store_true')
    args = ap.parse_args()

    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    commits, issues = fetch_github(args.repo, args.since, token)
    if commits is None or issues is None:
        sys.exit(1)

    summary = aggregate(commits, issues, args.repo, args.since, args.until, args.lang)
    print(json.dumps({"repo": args.repo, "stats": summary['stats']}, indent=2))

    if args.claude:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("ANTHROPIC_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        resp = call_claude(summary, api_key, args.lang)
        if resp:
            summary['summary'] = resp['content'][0]['text']
            print("\n--- CLAUDE SUMMARY ---\n")
            print(summary['summary'])

    if args.slack:
        url = os.environ.get('SLACK_WEBHOOK_URL')
        if url:
            deliver_slack(summary, url)
            print("Delivered to Slack")
        else:
            print("SLACK_WEBHOOK_URL not set", file=sys.stderr)

    if args.discord:
        url = os.environ.get('DISCORD_WEBHOOK_URL')
        if url:
            deliver_discord(summary, url)
            print("Delivered to Discord")
        else:
            print("DISCORD_WEBHOOK_URL not set", file=sys.stderr)

if __name__ == '__main__':
    main()
