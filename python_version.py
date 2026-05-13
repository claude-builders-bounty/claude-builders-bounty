#!/usr/bin/env python3
"""
Weekly Dev Summary - Python standalone version
No n8n required. Run directly: python weekly_dev_summary.py
"""
import os, json, requests, datetime, sys

def get_env(key, default=""):
    return os.environ.get(key, default)

def fetch_github_activity(repo, token, days=7):
    """Fetch commits, issues, PRs from GitHub API"""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
    base = f"https://api.github.com/repos/{repo}"

    result = {"repo": repo, "commits": [], "issues": [], "pull_requests": []}

    # Fetch commits
    r = requests.get(f"{base}/commits?per_page=20&since={since}", headers=headers, timeout=15)
    if r.status_code == 200:
        for c in r.json():
            result["commits"].append({
                "author": c.get("commit", {}).get("author", {}).get("name", c.get("author", {}).get("login", "?")),
                "message": c.get("commit", {}).get("message", "").split("\n")[0],
                "sha": c.get("sha", "")[:7],
                "url": c.get("html_url", "")
            })

    # Fetch issues
    r = requests.get(f"{base}/issues?state=closed&per_page=20&since={since}", headers=headers, timeout=15)
    if r.status_code == 200:
        for i in r.json():
            if "pull_request" not in i:  # exclude PRs from issues
                result["issues"].append({
                    "title": i.get("title", ""),
                    "number": i.get("number", ""),
                    "author": i.get("user", {}).get("login", "?"),
                    "url": i.get("html_url", "")
                })

    # Fetch PRs
    r = requests.get(f"{base}/pulls?state=closed&per_page=20&sort=updated&direction=desc", headers=headers, timeout=15)
    if r.status_code == 200:
        for pr in r.json():
            if pr.get("merged_at"):
                result["pull_requests"].append({
                    "title": pr.get("title", ""),
                    "number": pr.get("number", ""),
                    "author": pr.get("user", {}).get("login", "?"),
                    "url": pr.get("html_url", "")
                })

    return result

def generate_summary(data, api_key, language="EN"):
    """Call Claude API to generate narrative summary"""
    commits_text = "\n".join([f"- {c['author']}: {c['message']} ({c['sha']})" for c in data["commits"][:10]])
    issues_text = "\n".join([f"- #{i['number']} {i['title']}" for i in data["issues"][:10]])
    prs_text = "\n".join([f"- #{p['number']} {p['title']}" for p in data["pull_requests"][:10]])

    lang_instruction = "Write a narrative summary in English (5-8 paragraphs)." if language == "EN" \
        else "Rédigez un résumé narratif en français (5-8 paragraphes)."

    prompt = f"""Create a weekly development summary for repository {data['repo']}.

Commits: {len(data['commits'])}
Closed Issues: {len(data['issues'])}
Merged PRs: {len(data['pull_requests'])}

Commit Details:
{commits_text}

Issues:
{issues_text}

PRs:
{prs_text}

{lang_instruction} Highlight trends, major changes, and areas of focus."""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": "You are a technical writer creating a weekly development summary.",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )

    if r.status_code == 200:
        return r.json()["content"][0]["text"]
    else:
        return f"Error calling Claude API: {r.status_code} - {r.text[:200]}"

def save_report(summary_text, filename="weekly_summary.md"):
    """Save the summary to a file"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"Summary saved to {filename}")

def send_webhook(summary_text, webhook_url):
    """Send to Slack/Discord webhook"""
    if not webhook_url:
        return
    r = requests.post(webhook_url, json={"text": summary_text}, timeout=15)
    print(f"Webhook sent: HTTP {r.status_code}")

if __name__ == "__main__":
    repo = get_env("GITHUB_REPO", "anthropics/claude-code")
    token = get_env("GITHUB_TOKEN", "")
    api_key = get_env("CLAUDE_API_KEY", "")
    lang = get_env("SUMMARY_LANGUAGE", "EN")
    webhook = get_env("WEBHOOK_URL", "")

    if not token:
        print("ERROR: GITHUB_TOKEN environment variable required")
        sys.exit(1)

    print(f"Fetching activity for: {repo}")
    data = fetch_github_activity(repo, token)
    print(f"Found: {len(data['commits'])} commits, {len(data['issues'])} issues, {len(data['pull_requests'])} PRs")

    if api_key and (data['commits'] or data['issues'] or data['pull_requests']):
        print("Generating summary with Claude...")
        summary = generate_summary(data, api_key, lang)
    else:
        # Fallback: simple text summary without Claude
        summary = f"# Weekly Development Summary\n\n**Repo**: {repo}\n**Date**: {datetime.date.today()}\n\n"
        summary += f"**Commits**: {len(data['commits'])}\n"
        for c in data['commits'][:5]:
            summary += f"- {c['author']}: {c['message']}\n"
        summary += f"\n**Issues Closed**: {len(data['issues'])}\n"
        for i in data['issues'][:5]:
            summary += f"- #{i['number']}: {i['title']}\n"
        summary += f"\n**Merged PRs**: {len(data['pull_requests'])}\n"
        for p in data['pull_requests'][:5]:
            summary += f"- #{p['number']}: {p['title']}\n"

    save_report(summary)
    send_webhook(summary, webhook)
    print("Done!")
