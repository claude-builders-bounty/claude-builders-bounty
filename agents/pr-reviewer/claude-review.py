#!/usr/bin/env python3
"""CLI tool that fetches a GitHub PR diff and returns a structured Markdown review.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr owner/repo/123
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

Environment variables:
    GH_TOKEN                GitHub personal access token (optional, raises rate limits)
    ANTHROPIC_API_KEY       Anthropic API key (optional; falls back to rule-based review)
    ANTHROPIC_MODEL         Model name (default: claude-sonnet-4-20250514)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.error

GH_TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int


def parse_pr_url(url: str) -> PRInfo:
    patterns = [
        r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
        r"(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?P<number>\d+)",
    ]
    for pattern in patterns:
        m = re.match(pattern, url.strip())
        if m:
            return PRInfo(
                owner=m.group("owner"),
                repo=m.group("repo"),
                number=int(m.group("number")),
            )
    raise ValueError(f"Cannot parse PR URL: {url}")


def _use_curl(url: str) -> str:
    cmd = ["curl", "-sL", "-H", "Accept: application/vnd.github.v3+json"]
    if GH_TOKEN:
        cmd.extend(["-H", f"Authorization: token {GH_TOKEN}"])
    cmd.append(url)
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr.strip()}")
    return result.stdout


def github_api(path: str) -> dict:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if GH_TOKEN:
        req.add_header("Authorization", f"token {GH_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError:
        return json.loads(_use_curl(url))


def fetch_diff(info: PRInfo) -> tuple[str, dict]:
    pr = github_api(f"/repos/{info.owner}/{info.repo}/pulls/{info.number}")
    diff_url = pr["diff_url"]
    req = urllib.request.Request(diff_url)
    if GH_TOKEN:
        req.add_header("Authorization", f"token {GH_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            diff = resp.read().decode()
    except urllib.error.URLError:
        diff = _use_curl(diff_url)
    return diff, pr


def count_changes(diff: str) -> tuple[int, int, int]:
    additions = 0
    deletions = 0
    files = 0
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            files += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return files, additions, deletions


def rule_based_review(diff: str, pr: dict) -> str:
    files, additions, deletions = count_changes(diff)
    title = pr.get("title", "")
    body = pr.get("body", "") or ""

    lowered_diff = diff.lower()
    lowered_title = title.lower()
    lowered_body = body.lower()

    # ── File-type detection ──
    file_paths = re.findall(r"^diff --git a/(.+) b/\1$", diff, re.MULTILINE)
    extensions = {Path(p).suffix.lower() for p in file_paths if Path(p).suffix}
    has_tests = any("test" in p.lower() for p in file_paths)

    risks: list[str] = []
    suggestions: list[str] = []

    # ── Risk patterns ──
    if re.search(r"rm\s+[-]r[-]?f|rm\s+[-]f[-]?r", lowered_diff):
        risks.append("Contains `rm -rf` or similar destructive shell command.")
    if re.search(r"eval\(|exec\(|compile\(", lowered_diff):
        risks.append("Use of `eval`, `exec`, or dynamic code compilation can introduce code-injection risks.")
    if re.search(r"select\s+.*\s+from\s+.*\+\s*[\'\"]|\.query\s*\(.*\+\s*[\'\"]", lowered_diff, re.DOTALL):
        risks.append("Possible SQL injection via string concatenation in a query.")
    if re.search(r"innerhtml\s*=|dangerouslysetinnerhtml", lowered_diff):
        risks.append("Direct HTML insertion may expose XSS vulnerabilities if input is not sanitized.")
    if re.search(r"password|secret|token|api[-_]?key\s*[=:]\s*[\"\'][^\"\']{4,}[\"\']", diff, re.IGNORECASE):
        risks.append("Possible hardcoded credential or secret reference; verify no plaintext secrets are committed.")
    if re.search(r"md5|sha1|des\b|rc4", lowered_diff) and not re.search(r"sha256|sha384|sha512|aes|bcrypt|argon2", lowered_diff):
        risks.append("Use of weak or deprecated cryptographic primitives detected.")
    if re.search(r"pickle\.loads|yaml\.load\(|\.loads\(.*object_hook", lowered_diff):
        risks.append("Unsafe deserialization path may allow arbitrary object execution.")
    if re.search(r"threading\.\w+|asyncio\.create_task|settimeout\s*\(", lowered_diff) and re.search(r"lock|semaphore|mutex", lowered_diff) is None:
        risks.append("Concurrency-related change without explicit synchronization primitives; check for race conditions.")
    if "console.log" in lowered_diff or "print(" in lowered_diff or "debugger;" in lowered_diff:
        risks.append("Debug logging statements may have been left in the code.")
    if re.search(r"\b(todo|fixme|hack|xxx)\b", lowered_diff):
        risks.append("Contains TODO/FIXME/HACK comments that may indicate incomplete or temporary work.")
    if files > 20:
        risks.append("Large number of changed files; review carefully for unintended changes.")
    if additions + deletions > 1000:
        risks.append("Large diff; consider breaking into smaller PRs for easier review.")

    # ── Context-aware suggestions ──
    if not has_tests and additions > 30:
        suggestions.append("No test files appear in the diff; consider adding unit or integration tests for the changed logic.")
    if ".py" in extensions and not has_tests:
        suggestions.append("For Python changes, add or update pytest cases covering the new behavior.")
    if any(ext in extensions for ext in [".ts", ".tsx", ".js", ".jsx"]) and not has_tests:
        suggestions.append("For TypeScript/JavaScript changes, consider adding Vitest/Jest coverage or updating existing tests.")
    if ".rs" in extensions:
        suggestions.append("For Rust changes, run `cargo clippy` and ensure the new code handles `Result`/`Option` explicitly.")
    if ".sol" in extensions:
        suggestions.append("For Solidity changes, consider adding reentrancy guards and verify integer math with tests.")
    if re.search(r"migration|schema|alter\s+table|create\s+table", lowered_diff):
        suggestions.append("Database schema changes should include a rollback plan and be verified against production-like data.")
    if re.search(r"^\+.*TODO|^\+.*FIXME", diff, re.MULTILINE):
        suggestions.append("Resolve newly introduced TODO/FIXME comments before merging if possible.")
    if len(body.strip()) < 50:
        suggestions.append("PR description is brief; consider expanding with motivation, acceptance criteria, and test notes.")
    if files > 10 and additions + deletions > 500:
        suggestions.append("Consider splitting unrelated changes into smaller, focused PRs to simplify review.")

    # ── Fallback messages ──
    if not risks:
        risks.append("No obvious high-risk patterns detected by automated scan.")
    if not suggestions:
        suggestions.append("Automated scan found no specific suggestions beyond normal code review.")

    # ── Confidence score ──
    high_risk = any(r.startswith(("Contains", "Use of", "Possible", "Unsafe", "Direct")) for r in risks)
    if high_risk:
        confidence = "Low"
    elif additions + deletions < 80 and not high_risk and has_tests:
        confidence = "High"
    else:
        confidence = "Medium"

    # ── Summary ──
    if "fix" in lowered_title:
        change_type = "bug fix"
    elif "feat" in lowered_title or "add" in lowered_title:
        change_type = "feature addition"
    elif "test" in lowered_title:
        change_type = "test-only change"
    elif "docs" in lowered_title or "readme" in lowered_title:
        change_type = "documentation update"
    elif "refactor" in lowered_title:
        change_type = "refactoring"
    else:
        change_type = "change"

    summary = (
        f"This PR is a **{change_type}** touching {files} file(s) "
        f"with {additions} additions and {deletions} deletions. "
        f"Title: '{title}'. The automated scan {'did not find' if confidence == 'High' else 'found some'} "
        f"patterns worth reviewer attention."
    )

    lines = [
        "## PR Review",
        "",
        f"### Summary\n\n{summary}",
        "",
        "### Identified Risks",
    ]
    for risk in risks:
        lines.append(f"- {risk}")
    lines.extend(["", "### Improvement Suggestions"])
    for suggestion in suggestions:
        lines.append(f"- {suggestion}")
    lines.extend(["", f"### Confidence Score\n\n**{confidence}**"])
    return "\n".join(lines)


def claude_api_review(diff: str, pr: dict) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    prompt = f"""You are a senior software engineer reviewing a pull request. Analyze the diff below and produce a structured Markdown review with exactly these sections:

