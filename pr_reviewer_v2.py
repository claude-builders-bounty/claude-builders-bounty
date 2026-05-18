#!/usr/bin/env python3
import sys
import subprocess
import json
import os
import re

def get_pr_diff(pr_url):
    try:
        # Extract owner, repo, and number
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            return None, "Invalid PR URL"
        
        owner, repo, number = match.groups()
        repo_fullname = f"{owner}/{repo}"
        
        # Use gh CLI to get the patch
        result = subprocess.run(
            ["gh", "pr", "view", number, "--repo", repo_fullname, "--patch"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return None, f"Error fetching PR: {result.stderr}"
            
        return result.stdout, None
    except Exception as e:
        return None, str(e)

def analyze_diff(diff):
    # This part would normally call an LLM. 
    # For the purpose of this tool, we simulate the analysis logic.
    # In a real environment, this script would be used BY Claude.
    
    # We will output a prompt for Claude to perform the actual review.
    prompt = f"""
Please analyze the following PR diff and provide a review in Markdown format:

{diff}

Output MUST include:
1. Summary of changes (2–3 sentences)
2. Identified risks (list)
3. Improvement suggestions (list)
4. Confidence score: Low / Medium / High
"""
    return prompt

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "--pr":
        print("Usage: claude-review --pr https://github.com/owner/repo/pull/123")
        sys.exit(1)
        
    pr_url = sys.argv[2]
    print(f"🔍 Fetching diff for {pr_url}...")
    
    diff, error = get_pr_diff(pr_url)
    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)
        
    print("✅ Diff fetched. Analyzing (simulated context)...")
    # Output the analysis instructions. 
    # Since this is a 'Claude Code Agent', it is intended to be run inside Claude Code.
    print(analyze_diff(diff))

if __name__ == "__main__":
    main()
