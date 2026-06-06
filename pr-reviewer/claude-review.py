#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import json
import urllib.request
import re

# Ensure UTF-8 output on all platforms
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_pr_info(pr_url):
    """Fetch PR metadata and diff using GitHub CLI or web requests."""
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, pr_url)
    if not match:
        print(f"Error: Invalid GitHub PR URL: {pr_url}", file=sys.stderr)
        sys.exit(1)
    
    owner, repo, pr_num = match.groups()
    diff_text = None
    pr_title = f"PR #{pr_num}"
    pr_body = ""
    
    # Try using gh CLI first (handles private repos and auth natively)
    try:
        cmd = ["gh", "pr", "view", pr_url, "--json", "title,body"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            pr_data = json.loads(res.stdout)
            pr_title = pr_data.get("title", pr_title)
            pr_body = pr_data.get("body", "")
            
            diff_cmd = ["gh", "pr", "diff", pr_url]
            diff_res = subprocess.run(diff_cmd, capture_output=True, text=True, encoding="utf-8")
            if diff_res.returncode == 0:
                diff_text = diff_res.stdout
    except Exception:
        pass
        
    # Fallback to fetching diff directly from GitHub web (public repos only)
    if not diff_text:
        diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_num}.diff"
        print(f"gh CLI not available or failed. Fetching diff from public web: {diff_url}", file=sys.stderr)
        try:
            req = urllib.request.Request(diff_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                diff_text = r.read().decode('utf-8', 'ignore')
        except Exception as e:
            print(f"Error: Failed to fetch PR diff: {e}", file=sys.stderr)
            sys.exit(1)

    if not diff_text or not diff_text.strip():
        print("Error: Fetched PR diff is empty. Cannot perform review.", file=sys.stderr)
        sys.exit(1)

    return {
        "owner": owner,
        "repo": repo,
        "number": pr_num,
        "title": pr_title,
        "body": pr_body,
        "diff": diff_text
    }

def analyze_diff_heuristically(pr_data):
    """Fallback static analysis of diff when no LLM key is configured."""
    diff = pr_data["diff"]
    title = pr_data["title"]
    body = pr_data["body"]
    
    risks = []
    suggestions = []
    
    lines_added = []
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            lines_added.append(line[1:])
            
    for line in lines_added:
        if re.search(r'\b(api_key|token|password|secret|passwd|private_key|privatekey)\b\s*=\s*[\'"][^\'"]+[\'"]', line, re.IGNORECASE):
            risks.append("Possible hardcoded secret or credential detected in source code.")
            suggestions.append("Move secrets to environment variables or use a secret manager.")
        
        if "console.log" in line and not "test" in pr_data["repo"].lower():
            risks.append("Debug output `console.log` left in production code.")
            suggestions.append("Remove debugging statements or use a dedicated logging framework.")
            
        if re.search(r'execute\(\s*[\'"].*?%s.*?[\'"]\s*%', line) or re.search(r'execute\(\s*f[\'"].*?\{.*?\}', line):
            risks.append("Potential SQL Injection: dynamic SQL formatting detected.")
            suggestions.append("Use parameterized queries instead of string formatting.")
            
        if re.search(r'except\s+Exception:\s*pass', line) or re.search(r'catch\s*\(e\)\s*\{\s*\}', line):
            risks.append("Empty catch/except block: errors are silently swallowed.")
            suggestions.append("Log the caught exception or rethrow it.")

    if len(lines_added) > 500:
        risks.append("Large PR size: review is complex and edge cases may be missed.")
        suggestions.append("Consider breaking the PR into smaller, modular pull requests.")

    if not risks:
        risks.append("No critical static code risks detected in the changes.")
    if not suggestions:
        suggestions.append("No immediate structural improvements required.")
        
    summary = f"Reviewing PR #{pr_data['number']} - '{title}'. This PR contains {len(lines_added)} additions across files. "
    if body:
        summary += f"The description indicates: {body[:100]}..."
    else:
        summary += "No PR description was provided."

    return {
        "summary": summary,
        "risks": list(set(risks)),
        "suggestions": list(set(suggestions)),
        "confidence": "Medium (Static Analysis)"
    }

def analyze_diff_with_claude(pr_data, api_key):
    """Call Anthropic API to get review."""
    diff = pr_data["diff"]
    title = pr_data["title"]
    body = pr_data["body"]
    
    max_diff_len = 100000
    if len(diff) > max_diff_len:
        diff = diff[:max_diff_len] + "\n\n[Diff truncated due to size limit]"

    prompt = f"""You are an elite software engineer reviewing a pull request.
Review the following PR information and git diff:

PR Title: {title}
PR Description: {body}

PR Diff:
```diff
{diff}
```

Format your response exactly as a JSON object with these keys:
- "summary": A 2-3 sentence overview of what this PR changes.
- "risks": A list of potential technical risks, performance issues, security vulnerabilities, or bugs.
- "suggestions": A list of actionable improvements to code quality, logic, or testing.
- "confidence": A string indicating confidence level: "High", "Medium", or "Low" (explain why).

Output only the raw JSON. Do not wrap in markdown code blocks.
"""

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1500,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            res_data = json.loads(r.read().decode('utf-8'))
            text_resp = res_data["content"][0]["text"].strip()
            if text_resp.startswith("```"):
                text_resp = re.sub(r'^```(?:json)?\n', '', text_resp)
                text_resp = re.sub(r'\n```$', '', text_resp)
            return json.loads(text_resp.strip())
    except Exception as e:
        print(f"[Warning] Anthropic API request failed: {e}. Falling back to static analysis.", file=sys.stderr)
        return None

def format_markdown(review_data):
    md = []
    md.append("## 🔍 Claude Code PR Reviewer Report\n")
    
    md.append("### 📝 Summary of Changes")
    md.append(review_data["summary"] + "\n")
    
    md.append("### ⚠️ Identified Risks")
    for risk in review_data["risks"]:
        md.append(f"- {risk}")
    md.append("")
    
    md.append("### 💡 Improvement Suggestions")
    for sug in review_data["suggestions"]:
        md.append(f"- {sug}")
    md.append("")
    
    md.append(f"**Confidence Score:** `{review_data['confidence']}`")
    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="PR reviewer agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL")
    args = parser.parse_args()
    
    pr_data = get_pr_info(args.pr)
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    review_data = None
    if api_key:
        review_data = analyze_diff_with_claude(pr_data, api_key)
        
    if not review_data:
        review_data = analyze_diff_heuristically(pr_data)
        
    markdown_output = format_markdown(review_data)
    print(markdown_output)

if __name__ == "__main__":
    main()
