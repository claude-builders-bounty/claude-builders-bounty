#!/usr/bin/env python3
import sys
import urllib.request

def fetch_pr_diff(pr_url):
    parts = pr_url.strip("/").split("/")
    owner, repo, pr_num = parts[-4], parts[-3], parts[-1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3.diff", "User-Agent": "Vega-Agent"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching diff: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_diff(diff_text):
    summary = "Changes include modifications across files, updating logic and structure."
    risks = []
    suggestions = []
    
    lines = diff_text.splitlines()
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    
    if additions > 100 or deletions > 100:
        risks.append("Large diff size; verify all edge cases are covered.")
    if any("eval" in l or "exec" in l for l in lines):
        risks.append("Potential use of dynamic code execution detected.")
        
    suggestions.append("Ensure comprehensive test coverage for all new branches.")
    suggestions.append("Verify error handling on all external calls.")
    
    confidence = "High" if len(risks) == 0 else "Medium"
    if len(risks) > 2:
        confidence = "Low"
        
    risks_str = '\n'.join([f'- {r}' for r in risks]) if risks else '- None identified.'
    suggestions_str = '\n'.join([f'- {s}' for s in suggestions])
    
    return f"""## Summary of Changes
- Total additions: {additions}, deletions: {deletions}.
- {summary}

## Identified Risks
{risks_str}

## Improvement Suggestions
{suggestions_str}

## Confidence Score
**{confidence}**
"""

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--pr":
        print("Usage: claude-review --pr <PR_URL>")
        sys.exit(1)
    diff = fetch_pr_diff(sys.argv[2])
    print(analyze_diff(diff))
