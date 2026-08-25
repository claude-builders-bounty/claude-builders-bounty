#!/usr/bin/env python3
"""Review a GitHub pull request and emit structured Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    diff: str
    files_changed: int
    additions: int
    deletions: int


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Not a GitHub PR URL: {url}")
    owner, repo, number = match.group(1), match.group(2), int(match.group(3))
    return owner, repo.rstrip(".git"), number


def gh_json(args: list[str]) -> dict:
    proc = subprocess.run(
        ["gh", "api", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def load_pr(url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(url)
    meta = gh_json([f"repos/{owner}/{repo}/pulls/{number}"])
    diff = subprocess.run(
        ["gh", "pr", "diff", str(number), "--repo", f"{owner}/{repo}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=meta["title"],
        body=meta.get("body") or "",
        author=meta["user"]["login"],
        diff=diff,
        files_changed=meta.get("changed_files", 0),
        additions=meta.get("additions", 0),
        deletions=meta.get("deletions", 0),
    )


def heuristic_review(pr: PullRequest) -> tuple[str, list[str], list[str], str]:
    risks: list[str] = []
    suggestions: list[str] = []
    diff_lower = pr.diff.lower()

    if "password" in diff_lower or "api_key" in diff_lower or "secret" in diff_lower:
        risks.append("Diff mentions credentials or secrets — verify nothing sensitive is committed.")
    if pr.additions > 500:
        risks.append(f"Large addition (+{pr.additions} lines) increases review surface and merge risk.")
    if pr.files_changed > 10:
        risks.append(f"{pr.files_changed} files touched — consider splitting if unrelated.")
    if not pr.body.strip():
        suggestions.append("Add a PR description explaining motivation, testing, and rollout notes.")
    if "test" not in diff_lower and "spec" not in diff_lower:
        suggestions.append("No obvious test changes — confirm behavior is covered or manually verified.")
    if not risks:
        risks.append("No high-severity patterns detected by static heuristics.")
    if not suggestions:
        suggestions.append("Consider adding a short verification checklist for reviewers.")

    summary = (
        f"PR #{pr.number} by @{pr.author} changes {pr.files_changed} file(s) "
        f"(+{pr.additions}/-{pr.deletions}) for “{pr.title}”."
    )
    confidence = "Medium"
    if pr.files_changed <= 3 and pr.additions < 200:
        confidence = "High"
    elif pr.additions > 800:
        confidence = "Low"
    return summary, risks, suggestions, confidence


def claude_review(pr: PullRequest, model: str) -> tuple[str, list[str], list[str], str]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return heuristic_review(pr)

    prompt = f"""Review this pull request and respond ONLY with JSON:
{{"summary":"2-3 sentences","risks":["..."],"suggestions":["..."],"confidence":"Low|Medium|High"}}

PR: {pr.title}
Author: {pr.author}
Files: {pr.files_changed}, +{pr.additions}/-{pr.deletions}

Description:
{pr.body[:4000]}

Diff (truncated):
{pr.diff[:12000]}
"""
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        text = data["content"][0]["text"]
        parsed = json.loads(text.strip().strip("`").removeprefix("json"))
        return (
            parsed["summary"],
            list(parsed.get("risks", [])),
            list(parsed.get("suggestions", [])),
            parsed.get("confidence", "Medium"),
        )
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, IndexError):
        return heuristic_review(pr)


def render_markdown(
    pr: PullRequest,
    summary: str,
    risks: list[str],
    suggestions: list[str],
    confidence: str,
) -> str:
    lines = [
        f"# PR Review — {pr.owner}/{pr.repo}#{pr.number}",
        "",
        "## Summary",
        summary,
        "",
        "## Identified risks",
        *[f"- {item}" for item in risks],
        "",
        "## Improvement suggestions",
        *[f"- {item}" for item in suggestions],
        "",
        f"## Confidence score: **{confidence}**",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Structured Markdown PR review")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model when ANTHROPIC_API_KEY is set",
    )
    parser.add_argument("-o", "--output", help="Write review to file instead of stdout")
    args = parser.parse_args()

    pr = load_pr(args.pr)
    summary, risks, suggestions, confidence = claude_review(pr, args.model)
    markdown = render_markdown(pr, summary, risks, suggestions, confidence)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
