#!/usr/bin/env python3
"""Claude Code PR reviewer — fetches a GitHub PR diff and returns structured Markdown."""

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
from typing import Any

PR_URL_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
SECRET_RE = re.compile(
    r"\b(api_key|token|password|secret|passwd|private_key|privatekey)\b\s*=\s*['\"][^'\"]+['\"]",
    re.IGNORECASE,
)
SQL_FMT_RE = re.compile(r"execute\(\s*['\"].*?%s.*?['\"]\s*%|execute\(\s*f['\"].*?\{.*?\}")
EMPTY_CATCH_RE = re.compile(r"except\s+Exception:\s*pass|catch\s*\(e\)\s*\{\s*\}")

CONFIDENCE_LEVELS = ("Low", "Medium", "High")


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: str
    title: str
    body: str
    diff: str


@dataclass
class Review:
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "risks": self.risks,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
        }


def parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    match = PR_URL_RE.search(pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    return match.group(1), match.group(2), match.group(3)


def fetch_pr(pr_url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(pr_url)
    title = f"PR #{number}"
    body = ""
    diff = ""

    try:
        view = subprocess.run(
            ["gh", "pr", "view", pr_url, "--json", "title,body"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if view.returncode == 0:
            data = json.loads(view.stdout)
            title = data.get("title", title)
            body = data.get("body") or ""

        diff_cmd = subprocess.run(
            ["gh", "pr", "diff", pr_url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if diff_cmd.returncode == 0:
            diff = diff_cmd.stdout
    except (OSError, json.JSONDecodeError):
        pass

    if not diff.strip():
        diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
        req = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                diff = response.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to fetch PR diff: {exc}") from exc

    if not diff.strip():
        raise RuntimeError("Fetched PR diff is empty. Cannot perform review.")

    return PullRequest(owner, repo, number, title, body, diff)


def added_lines(diff: str) -> list[str]:
    return [
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def analyze_static(pr: PullRequest) -> Review:
    additions = added_lines(pr.diff)
    risks: list[str] = []
    suggestions: list[str] = []

    for line in additions:
        if SECRET_RE.search(line):
            risks.append("Possible hardcoded secret or credential detected in source code.")
            suggestions.append("Move secrets to environment variables or a secret manager.")
        if "console.log" in line and "test" not in pr.repo.lower():
            risks.append("Debug output `console.log` left in production code.")
            suggestions.append("Remove debugging statements or use a structured logger.")
        if SQL_FMT_RE.search(line):
            risks.append("Potential SQL injection: dynamic SQL formatting detected.")
            suggestions.append("Use parameterized queries instead of string formatting.")
        if EMPTY_CATCH_RE.search(line):
            risks.append("Empty catch/except block: errors are silently swallowed.")
            suggestions.append("Log the caught exception or rethrow it.")

    if len(additions) > 500:
        risks.append("Large PR size: review complexity increases the chance of missed edge cases.")
        suggestions.append("Consider splitting this PR into smaller, focused changes.")

    if not risks:
        risks.append("No critical static code risks detected in the changes.")
    if not suggestions:
        suggestions.append("No immediate structural improvements required.")

    summary = (
        f"This PR (#{pr.number}) titled \"{pr.title}\" adds {len(additions)} lines across the diff. "
    )
    if pr.body.strip():
        snippet = " ".join(pr.body.strip().split())[:160]
        summary += f"The author describes it as: {snippet}."
    else:
        summary += "No PR description was provided, so intent must be inferred from the diff alone."

    return Review(
        summary=summary,
        risks=_dedupe(risks),
        suggestions=_dedupe(suggestions),
        confidence="Medium",
    )


def analyze_with_claude(pr: PullRequest, api_key: str) -> Review | None:
    diff = pr.diff
    if len(diff) > 100_000:
        diff = diff[:100_000] + "\n\n[Diff truncated due to size limit]"

    prompt = f"""You are a senior software engineer reviewing a pull request.

PR Title: {pr.title}
PR Description: {pr.body}

PR Diff:
```diff
{diff}
```

Respond with raw JSON only (no markdown fences) using these keys:
- "summary": 2-3 sentences describing what changed
- "risks": list of technical risks, security issues, or bugs
- "suggestions": list of actionable improvements
- "confidence": exactly one of "Low", "Medium", or "High"
"""

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        parsed = json.loads(text)
        confidence = _normalize_confidence(parsed.get("confidence", "Medium"))
        return Review(
            summary=str(parsed.get("summary", "")).strip(),
            risks=[str(r) for r in parsed.get("risks", [])],
            suggestions=[str(s) for s in parsed.get("suggestions", [])],
            confidence=confidence,
        )
    except Exception:
        return None


def review_pr(pr: PullRequest, api_key: str | None = None) -> Review:
    if api_key:
        claude_review = analyze_with_claude(pr, api_key)
        if claude_review and claude_review.summary:
            return claude_review
    return analyze_static(pr)


def format_markdown(review: Review) -> str:
    lines = [
        "## PR Review",
        "",
        "### Summary of Changes",
        review.summary,
        "",
        "### Identified Risks",
    ]
    lines.extend(f"- {risk}" for risk in review.risks)
    lines.extend(["", "### Improvement Suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in review.suggestions)
    lines.extend(["", f"### Confidence Score: **{review.confidence}**"])
    return "\n".join(lines) + "\n"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _normalize_confidence(value: str) -> str:
    for level in CONFIDENCE_LEVELS:
        if level.lower() in value.lower():
            return level
    return "Medium"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and output structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args(argv)

    try:
        pr = fetch_pr(args.pr)
        review = review_pr(pr, os.environ.get("ANTHROPIC_API_KEY"))
        sys.stdout.write(format_markdown(review))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
