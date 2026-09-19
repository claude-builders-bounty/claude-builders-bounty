#!/usr/bin/env python3
"""Review a public GitHub pull request and print a structured Markdown report."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_pr(url: str) -> tuple[str, str, int]:
    match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?", url)
    if not match:
        raise ValueError("expected https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_diff(url: str) -> str:
    request = urllib.request.Request(url + ".diff", headers={"User-Agent": "claude-review/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def heuristic_review(diff: str, owner: str, repo: str, number: int) -> str:
    files = re.findall(r"^diff --git a/(.*?) b/", diff, re.MULTILINE)
    additions = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    risks = []
    lowered = diff.lower()
    if any(word in lowered for word in ("password", "token", "secret", "api_key")):
        risks.append("Review changed credential-like strings for accidental secret exposure.")
    if any(word in lowered for word in ("delete ", "drop table", "truncate", "rm -rf")):
        risks.append("Destructive operations are present; verify authorization and guardrails.")
    if not risks:
        risks.append("No obvious security-sensitive pattern was detected by the lightweight fallback review.")
    file_list = ", ".join(f"`{path}`" for path in files[:8]) or "the submitted patch"
    return "\n".join(
        [
            f"# Review: {owner}/{repo}#{number}",
            "",
            "## Summary",
            f"The PR changes {file_list}. The patch contains {additions} additions and {deletions} deletions.",
            "The review was generated from the public GitHub diff.",
            "",
            "## Identified risks",
            *[f"- {risk}" for risk in risks],
            "",
            "## Improvement suggestions",
            "- Add or update focused tests for the changed behavior.",
            "- Run the repository's lint and test checks in CI before merging.",
            "",
            "## Confidence",
            "Medium",
        ]
    )


def claude_review(diff: str, url: str) -> str | None:
    if not shutil.which("claude"):
        return None
    prompt = f"""Review this GitHub PR: {url}
Return only Markdown with exactly these sections: Summary, Identified risks, Improvement suggestions, Confidence.
Summary must be 2-3 sentences. Risks and suggestions must be lists. Confidence must be Low, Medium, or High.

PR diff:
{diff[:120000]}"""
    result = subprocess.run(["claude", "-p", prompt], text=True, capture_output=True, timeout=180, check=False)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True, help="public GitHub pull request URL")
    args = parser.parse_args()
    try:
        owner, repo, number = parse_pr(args.pr)
        diff = fetch_diff(args.pr)
        report = claude_review(diff, args.pr) or heuristic_review(diff, owner, repo, number)
    except (ValueError, OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
