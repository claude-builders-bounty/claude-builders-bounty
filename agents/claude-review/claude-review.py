#!/usr/bin/env python3
import sys
import re
import os
import argparse
import subprocess
import requests

# Set exactly how the markdown should be formatted
REVIEW_PROMPT = """
You are an expert Principal Software Engineer. Analyze the provided git diff and return a structured Markdown review comment.
Your response MUST strictly adhere to the following structure:

### Summary
[Summary of changes (2-3 sentences)]

### Identified Risks
- [Risk 1]
- [Risk 2]
(List none if none found)

### Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
(List none if none found)

### Confidence Score
[Low / Medium / High]

Here is the diff to review:
```diff
{diff}
```
"""

def get_pr_diff(pr_url, token=None):
    """Fetches the diff for a given PR URL via GitHub API."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        print("Error: Invalid PR URL. Use format: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
        
    owner, repo, pr_num = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    headers = {"Accept": "application/vnd.github.v3.diff"}
    # Use GITHUB_TOKEN if available to avoid rate limits
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching PR diff (Status {response.status_code}): {response.text}", file=sys.stderr)
        sys.exit(1)
        
    return response.text

def run_claude_cli_eval(diff_content):
    """
    Evaluates the prompt using the `claude` CLI if installed.
    As a Claude Code sub-agent, we pipe the evaluation directly.
    """
    prompt = REVIEW_PROMPT.format(diff=diff_content)
    
    # Check if 'claude' CLI is available
    import shutil
    if not shutil.which("claude"):
        print("Error: 'claude' CLI is not installed or not in PATH.", file=sys.stderr)
        print("Please install Claude Code: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
        sys.exit(1)
        
    print(f"Evaluating PR with Claude Code...", file=sys.stderr)
    
    try:
        # Run claude --print "prompt" to get output directly to stdout
        # Note: Depending on Claude Code version, syntax is `claude -p "prompt"`
        # However, passing a huge diff via argument can exceed MAX_ARG_STRLEN.
        # Instead, we will pipe the prompt to claude using stdin: `echo "<prompt>" | claude -p`
        # But `claude -p` might start an interactive session if stdin is redirected.
        # We write prompt to a temp file and ask Claude to read it.
        
        prompt_file = ".claude_pr_review_prompt.txt"
        with open(prompt_file, "w") as f:
            f.write(prompt)
            
        result = subprocess.run(
            ["claude", "-p", f"Read the file {prompt_file} and output EXACTLY the structured review response for the diff inside it without any dialog or conversational wrapper."],
            capture_output=True,
            text=True
        )
        
        if os.path.exists(prompt_file):
            os.remove(prompt_file)
            
        if result.returncode != 0:
            print("Error executing Claude Code:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
            
        return result.stdout.strip()
        
    except Exception as e:
        print(f"Execution error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude Code sub-agent that reviews a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    
    gh_token = os.environ.get("GITHUB_TOKEN")
    
    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff = get_pr_diff(args.pr, gh_token)
    
    if not diff.strip():
        print("Diff is empty. Nothing to review.", file=sys.stderr)
        sys.exit(0)
        
    review_markdown = run_claude_cli_eval(diff)
    print("\n" + review_markdown)

if __name__ == "__main__":
    main()
