#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable, List, Optional


PR_URL_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<num>\d+)/?$")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def diff_url(self) -> str:
        return f"{self.url}.diff"


@dataclass(frozen=True)
class DiffStats:
    files: List[str]
    additions: int
    deletions: int
    test_files: int
    docs_files: int


def parse_pr_url(value: str) -> PullRequestRef:
    match = PR_URL_RE.match(value.strip())
    if not match:
        raise ValueError("expected PR URL like https://github.com/owner/repo/pull/123")
    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("num")),
    )


def fetch_diff(ref: PullRequestRef) -> str:
    request = urllib.request.Request(
        ref.diff_url,
        headers={"User-Agent": "claude-review-agent", "Accept": "text/plain"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub returned HTTP {error.code} for {ref.diff_url}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"could not fetch PR diff: {error.reason}") from error


def changed_files(diff: str) -> List[str]:
    files: List[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                files.append(path[2:] if path.startswith("b/") else path)
    return files


def diff_stats(diff: str) -> DiffStats:
    files = changed_files(diff)
    additions = 0
    deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1
    test_files = sum(1 for path in files if re.search(r"(^|/)(test|tests|spec|__tests__)/|(\.|_)(test|spec)\.", path, re.I))
    docs_files = sum(1 for path in files if path.lower().endswith((".md", ".mdx", ".rst", ".txt")))
    return DiffStats(files=files, additions=additions, deletions=deletions, test_files=test_files, docs_files=docs_files)


def summary(ref: PullRequestRef, stats: DiffStats) -> str:
    file_text = "file" if len(stats.files) == 1 else "files"
    return (
        f"This PR changes {len(stats.files)} {file_text} in `{ref.owner}/{ref.repo}`, "
        f"with {stats.additions} additions and {stats.deletions} deletions. "
        f"The review below focuses on risk signals visible from the diff and follow-up checks "
        f"that should be confirmed before merge."
    )


def has_any_path(files: Iterable[str], patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, path, re.I) for path in files for pattern in patterns)


def risks(stats: DiffStats, diff: str) -> List[str]:
    found: List[str] = []
    if len(stats.files) == 0:
        found.append("No changed files were detected in the diff; confirm the PR is still open and accessible.")
    if stats.additions + stats.deletions > 800:
        found.append("Large diff size increases review risk; split or request focused reviewer coverage if possible.")
    if has_any_path(stats.files, [r"package-lock\.json$", r"pnpm-lock\.yaml$", r"yarn\.lock$", r"requirements.*\.txt$", r"pyproject\.toml$"]):
        found.append("Dependency or lockfile changes can affect install and supply-chain behavior.")
    if has_any_path(stats.files, [r"migrations?/", r"schema", r"\.sql$"]):
        found.append("Database or migration files changed; verify forward migration, rollback expectations, and data safety.")
    if has_any_path(stats.files, [r"auth", r"session", r"permission", r"security", r"middleware"]):
        found.append("Authentication, authorization, or request middleware paths changed; verify access-control behavior.")
    if stats.test_files == 0 and stats.docs_files < len(stats.files):
        found.append("No test files changed; confirm existing tests cover the modified behavior.")
    if re.search(r"delete\s+from|drop\s+table|truncate|rm\s+-rf|--force", diff, re.I):
        found.append("Diff contains destructive-operation keywords; inspect the execution path carefully.")
    if not found:
        found.append("No high-risk diff signals were detected by the static review.")
    return found


def suggestions(stats: DiffStats) -> List[str]:
    items: List[str] = []
    if stats.test_files == 0:
        items.append("Add or identify regression coverage for the changed behavior before merge.")
    if stats.docs_files > 0:
        items.append("Preview the rendered Markdown/docs to catch formatting and navigation issues.")
    if stats.additions + stats.deletions > 300:
        items.append("Ask reviewers to focus on the highest-risk files first, then do a second pass for naming and cleanup.")
    items.append("Run the repository's lint, typecheck, and test commands and paste the exact results into the PR.")
    items.append("Confirm the PR description explains user-visible behavior, migration impact, and rollback considerations where relevant.")
    return items


def confidence(stats: DiffStats) -> str:
    total = stats.additions + stats.deletions
    if total == 0 or total > 800:
        return "Low"
    if total > 250 or stats.test_files == 0:
        return "Medium"
    return "High"


def render_review(ref: PullRequestRef, diff: str) -> str:
    stats = diff_stats(diff)
    risk_items = risks(stats, diff)
    suggestion_items = suggestions(stats)
    changed = "\n".join(f"- `{path}`" for path in stats.files[:20])
    if len(stats.files) > 20:
        changed += f"\n- ...and {len(stats.files) - 20} more files"

    return "\n".join(
        [
            "## PR Review",
            "",
            "### Summary",
            "",
            summary(ref, stats),
            "",
            "### Changed Files",
            "",
            changed or "- None detected.",
            "",
            "### Identified Risks",
            "",
            *[f"- {item}" for item in risk_items],
            "",
            "### Improvement Suggestions",
            "",
            *[f"- {item}" for item in suggestion_items],
            "",
            f"### Confidence: {confidence(stats)}",
            "",
            "_Generated by `claude-review` from the public GitHub PR diff._",
            "",
        ]
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--output", help="Optional file path for Markdown output")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        ref = parse_pr_url(args.pr)
        review = render_review(ref, fetch_diff(ref))
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            output.write(review)
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
