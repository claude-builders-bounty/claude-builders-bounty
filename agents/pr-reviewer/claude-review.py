#!/usr/bin/env python3
import argparse
import urllib.request
import json
import os
import sys

def get_pr_diff(pr_url):
    diff_url = pr_url.rstrip('/') + '.diff'
    req = urllib.request.Request(diff_url)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        sys.exit(1)

def call_claude(diff):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.")
        sys.exit(1)
        
    prompt = f"""You are an expert code reviewer. Analyze the following GitHub Pull Request diff and provide a structured Markdown review.

Required format exactly as follows:
### 📝 Summary of Changes
(2-3 sentences summarizing the diff)

### ⚠️ Identified Risks
- (List any security, performance, or logic risks. If none, state "None identified".)

### 💡 Improvement Suggestions
- (List suggestions for better code quality, readability, or best practices.)

### 📊 Confidence Score
(Low / Medium / High)

Here is the PR diff:
```diff
{diff}
