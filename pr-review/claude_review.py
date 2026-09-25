#!/usr/bin/env python3
"""Write a structured review from a GitHub pull request diff.

Usage: python3 claude_review.py --pr https://github.com/owner/repo/pull/123
The diff comes from `gh pr diff`. No model API is called.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

RISKS = [
    ("shell execution", re.compile(r"shell\s*=\s*True|os\.system\(|subprocess\.(?:Popen|run|call)\(")),
    ("removed test or guard", re.compile(r"^-\s*(?:def test_|assert )", re.M)),
    ("secret-shaped assignment", re.compile(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{8,}")),
    ("broad exception swallow", re.compile(r"except\s+Exception\s*:\s*(?:pass|\.\.\.)")),
    ("SQL string concatenation", re.compile(r"(?i)(?:execute|query)\(\s*f?['\"].*(?:select|insert|update|delete).*(?:\+|%|\{)")),
]
SUGGESTIONS = [
    ("large added block", re.compile(r"^\+(?!\+\+).{180,}", re.M), "Split added lines longer than 180 characters so the diff stays reviewable."),
    ("new TODO", re.compile(r"^\+.*\bTODO\b", re.M), "Resolve the new TODO before merge or link it to an issue."),
    ("debug print", re.compile(r"^\+\s*(?:print|console\.log)\(", re.M), "Remove debug output added in this diff, or gate it behind a verbose flag."),
]


def parse(url: str) -> tuple[str, str, str]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise SystemExit("The --pr value must be a GitHub pull request URL.")
    owner, repo, number = match.groups()
    return f"{owner}/{repo}", number, url


def diff_for(repo: str, number: str) -> str:
    result = subprocess.run(
        ["gh", "pr", "diff", number, "--repo", repo],
        text=True, capture_output=True, timeout=60,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "gh pr diff failed")
    return result.stdout


def added_lines(diff: str) -> list[str]:
    return [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]


def review(url: str) -> str:
    repo, number, _ = parse(url)
    diff = diff_for(repo, number)
    files = re.findall(r"^\+\+\+ b/(.+)$", diff, re.M)
    added = added_lines(diff)
    removed = [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    risks = []
    for name, pattern in RISKS:
        if pattern.search(diff):
            risks.append(name)
    suggestions = [text for _name, pattern, text in SUGGESTIONS if pattern.search(diff)]
    if len(added) > 400:
        suggestions.append("The diff adds more than 400 lines. Ask the author to split independent changes.")
    if not suggestions:
        suggestions.append("No mechanical suggestion fired. Read the named files for behavior changes the patterns cannot see.")
    score = "Low" if len(risks) >= 2 or len(added) > 800 else "Medium" if risks or len(added) > 200 else "High"
    file_text = ", ".join(files[:8]) or "no file headers found"
    summary = (
        f"This review covers PR {number} in {repo}. "
        f"The diff touches {len(files)} file(s): {file_text}. "
        f"It adds {len(added)} lines and removes {len(removed)} lines."
    )
    lines = [
        f"# Review {repo}#{number}", "",
        "## Summary", "", summary, "",
        "## Risks", "",
    ]
    lines += [f"- {item}" for item in risks] or ["- None of the mechanical risk patterns matched."]
    lines += ["", "## Suggestions", ""]
    lines += [f"- {item}" for item in suggestions]
    lines += ["", "## Confidence", "", score, ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True)
    args = parser.parse_args()
    sys.stdout.write(review(args.pr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
