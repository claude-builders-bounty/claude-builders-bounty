#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub PR diff."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    risks: list[str]


def fetch_pr_diff(pr_url: str) -> str:
    diff_url = pr_url.rstrip("/") + ".diff"
    request = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_diff(diff: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    risks: list[str] = []

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            match = re.search(r" b/(.+)$", line)
            if match:
                files.append(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    lowered = diff.lower()
    if any(name.endswith((".env", ".pem", ".key")) for name in files):
        risks.append("Changes touch sensitive configuration or secret-adjacent files.")
    if any("migration" in name.lower() or "schema" in name.lower() for name in files):
        risks.append("Database or schema changes may need migration and rollback review.")
    if re.search(r"\b(subprocess|exec\(|eval\(|shell=True)\b", diff):
        risks.append("Command execution paths need input validation and quoting review.")
    if re.search(r"\bdelete\s+from\b", lowered) and not re.search(r"\bwhere\b", lowered):
        risks.append("SQL deletion appears without an obvious WHERE clause.")
    if any(name.endswith(("package-lock.json", "pnpm-lock.yaml", "yarn.lock")) for name in files):
        risks.append("Dependency lockfile changes should be checked for unexpected upgrades.")
    if additions + deletions > 500:
        risks.append("Large diff size increases review risk and may hide unrelated changes.")

    return DiffStats(files=files, additions=additions, deletions=deletions, risks=risks)


def confidence(stats: DiffStats) -> str:
    churn = stats.additions + stats.deletions
    if churn > 500 or len(stats.risks) >= 3:
        return "Low"
    if churn > 150 or stats.risks:
        return "Medium"
    return "High"


def render_review(pr_url: str, diff: str) -> str:
    stats = parse_diff(diff)
    file_count = len(stats.files)
    churn = stats.additions + stats.deletions
    changed = ", ".join(stats.files[:5]) if stats.files else "no files detected"
    if len(stats.files) > 5:
        changed += f", and {len(stats.files) - 5} more"

    summary = (
        f"This PR changes {file_count} file{'s' if file_count != 1 else ''} with "
        f"{stats.additions} additions and {stats.deletions} deletions. "
        f"The main touched paths are {changed}."
    )

    risks = stats.risks or ["No obvious high-risk patterns were detected from the diff alone."]
    suggestions = [
        "Run the repository's focused tests for the touched area before merge.",
        "Confirm the PR scope matches the linked issue and does not include unrelated cleanup.",
    ]
    if churn > 150:
        suggestions.append("Consider splitting follow-up cleanup from behavior changes if reviewers need a smaller diff.")
    if any("schema" in risk.lower() or "database" in risk.lower() for risk in risks):
        suggestions.append("Verify migration ordering, rollback behavior, and existing-data compatibility.")

    lines = [
        "# PR Review",
        "",
        f"Source: {pr_url}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Identified Risks",
        "",
        *[f"- {risk}" for risk in risks],
        "",
        "## Improvement Suggestions",
        "",
        *[f"- {suggestion}" for suggestion in suggestions],
        "",
        "## Confidence",
        "",
        confidence(stats),
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print structured Markdown.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL.")
    source.add_argument("--diff-file", help="Local diff file to review.")
    parser.add_argument("--output", help="Optional markdown output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.pr:
        pr_url = args.pr
        diff = fetch_pr_diff(pr_url)
    else:
        pr_url = f"file://{Path(args.diff_file).resolve()}"
        diff = Path(args.diff_file).read_text(encoding="utf-8")

    review = render_review(pr_url, diff)
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
