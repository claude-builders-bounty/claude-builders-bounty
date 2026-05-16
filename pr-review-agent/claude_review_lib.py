"""
claude-review library — reusable functions for PR diff analysis.
Extracted from claude-review CLI for testability and import.
"""

import os
import re
import json
import tempfile
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.parse
    HAS_REQUESTS = False


def fetch_pr_diff(repo: str, pr_number: int, token: str = None) -> str:
    """Fetch the unified diff of a PR from GitHub."""
    url = f"https://github.com/{repo}/pull/{pr_number}.diff"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    if HAS_REQUESTS:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return r.text
    else:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")


def call_openrouter(prompt: str, api_key: str, model: str = "~anthropic/claude-sonnet-latest") -> str:
    """Send prompt to OpenRouter and return the response text."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior code reviewer. Analyze PR diffs and produce structured, actionable review comments."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/pokeehokee/claude-review",
        "X-Title": "Claude PR Review Agent"
    }
    
    if HAS_REQUESTS:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
    else:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    
    return data["choices"][0]["message"]["content"]


def call_ollama(prompt: str, model: str = "gemma4:latest") -> str:
    """Fallback: use local Ollama for review generation."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior code reviewer. Analyze PR diffs and produce structured, actionable review comments."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 4000}
    }
    
    if HAS_REQUESTS:
        r = requests.post(url, json=payload, timeout=300)
        r.raise_for_status()
        data = r.json()
    else:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    
    return data["message"]["content"]


def generate_review(prompt: str, api_key: str = None, model: str = None) -> str:
    """Generate review using OpenRouter (preferred) or Ollama (fallback)."""
    # Try OpenRouter first
    if api_key:
        try:
            return call_openrouter(prompt, api_key, model or "~anthropic/claude-sonnet-latest")
        except Exception as e:
            print(f"   ⚠ OpenRouter failed ({e}), falling back to Ollama...")
    
    # Fallback to Ollama
    return call_ollama(prompt, model or "gemma4:latest")


def truncate_diff(diff: str, max_chars: int = 8000) -> str:
    """Truncate diff if too large."""
    if len(diff) > max_chars:
        return diff[:max_chars] + "\n\n[... diff truncated due to length ...]"
    return diff


def build_review_prompt(diff: str, repo: str, pr_number: int) -> str:
    """Construct the review prompt for Claude."""
    diff = truncate_diff(diff, max_chars=8000)
    prompt = f"""Review the following Pull Request diff from {repo}#{pr_number}.

## Instructions
Produce a structured Markdown review with these exact sections:

### Summary of Changes
2-3 sentences describing what the PR does at a high level.

### Identified Risks
- Bullet list of potential bugs, security issues, or regressions
- Mark each with [LOW], [MEDIUM], or [HIGH] severity

### Improvement Suggestions
- Bullet list of concrete, actionable improvements
- Include specific file/line references where possible

### Confidence Score
One of: **Low** | **Medium** | **High**
Explain in 1 sentence why.

---

## PR Diff

```diff
{diff}
```
"""
    return prompt


def post_github_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post the review as a comment on the PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {"body": body}
    
    if HAS_REQUESTS:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
    else:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    
    return data["html_url"]


def parse_pr_url(url: str) -> tuple:
    """Extract (owner/repo, pr_number) from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return f"{m.group(1)}/{m.group(2)}", int(m.group(3))
