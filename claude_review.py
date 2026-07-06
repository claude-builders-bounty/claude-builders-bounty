#!/usr/bin/env python3
"""
Claude Code PR Review Agent
CLI tool that fetches a GitHub PR diff and produces a structured AI review via DeepSeek.
"""

import argparse
import sys
import urllib.request
import urllib.error
import json
import re
import os


# ── helpers ──────────────────────────────────────────────────────────────────

def parse_pr_url(pr_url: str):
    """Parse a GitHub PR URL -> (owner, repo, pr_number)."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url!r}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_diff(owner: str, repo: str, pr_number: int, token: str | None = None) -> str:
    """Fetch the unified diff for a GitHub PR.  Returns the raw diff text."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API returned {exc.code} for {url}: {detail}"
        ) from exc

    if not body.strip():
        raise RuntimeError("Empty diff returned from GitHub API")
    return body


def analyze_diff(diff_text: str, api_key: str) -> str:
    """Send the diff to DeepSeek and return the structured review text."""
    prompt = f"""You are a senior code reviewer. Analyze the following GitHub pull request diff and produce a structured review.

{{
  "summary": "2-3 sentences summarising the changes",
  "risks": ["risk 1", "risk 2", …],
  "suggestions": ["suggestion 1", "suggestion 2", …],
  "confidence": "Low|Medium|High"
}}

Respond with ONLY valid JSON — no markdown fences, no commentary.

DIFF:
```
{diff_text}
```
"""

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a senior software engineer reviewing a pull request. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {exc.code}: {detail}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse DeepSeek response: {exc}") from exc

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"DeepSeek returned no choices: {json.dumps(data, indent=2)[:500]}")

    return choices[0]["message"]["content"]


def parse_llm_json(raw: str) -> dict:
    """Try to extract a JSON object from the LLM response (handles markdown fences etc.)."""
    raw = raw.strip()

    # Strip markdown fences if present
    for fence in ("```json", "```JSON", "```"):
        if fence in raw:
            # Find last occurrence of the fence that starts a block
            start = raw.find(fence)
            content_start = raw.find("\n", start) + 1
            end = raw.rfind("```")
            if end > content_start:
                raw = raw[content_start:end].strip()

    return json.loads(raw)


def print_review(review: dict):
    """Pretty-print the structured review."""
    print("\n" + "=" * 60)
    print("  CLAUDE CODE PR REVIEW")
    print("=" * 60)

    print(f"\n📝 Summary of changes")
    print(f"   {review.get('summary', 'N/A')}")

    risks = review.get("risks", [])
    print(f"\n⚠️  Identified risks ({len(risks)})")
    if risks:
        for r in risks:
            print(f"   • {r}")
    else:
        print("   (none)")

    suggestions = review.get("suggestions", [])
    print(f"\n💡 Improvement suggestions ({len(suggestions)})")
    if suggestions:
        for s in suggestions:
            print(f"   • {s}")
    else:
        print("   (none)")

    confidence = review.get("confidence", "N/A")
    print(f"\n🎯 Confidence score: {confidence}")
    print("=" * 60 + "\n")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — analyse a GitHub PR with DeepSeek."
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--token", default=None, help="GitHub personal access token (optional, for private repos)")
    args = parser.parse_args()

    # API key — env var first, then hard-coded default
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        api_key = "sk-70c46d38912640c39024723a05a4af92"

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"🔍 Fetching diff for {owner}/{repo} PR #{pr_number} …")

        diff = fetch_diff(owner, repo, pr_number, token=args.token)

        print(f"📄 Diff fetched ({len(diff)} bytes)")
        print(f"🤖 Analysing with DeepSeek …")

        raw = analyze_diff(diff, api_key)
        review = parse_llm_json(raw)

        print_review(review)

    except (ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