### Summary
2-3 sentences describing the overall change.

### Identified Risks
A bullet list of risks (empty if none).

### Improvement Suggestions
A bullet list of actionable suggestions (empty if none).

### Confidence Score
One of: Low / Medium / High

PR Title: {pr.get('title', '')}
PR Body: {pr.get('body', '') or 'No description provided.'}

Diff:
```diff
{diff[:90000]}
```
"""

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["content"][0]["text"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured PR review")
    parser.add_argument("--pr", required=True, help="GitHub PR URL or owner/repo/number")
    parser.add_argument("--output", type=Path, help="File to write review to")
    parser.add_argument("--rule-based", action="store_true", help="Force rule-based review")
    args = parser.parse_args(argv)

    info = parse_pr_url(args.pr)
    try:
        diff, pr = fetch_diff(info)
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch PR: {e}", file=sys.stderr)
        return 1

    if not diff.strip():
        print("PR diff is empty.", file=sys.stderr)
        return 1

    if ANTHROPIC_API_KEY and not args.rule_based:
        try:
            review = claude_api_review(diff, pr)
        except Exception as e:
            print(f"Claude API review failed ({e}), falling back to rule-based review.", file=sys.stderr)
            review = rule_based_review(diff, pr)
    else:
        review = rule_based_review(diff, pr)

    if args.output:
        args.output.write_text(review, encoding="utf-8")
        print(f"Review written to {args.output}")
    else:
        print(review)

    return 0


if __name__ == "__main__":
    sys.exit(main())
