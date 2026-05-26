#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
import re

def log(msg):
    print(f"[claude-review] {msg}", file=sys.stderr)

def make_http_request(url, headers, data=None, method="GET"):
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        if isinstance(data, dict):
            req.data = json.dumps(data).encode("utf-8")
        else:
            req.data = data
    try:
        with urllib.request.urlopen(req) as res:
            return res.read().decode("utf-8"), res.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        log(f"HTTP Error {e.code}: {e.reason}\nBody: {body}")
        raise e
    except Exception as e:
        log(f"Request failed: {e}")
        raise e

def parse_pr_url(pr_url):
    # Matches formats like:
    # https://github.com/owner/repo/pull/123
    # github.com/owner/repo/pull/123
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        log(f"Invalid PR URL format: {pr_url}")
        sys.exit(1)
    return m.group(1), m.group(2), m.group(3)

def fetch_pr_details(owner, repo, pr_number, gh_token):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-pr-reviewer-action"
    }
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"
        
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    log(f"Fetching PR metadata from {api_url}...")
    metadata_json, _ = make_http_request(api_url, headers)
    metadata = json.loads(metadata_json)
    
    # Fetch Diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    log("Fetching PR diff...")
    diff, _ = make_http_request(api_url, diff_headers)
    
    return metadata, diff

def post_pr_comment(owner, repo, pr_number, gh_token, body_text):
    if not gh_token:
        log("No GITHUB_TOKEN/GH_TOKEN provided. Skipping comment posting.")
        return False
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-pr-reviewer-action",
        "Authorization": f"token {gh_token}",
        "Content-Type": "application/json"
    }
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    log(f"Posting review comment to PR #{pr_number}...")
    
    payload = {"body": body_text}
    make_http_request(api_url, headers, payload, method="POST")
    log("Successfully posted comment.")
    return True

def call_claude_api(api_key, model, pr_title, pr_body, diff):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = (
        "You are a senior software engineer performing an automated code review on a pull request.\n"
        "Your task is to analyze the PR details and git diff, and return a structured markdown review.\n"
        "Be constructive, precise, and professional. Focus on correctness, security vulnerabilities, "
        "performance bottlenecks, concurrency issues, and code readability.\n\n"
        "You must follow this exact markdown structure:\n"
        "### Summary of Changes\n"
        "[2-3 sentences summarizing the PR's purpose and key modifications]\n\n"
        "### Identified Risks\n"
        "[Bulleted list of security, performance, concurrency, or correctness risks. If none are found, write 'None detected.']\n\n"
        "### Improvement Suggestions\n"
        "[Bulleted list of actionable code modifications, architectural changes, or extra tests needed. Include specific file/line contexts if applicable. If none, write 'None.']\n\n"
        "### Confidence Score\n"
        "**Score**: [Low / Medium / High]\n"
        "**Justification**: [1-2 sentences explaining why you gave this score]"
    )
    
    user_message = (
        f"PR Title: {pr_title}\n"
        f"PR Description:\n{pr_body}\n\n"
        f"--- GIT DIFF START ---\n{diff}\n--- GIT DIFF END ---"
    )
    
    # Payload
    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    log(f"Calling Anthropic API ({model})...")
    api_url = "https://api.anthropic.com/v1/messages"
    res_json, _ = make_http_request(api_url, headers, payload, method="POST")
    res = json.loads(res_json)
    
    review_content = res["content"][0]["text"]
    return review_content

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Claude Code sub-agent for reviewing GitHub PRs.")
    parser.add_argument("--pr", help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Anthropic model to use")
    args = parser.parse_args()
    
    # 1. Resolve inputs
    pr_url = args.pr or os.environ.get("INPUT_PR_URL")
    if not pr_url:
        # Check if running inside GitHub Action event context
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if event_path and os.path.exists(event_path):
            try:
                with open(event_path, "r") as f:
                    event = json.load(f)
                pr_url = event.get("pull_request", {}).get("html_url")
            except Exception as e:
                log(f"Failed to read GitHub event file: {e}")
        
    if not pr_url:
        log("Error: No PR URL provided via --pr argument or GITHUB_EVENT_PATH.")
        sys.exit(1)
        
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        log("Error: ANTHROPIC_API_KEY environment variable is required.")
        sys.exit(1)
        
    owner, repo, pr_number = parse_pr_url(pr_url)
    log(f"Target PR: {owner}/{repo} #{pr_number}")
    
    # 2. Fetch PR details
    try:
        metadata, diff = fetch_pr_details(owner, repo, pr_number, gh_token)
    except Exception as e:
        log(f"Failed to fetch PR: {e}")
        sys.exit(1)
        
    pr_title = metadata.get("title", "")
    pr_body = metadata.get("body", "") or "No description provided."
    
    # 3. Call Claude for review
    try:
        review_md = call_claude_api(anthropic_key, args.model, pr_title, pr_body, diff)
    except Exception as e:
        log(f"Claude API request failed: {e}")
        sys.exit(1)
        
    # 4. Output review
    print("\n--- CLAUDE REVIEW OUTPUT ---")
    print(review_md)
    print("----------------------------\n")
    
    # 5. Comment on GitHub PR if running in Action
    if os.environ.get("GITHUB_ACTIONS") == "true" or gh_token:
        # Construct header/footer to make the review clean
        comment_body = (
            f"## 🤖 Claude Code PR Review\n\n"
            f"{review_md}\n\n"
            f"*Review generated by Claude using `{args.model}`.*"
        )
        post_pr_comment(owner, repo, pr_number, gh_token, comment_body)

if __name__ == "__main__":
    main()
