#!/usr/bin/env python3
"""Review a public GitHub PR diff and emit a structured Markdown comment.

This is intentionally deterministic and credential-free: it fetches only public
`.diff` URLs and never asks for GitHub tokens, API keys, or repository write
access. It can also review a local diff file for offline testing.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?$"
)

RISK_FILE_PATTERNS = (
    ("auth/security", re.compile(r"(auth|security|permission|policy|rbac|oauth)", re.I)),
    ("payments/billing", re.compile(r"(payment|billing|stripe|invoice|checkout)", re.I)),
    ("database/migration", re.compile(r"(migration|schema|sql|prisma|supabase|db/)", re.I)),
    ("CI/release", re.compile(r"(\.github/workflows|release|deploy|docker|package-lock|pnpm-lock)", re.I)),
    ("API/webhook", re.compile(r"(api|webhook|controller|route|endpoint)", re.I)),
    ("configuration", re.compile(r"(\.env|config|settings|secrets?)", re.I)),
)

RISK_LINE_PATTERNS = (
    ("credential-like text", re.compile(r"(api[_-]?key|token|secret|password|private[_-]?key)", re.I)),
    ("destructive data operation", re.compile(r"\b(drop|truncate|delete\s+from|rm\s+-rf)\b", re.I)),
    ("network/webhook change", re.compile(r"(webhook|fetch\(|axios\.|urllib|requests\.)", re.I)),
    ("error handling", re.compile(r"(catch\s*\(|except\s+|throw\s+|raise\s+|error)", re.I)),
)

TEST_FILE_RE = re.compile(r"(__tests__|tests?/|\.test\.|\.spec\.)", re.I)


@dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    tests_changed: bool
    risky_files: list[str]
    risky_lines: list[str]


def github_pr_to_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError(
            "Expected a public GitHub PR URL like "
            "https://github.com/owner/repo/pull/123"
        )
    return f"{pr_url.rstrip('/')}.diff"


def fetch_diff(pr_url: str, timeout: int = 20) -> str:
    diff_url = github_pr_to_diff_url(pr_url)
    request = urllib.request.Request(
        diff_url,
        headers={
            "User-Agent": "claude-pr-review-agent/0.1",
            "Accept": "text/x-diff,text/plain,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch public PR diff: {exc}") from exc


def parse_changed_files(diff_text: str) -> list[str]:
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3].removeprefix("b/"))
    return files


def iter_added_removed_lines(diff_text: str) -> Iterable[str]:
    for line in diff_text.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith(("+", "-")):
            yield line


def analyze_diff(diff_text: str) -> DiffStats:
    files = parse_changed_files(diff_text)
    additions = sum(
        1
        for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    deletions = sum(
        1
        for line in diff_text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    tests_changed = any(TEST_FILE_RE.search(path) for path in files)

    risky_files: list[str] = []
    for path in files:
        labels = [label for label, pattern in RISK_FILE_PATTERNS if pattern.search(path)]
        if labels:
            risky_files.append(f"{path} ({', '.join(labels)})")

    risky_lines: list[str] = []
    for raw_line in iter_added_removed_lines(diff_text):
        line = raw_line[:240]
        for label, pattern in RISK_LINE_PATTERNS:
            if pattern.search(line):
                risky_lines.append(f"{label}: `{line.strip()}`")
                break
        if len(risky_lines) >= 8:
            break

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        tests_changed=tests_changed,
        risky_files=risky_files[:10],
        risky_lines=risky_lines,
    )


def confidence_for(stats: DiffStats) -> str:
    total = stats.additions + stats.deletions
    risk_count = len(stats.risky_files) + len(stats.risky_lines)
    if total <= 160 and stats.tests_changed and risk_count <= 4:
        return "High"
    if total <= 500 and (stats.tests_changed or risk_count <= 4):
        return "Medium"
    return "Low"


def bullet_list(items: list[str], empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def render_review(pr_url: str, stats: DiffStats) -> str:
    changed_files = ", ".join(stats.files[:8]) if stats.files else "no files parsed"
    if len(stats.files) > 8:
        changed_files += f", and {len(stats.files) - 8} more"

    risk_items: list[str] = []
    if stats.risky_files:
        risk_items.append(
            "Sensitive areas changed: " + "; ".join(stats.risky_files[:6])
        )
    if not stats.tests_changed:
        risk_items.append("No obvious test/spec file was changed in this diff.")
    if stats.additions + stats.deletions > 500:
        risk_items.append(
            f"Large diff size ({stats.additions} additions, {stats.deletions} deletions) may hide regressions."
        )
    risk_items.extend(stats.risky_lines[:5])

    suggestions = [
        "Run the project test suite and the smallest focused test for the changed module.",
        "Confirm any user-facing behavior with one before/after example in the PR description.",
    ]
    if not stats.tests_changed:
        suggestions.insert(0, "Add or update at least one regression test before merge.")
    if stats.risky_files:
        suggestions.append(
            "Ask a maintainer familiar with the sensitive area to review the changed files."
        )
    if any("CI/release" in item for item in stats.risky_files):
        suggestions.append("Verify release or CI changes on a throwaway branch before merging.")
    if any("API/webhook" in item for item in stats.risky_files):
        suggestions.append("Check backwards compatibility for API/webhook payloads.")

    confidence = confidence_for(stats)
    return (
        f"## Summary\n"
        f"Reviewed public PR diff: {pr_url}\n\n"
        f"- Changed files: {len(stats.files)} ({changed_files})\n"
        f"- Diff size: +{stats.additions} / -{stats.deletions}\n"
        f"- Tests changed: {'yes' if stats.tests_changed else 'no obvious test files detected'}\n\n"
        f"## Identified risks\n"
        f"{bullet_list(risk_items, 'No high-risk file path or line pattern detected by the heuristic scan.')}\n\n"
        f"## Improvement suggestions\n"
        f"{bullet_list(suggestions, 'No specific follow-up suggestions.')}\n\n"
        f"## Confidence\n"
        f"{confidence}\n\n"
        f"_Generated by a deterministic public-diff review agent. It does not use repository write access, passwords, API keys, tokens, or private credentials._\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a public GitHub PR and print a structured Markdown comment."
    )
    parser.add_argument("--pr", required=True, help="Public GitHub PR URL")
    parser.add_argument(
        "--diff-file",
        help="Optional local diff file for offline testing instead of fetching the PR diff.",
    )
    args = parser.parse_args()

    try:
        if args.diff_file:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        else:
            diff_text = fetch_diff(args.pr)
        stats = analyze_diff(diff_text)
        sys.stdout.write(render_review(args.pr, stats))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should return a readable failure.
        sys.stderr.write(f"claude-review failed: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
