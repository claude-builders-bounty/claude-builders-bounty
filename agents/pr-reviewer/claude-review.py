#!/usr/bin/env python3
"""PR Review Agent — analyzes PR diffs and outputs structured Markdown review."""

import os
import re
import sys
import json
import urllib.request
import urllib.error

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def parse_pr_url(url):
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        print("Usage: claude-review --pr https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2), m.group(3)


def fetch_pr_info(owner, repo, pr_num):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            diff = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)

    headers_json = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers_json["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req_json = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}",
        headers=headers_json
    )
    with urllib.request.urlopen(req_json) as r:
        info = json.loads(r.read().decode("utf-8"))

    return diff, info


def analyze_with_claude(diff, info):
    prompt = f"""Review this PR diff and return a structured analysis.

PR: {info.get('title', 'N/A')}
Author: {info.get('user', {}).get('login', 'N/A')}
Files changed: {info.get('changed_files', '?')}
Additions: {info.get('additions', '?')}
Deletions: {info.get('deletions', '?')}

DIFF:
{diff[:8000]}

Return analysis as JSON with: summary, risks (list), suggestions (list), confidence (Low/Medium/High)."""

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read().decode("utf-8"))
        content = resp.get("content", [{}])[0].get("text", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"summary": content[:200], "risks": ["Unable to parse structured output"], "suggestions": [], "confidence": "Low"}
    except Exception as e:
        return None


def template_review(diff, info):
    added = info.get('additions', 0)
    deleted = info.get('deletions', 0)
    files = info.get('changed_files', 0)
    title = info.get('title', 'N/A')
    author = info.get('user', {}).get('login', 'N/A')

    summary = f"PR '{title}' by {author} changes {files} files ({added} additions, {deleted} deletions)."

    risks = []
    if deleted > added * 3:
        risks.append("Large deletion volume — verify no logic is being removed without replacement")
    if "TODO" in diff or "FIXME" in diff:
        risks.append("Unresolved TODOs/FIXMEs in diff")
    if "api_key" in diff.lower() or "password" in diff.lower() or "secret" in diff.lower():
        risks.append("Possible credential exposure — check for secrets in diff")
    if "console.log" in diff or "print(" in diff:
        risks.append("Debug logging left in code")
    if "any" in diff and "as any" in diff:
        risks.append("Use of `any` type may bypass type checking")
    if not risks:
        risks.append("No significant risks detected in automated analysis")

    suggestions = []
    if added > 500:
        suggestions.append("Large PR — consider splitting into smaller, focused changes")
    if files > 10:
        suggestions.append(f"{files} files changed — verify all changes relate to a single concern")
    suggestions.append("Ensure test coverage for new/modified functionality")
    suggestions.append("Verify the diff handles edge cases (empty state, errors, loading)")

    confidence = "High" if added < 100 else "Medium" if added < 500 else "Low"

    return {"summary": summary, "risks": risks, "suggestions": suggestions, "confidence": confidence}


def format_markdown(result):
    parts = ["## PR Review", "", f"### Summary", "", result.get("summary", "N/A"), "",
             "### Identified Risks", ""]
    for r in result.get("risks", []):
        parts.append(f"- ⚠️ {r}")
    parts.extend(["", "### Improvement Suggestions", ""])
    for s in result.get("suggestions", []):
        parts.append(f"- 💡 {s}")
    parts.extend(["", f"### Confidence Score: **{result.get('confidence', 'Low')}**", ""])
    return "\n".join(parts)


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--pr":
        print("Usage: claude-review --pr https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[2]
    owner, repo, pr_num = parse_pr_url(url)
    diff, info = fetch_pr_info(owner, repo, pr_num)

    result = None
    if ANTHROPIC_API_KEY:
        result = analyze_with_claude(diff, info)
    if not result:
        result = template_review(diff, info)

    print(format_markdown(result))

    if "--json" in sys.argv:
        print("\n---\n```json")
        print(json.dumps(result, indent=2))
        print("```")


if __name__ == "__main__":
    main()
