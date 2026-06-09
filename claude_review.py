#!/usr/bin/env python3
"""
claude-review: Analyze a GitHub PR diff and produce a structured Markdown review.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123

Requires:
    - GITHUB_TOKEN env var (or `gh` CLI authenticated)
    - OPENAI_API_KEY env var (or any OpenAI-compatible provider)
    - OPENAI_BASE_URL env var (optional, defaults to https://api.openai.com/v1)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def get_gh_token() -> str:
    """Get GitHub token from env or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        import subprocess
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True, text=True, check=True
            )
            token = result.stdout.strip()
        except Exception:
            pass
    if not token:
        print("Error: No GitHub token found. Set GITHUB_TOKEN or run `gh auth login`.", file=sys.stderr)
        sys.exit(1)
    return token


def parse_pr_url(url: str) -> tuple:
    """Extract owner, repo, pr_number from a GitHub PR URL."""
    # Handle formats: https://github.com/owner/repo/pull/123
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print(f"Error: Invalid PR URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_info(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata and diff from GitHub API."""
    base = "https://api.github.com"

    # Get PR metadata
    req = urllib.request.Request(
        f"{base}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-review-agent",
        }
    )
    with urllib.request.urlopen(req) as resp:
        pr_data = json.loads(resp.read())

    # Get PR diff
    req = urllib.request.Request(
        f"{base}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review-agent",
        }
    )
    with urllib.request.urlopen(req) as resp:
        diff = resp.read().decode("utf-8", errors="replace")

    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", "") or "",
        "user": pr_data.get("user", {}).get("login", ""),
        "base": pr_data.get("base", {}).get("ref", ""),
        "head": pr_data.get("head", {}).get("ref", ""),
        "changed_files": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "diff": diff[:80000],  # Truncate very large diffs
    }


def analyze_with_llm(pr_info: dict) -> dict:
    """Send PR diff to LLM and get structured review."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        print("Warning: No OPENAI_API_KEY set. Using local heuristic analysis.", file=sys.stderr)
        return local_analysis(pr_info)

    prompt = f"""You are a senior code reviewer. Analyze this GitHub PR and provide a structured review.

## PR Info
- Title: {pr_info['title']}
- Author: {pr_info['user']}
- Branch: {pr_info['head']} -> {pr_info['base']}
- Changed files: {pr_info['changed_files']}
- Additions: {pr_info['additions']} | Deletions: {pr_info['deletions']}

## PR Description
{pr_info['body'][:2000]}

## Diff
```diff
{pr_info['diff'][:60000]}
```

Respond in EXACTLY this JSON format (no markdown fences):
{{
  "summary": "2-3 sentence summary of what this PR does and why",
  "risks": ["risk 1", "risk 2"],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "confidence": "Low|Medium|High"
}}"""

    data = json.dumps({
        "model": os.environ.get("REVIEW_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1500,
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"].strip()
        # Try to parse JSON from response
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"Warning: LLM call failed ({e}), falling back to local analysis.", file=sys.stderr)
        return local_analysis(pr_info)


def local_analysis(pr_info: dict) -> dict:
    """Fallback: heuristic analysis without LLM."""
    diff = pr_info["diff"]
    risks = []
    suggestions = []

    # Simple heuristics
    if "rm -rf" in diff or "rm -fr" in diff:
        risks.append("Contains `rm -rf` command — potential data loss risk")
    if "password" in diff.lower() or "secret" in diff.lower() or "api_key" in diff.lower():
        risks.append("Possible hardcoded credentials or secrets in code")
    if "TODO" in diff or "FIXME" in diff or "HACK" in diff:
        suggestions.append("Contains TODO/FIXME/HACK markers — consider resolving before merge")
    if "+import" in diff and "test" not in diff.lower():
        suggestions.append("New imports added — ensure no unused dependencies")
    if pr_info["changed_files"] > 10:
        risks.append(f"Large PR ({pr_info['changed_files']} files changed) — consider splitting")
    if pr_info["additions"] > 500:
        risks.append(f"High addition count ({pr_info['additions']} lines) — review complexity")
    if not risks:
        risks.append("No obvious risks detected from diff analysis")
    if not suggestions:
        suggestions.append("Code appears clean — verify test coverage for new functionality")

    # Confidence based on size
    if pr_info["changed_files"] <= 3 and pr_info["additions"] < 100:
        confidence = "High"
    elif pr_info["changed_files"] <= 10:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "summary": f"PR by @{pr_info['user']} modifies {pr_info['changed_files']} file(s) "
                   f"(+{pr_info['additions']}/-{pr_info['deletions']}). "
                   f"Branch `{pr_info['head']}` -> `{pr_info['base']}`.",
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def format_markdown(review: dict, pr_info: dict, pr_url: str) -> str:
    """Format review as structured Markdown."""
    lines = []
    lines.append("## 🔍 PR Review")
    lines.append("")
    lines.append(f"**PR:** {pr_url}")
    lines.append(f"**Author:** @{pr_info['user']}")
    lines.append(f"**Changes:** {pr_info['changed_files']} files, +{pr_info['additions']}/-{pr_info['deletions']}")
    lines.append("")

    # Summary
    lines.append("### 📝 Summary")
    lines.append(review.get("summary", "No summary available."))
    lines.append("")

    # Risks
    lines.append("### ⚠️ Risks")
    for r in review.get("risks", []):
        lines.append(f"- {r}")
    lines.append("")

    # Suggestions
    lines.append("### 💡 Suggestions")
    for s in review.get("suggestions", []):
        lines.append(f"- {s}")
    lines.append("")

    # Confidence
    conf = review.get("confidence", "Medium")
    emoji = {"Low": "🔴", "Medium": "🟡", "High": "🟢"}.get(conf, "⚪")
    lines.append(f"### 🎯 Confidence: {emoji} {conf}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a GitHub PR and produce a structured Markdown review."
    )
    parser.add_argument(
        "--pr", required=True,
        help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write output to file instead of stdout"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw JSON instead of Markdown"
    )
    args = parser.parse_args()

    # Parse URL
    owner, repo, pr_number = parse_pr_url(args.pr)
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    # Fetch PR
    token = get_gh_token()
    pr_info = fetch_pr_info(owner, repo, pr_number, token)
    print(f"Analyzing diff ({len(pr_info['diff'])} chars)...", file=sys.stderr)

    # Analyze
    review = analyze_with_llm(pr_info)

    # Format
    if args.json:
        output = json.dumps(review, indent=2)
    else:
        output = format_markdown(review, pr_info, args.pr)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
