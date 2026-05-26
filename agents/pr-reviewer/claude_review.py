#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub PR URL or diff."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


PR_URL_PATTERN = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")
DIFF_FILE_PATTERN = re.compile(r"^\+\+\+ b/(.+)$")
SECRET_PATTERN = re.compile(r"\b(api[_-]?key|secret|password|token|private[_-]?key|BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY)\b", re.I)
DESTRUCTIVE_PATTERN = re.compile(r"\b(rm\s+-rf|DROP\s+TABLE|TRUNCATE|DELETE\s+FROM|git\s+push.+--force)\b", re.I)
HIGH_RISK_PATTERN = re.compile(r"\b(auth|billing|payment|invoice|tenant|permission|delete|migration|schema|token|secret)\b", re.I)
TEST_PATTERN = re.compile(r"(^|/)(test|tests|spec|__tests__)/|(\.test\.|\.spec\.)", re.I)
LOCKFILE_PATTERN = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|Cargo\.lock)$")
MIGRATION_PATTERN = re.compile(r"(^|/)(migrations?|schema|db)/|migration", re.I)


@dataclass
class DiffStats:
    files: set[str] = field(default_factory=set)
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    test_files: set[str] = field(default_factory=set)
    lockfiles: set[str] = field(default_factory=set)
    migration_files: set[str] = field(default_factory=set)
    secret_hits: list[str] = field(default_factory=list)
    destructive_hits: list[str] = field(default_factory=list)
    high_risk_files: set[str] = field(default_factory=set)


def pr_to_diff_url(pr_url: str) -> str:
    match = PR_URL_PATTERN.match(pr_url)
    if not match:
        raise ValueError("Expected GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "claude-pr-reviewer/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def current_repo_diff() -> str:
    return subprocess.check_output(["git", "diff", "main...HEAD"], text=True)


def analyze(diff: str) -> DiffStats:
    stats = DiffStats()
    current_file = ""

    for raw_line in diff.splitlines():
        line = raw_line.rstrip("\n")
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            current_file = match.group(1)
            stats.files.add(current_file)
            if TEST_PATTERN.search(current_file):
                stats.test_files.add(current_file)
            if LOCKFILE_PATTERN.search(current_file):
                stats.lockfiles.add(current_file)
            if MIGRATION_PATTERN.search(current_file):
                stats.migration_files.add(current_file)
            if HIGH_RISK_PATTERN.search(current_file):
                stats.high_risk_files.add(current_file)
            continue

        if line.startswith("@@"):
            stats.hunks += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            stats.additions += 1
            if SECRET_PATTERN.search(line):
                stats.secret_hits.append(current_file or "<unknown>")
            if DESTRUCTIVE_PATTERN.search(line):
                stats.destructive_hits.append(current_file or "<unknown>")
            if HIGH_RISK_PATTERN.search(line) and current_file:
                stats.high_risk_files.add(current_file)
        elif line.startswith("-") and not line.startswith("---"):
            stats.deletions += 1

    return stats


def risk_level(stats: DiffStats) -> tuple[str, list[str]]:
    reasons: list[str] = []
    score = 0

    if len(stats.files) > 10 or stats.additions + stats.deletions > 500:
        score += 2
        reasons.append("large diff size")
    if stats.migration_files:
        score += 2
        reasons.append("database/schema files changed")
    if stats.high_risk_files:
        score += 2
        reasons.append("auth/billing/security-sensitive terms detected")
    if stats.secret_hits:
        score += 3
        reasons.append("secret-like strings detected")
    if stats.destructive_hits:
        score += 3
        reasons.append("destructive command patterns detected")
    if not stats.test_files:
        score += 1
        reasons.append("no obvious tests changed")
    if stats.lockfiles:
        score += 1
        reasons.append("lockfile changed")

    if score >= 5:
        return "High", reasons
    if score >= 2:
        return "Medium", reasons
    return "Low", reasons or ["small focused diff"]


def confidence(stats: DiffStats, risk: str) -> int:
    value = 85
    if risk == "Medium":
        value -= 12
    elif risk == "High":
        value -= 25
    if not stats.test_files:
        value -= 8
    if stats.secret_hits or stats.destructive_hits:
        value -= 15
    return max(35, min(95, value))


def bullets(items: list[str] | set[str], empty: str) -> str:
    values = sorted(set(items))
    if not values:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in values)


def render(stats: DiffStats, source: str) -> str:
    risk, reasons = risk_level(stats)
    review_confidence = confidence(stats, risk)

    suggestions: list[str] = []
    if not stats.test_files:
        suggestions.append("Add or update tests that exercise the changed behavior.")
    if stats.migration_files:
        suggestions.append("Document migration/rollback expectations and test against a disposable database.")
    if stats.lockfiles:
        suggestions.append("Confirm dependency changes are intentional and compatible with the supported runtime.")
    if stats.secret_hits:
        suggestions.append("Remove secret-like strings or prove they are safe test placeholders.")
    if stats.destructive_hits:
        suggestions.append("Gate destructive commands behind explicit confirmation or remove them.")
    if not suggestions:
        suggestions.append("No blocking suggestions detected by the automated review.")

    return f"""## Automated PR Review

Source: {source}

### Summary

- Files changed: {len(stats.files)}
- Hunks: {stats.hunks}
- Additions: {stats.additions}
- Deletions: {stats.deletions}
- Tests touched: {len(stats.test_files)}

### Risk Assessment

Risk: **{risk}**

Reasons:
{bullets(reasons, "No risk triggers detected.")}

Sensitive areas:
{bullets(stats.high_risk_files, "No auth, billing, migration, secret, or tenant-sensitive files detected.")}

### Suggested Changes

{bullets(suggestions, "No suggestions.")}

### Confidence

{review_confidence}/100

### Notes

This is a deterministic first-pass review. A human or Claude Code should still read the changed files before merging.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured PR review from a GitHub PR URL or diff.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff", help="Path to a local diff file")
    source.add_argument("--stdin", action="store_true", help="Read diff from stdin")
    source.add_argument("--current", action="store_true", help="Review git diff main...HEAD in the current repository")
    parser.add_argument("--output", help="Write Markdown review to this path")
    parser.add_argument("--source-label", help="Override the source label shown in the Markdown output")
    args = parser.parse_args()

    if args.pr:
        diff = fetch_url(pr_to_diff_url(args.pr))
        label = args.pr
    elif args.diff:
        diff = Path(args.diff).read_text(encoding="utf-8")
        label = args.diff
    elif args.current:
        diff = current_repo_diff()
        label = "git diff main...HEAD"
    else:
        diff = sys.stdin.read()
        label = "stdin"

    review = render(analyze(diff), args.source_label or label)
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
