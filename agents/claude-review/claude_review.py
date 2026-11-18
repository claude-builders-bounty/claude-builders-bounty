#!/usr/bin/env python3
"""Claude Code PR Reviewer Agent & CLI (`claude-review --pr <github-pr-url>`)."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

PR_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = PR_RE.search(url.strip())
    if not m:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def gh_fetch(url: str, accept: str = "application/vnd.github+json") -> str:
    headers = {"Accept": accept, "User-Agent": "claude-review-agent"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def analyze_diff_static(meta: dict, diff_text: str) -> str:
    added_lines = [l[1:] for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
    files = re.findall(r"^diff --git a/(.+?) b/(.+?)$", diff_text, flags=re.MULTILINE)
    changed_files = [b for _, b in files]

    risks = []
    suggestions = []

    joined = "\n".join(added_lines)
    if re.search(r"eval\(|exec\(|shell=True|dangerouslySetInnerHTML", joined):
        risks.append("Potential code/XSS/command injection vector detected in added lines (`eval`/`exec`/`shell=True`).")
    if re.search(r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]", joined, re.IGNORECASE):
        risks.append("Possible hardcoded credential or secret string detected in diff.")
    if re.search(r"\bexcept\s*:\s*pass\b|catch\s*\([^)]*\)\s*\{\s*\}", joined):
        risks.append("Empty exception handler silently swallows errors without logging or rethrowing.")
    if not any("test" in f.lower() for f in changed_files):
        suggestions.append("Add targeted unit/regression tests covering the modified paths (`tests/`).")
    if len(added_lines) > 250:
        suggestions.append("Diff adds >250 lines; consider splitting into smaller single-purpose commits/functions.")
    if not risks:
        risks.append("No high-severity security or regression patterns matched; verify edge-case error handling manually.")
    if not suggestions:
        suggestions.append("Verify CI checks pass cleanly across all modified modules before merge.")

    title = meta.get("title", "Pull Request")
    author = (meta.get("user") or {}).get("login", "contributor")
    file_count = len(changed_files) or int(meta.get("changed_files", 0))
    confidence = "High" if file_count <= 8 and len(added_lines) <= 200 else "Medium"

    risk_md = "\n".join(f"- {r}" for r in risks)
    sug_md = "\n".join(f"- {s}" for s in suggestions)
    return (
        f"## PR Review: {title} (#{meta.get('number')})\n\n"
        f"### Summary of Changes\n"
        f"PR opened by `@{author}` touching **{file_count} file(s)** (+{meta.get('additions', len(added_lines))}/-{meta.get('deletions', 0)} lines). "
        f"Changes target `{', '.join(changed_files[:5]) or 'repository files'}`.\n\n"
        f"### Identified Risks\n{risk_md}\n\n"
        f"### Improvement Suggestions\n{sug_md}\n\n"
        f"### Confidence Score\n**{confidence}**\n"
    )


def review_with_claude(meta: dict, diff_text: str, api_key: str) -> str:
    prompt = (
        "Review this GitHub Pull Request and output strictly Markdown with four sections:\n"
        "1. Summary of changes (2-3 sentences)\n"
        "2. Identified risks (bulleted list)\n"
        "3. Improvement suggestions (bulleted list)\n"
        "4. Confidence score: Low / Medium / High\n\n"
        f"PR Title: {meta.get('title')}\n"
        f"PR Body: {(meta.get('body') or '')[:1500]}\n\n"
        f"Diff (truncated to 12k chars):\n{diff_text[:12000]}"
    )
    body = json.dumps(
        {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated Claude Code PR Reviewer")
    parser.add_argument("--pr", required=True, help="Full GitHub Pull Request URL")
    parser.add_argument("--out", help="Optional Markdown file path to save the review")
    args = parser.parse_args()

    owner, repo, number = parse_pr_url(args.pr)
    meta = json.loads(gh_fetch(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"))
    diff_text = gh_fetch(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", accept="application/vnd.github.v3.diff")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        review_md = review_with_claude(meta, diff_text, api_key)
    else:
        review_md = analyze_diff_static(meta, diff_text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(review_md)
    print(review_md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
