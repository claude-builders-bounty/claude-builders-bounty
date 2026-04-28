#!/usr/bin/env python3
import argparse
import subprocess
import sys
import json
import os

def get_pr_diff(pr_url):
    try:
        # Use gh CLI to get the diff
        result = subprocess.run(["gh", "pr", "diff", pr_url], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}")
        sys.exit(1)

def get_pr_metadata(pr_url):
    try:
        # Use gh CLI to get title and body
        result = subprocess.run(["gh", "pr", "view", pr_url, "--json", "title,body"], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR metadata: {e.stderr}")
        sys.exit(1)

def review_pr(diff, metadata):
    # This is where we would call Claude. 
    # For the sake of this CLI tool, we assume the user has 'claude' CLI installed or we use an API key.
    # To make it a true "Claude Code Agent", we can provide a prompt that the user can pipe to 'claude'.
    
    prompt = f"""
Review the following GitHub Pull Request.

Title: {metadata['title']}
Body: {metadata['body']}

Diff:
{diff}

Provide a structured Markdown review with the following sections:
1. **Summary of Changes**: 2-3 sentences explaining what this PR does.
2. **Identified Risks**: A list of potential bugs, security issues, or regressions.
3. **Improvement Suggestions**: A list of ways to improve the code (performance, readability, best practices).
4. **Confidence Score**: Low / Medium / High based on how certain you are about the review.

Output ONLY the Markdown.
"""
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL or number")
    
    args = parser.parse_args()
    
    diff = get_pr_diff(args.pr)
    metadata = get_pr_metadata(args.pr)
    prompt = review_pr(diff, metadata)
    
    # In a real scenario, we might call the Anthropic API here.
    # For a Claude Code "agent", we can pipe this prompt to the 'claude' command if available,
    # or just output it for the user to use.
    
    # Check if 'claude' CLI is available
    claude_path = subprocess.run(["which", "claude"], capture_output=True, text=True).stdout.strip()
    
    if claude_path:
        print("Sending PR to Claude for review...")
        process = subprocess.Popen([claude_path], stdin=subprocess.PIPE, text=True)
        process.communicate(input=prompt)
    else:
        print("Claude CLI not found. Here is the review prompt you can use:")
        print("-" * 40)
        print(prompt)

if __name__ == "__main__":
    main()
