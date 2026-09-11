#!/usr/bin/env python3
"""dry-run.py — standalone harness for the n8n Weekly Dev Summary pipeline (stdlib only).

Steps (mirrors workflow.json):
  1. GitHub commits since `since` (no key needed; optional GH_TOKEN raises limit)
  2. GitHub closed issues + PRs since `since`
  3. (optional) Claude API narrative summary if ANTHROPIC_API_KEY is set
  4. (optional) Slack webhook deliver if SLACK_WEBHOOK_URL is set

Usage:
  python dry-run.py --repo expressjs/express --since 2026-09-01          # fetch only
  python dry-run.py --repo expressjs/express --since 2026-09-01 --claude # + Claude summary
"""
import argparse, json, os, sys, urllib.request

def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'weekly-dev-summary/1.0', 'Accept': 'application/vnd.github+json'})
    token = os.environ.get('GH_TOKEN')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='expressjs/express')
    ap.add_argument('--since', default='2026-09-01')
    ap.add_argument('--claude', action='store_true')
    args = ap.parse_args()

    # 1. commits
    commits_url = f'https://api.github.com/repos/{args.repo}/commits?since={args.since}T00:00:00Z&per_page=100'
    data = http_get(commits_url)
    commits = [{'msg': c['commit']['message'].split('\n')[0], 'author': (c['author'] or {}).get('login'), 'date': c['commit']['author']['date']} for c in data if isinstance(c, dict) and 'commit' in c]
    print(f'commits since {args.since}: {len(commits)}')

    # 2. issues + prs
    issues_url = f'https://api.github.com/repos/{args.repo}/issues?state=closed&since={args.since}T00:00:00Z&per_page=100'
    issues_raw = http_get(issues_url)
    issues, prs = [], []
    for i in issues_raw:
        if 'pull_request' in i:
            prs.append({'n': i['number'], 'title': i['title'], 'merged': bool(i['pull_request'].get('merged_at'))})
        else:
            issues.append({'n': i['number'], 'title': i['title']})
    print(f'issues closed: {len(issues)} | PRs: {len(prs)}')

    # 3. (optional) Claude summary
    key = os.environ.get('ANTHROPIC_API_KEY')
    if args.claude and key:
        model = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        user = (f'Weekly activity for *{args.repo}* since {args.since}:\n\n'
                f'Commits ({len(commits)}):\n' + '\n'.join(f'- {c["msg"]} ({c["author"]})' for c in commits) + '\n\n'
                f'Issues closed ({len(issues)}):\n' + '\n'.join(f'- #{i["n"]} {i["title"]}' for i in issues) + '\n\n'
                f'Pull requests ({len(prs)}):\n' + '\n'.join(f'- #{p["n"]} {p["title"]} [merged={p["merged"]}]' for p in prs) + '\n\n'
                'Give a structured weekly dev summary (max 2000 chars).')
        body = {'model': model, 'max_tokens': 1000, 'system': 'You are a senior engineering manager producing a weekly summary. Write in English, professional, concise. Use bullet points.', 'messages': [{'role': 'user', 'content': user}]}
        req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=json.dumps(body).encode(),
                                     headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
        with urllib.request.urlopen(req, timeout=90) as resp:
            out = json.loads(resp.read())
        text = '\n'.join(b.get('text', '') for b in out.get('content', []) if b.get('type') == 'text')
        print('\n=== SLACK PAYLOAD (summary) ===\n')
        print(text[:3000])

    # 4. (optional) deliver
    webhook = os.environ.get('SLACK_WEBHOOK_URL')
    if args.claude and webhook:
        urllib.request.urlopen(urllib.request.Request(webhook, data=json.dumps({'text': text}).encode(), headers={'content-type': 'application/json'}), timeout=15)

if __name__ == '__main__':
    main()