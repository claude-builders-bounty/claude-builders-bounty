#!/usr/bin/env python3
"""Structured PR review helper for Claude Code builders.

The tool accepts a GitHub PR URL or a local diff file/stdin and produces a
Markdown review comment with summary, risks, suggestions, and confidence.
"""
from __future__ import annotations

import argparse
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PR_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")


@dataclass(frozen=True)
class DiffStats:
    files_changed: int
    added: int
    removed: int
    tests_touched: int
    config_touched: int
    dependency_touched: int
    has_deletions: bool
    has_large_change: bool


def github_pr_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Expected GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_pr_diff(pr_url: str, timeout: float = 20.0) -> str:
    request = urllib.request.Request(
        github_pr_diff_url(pr_url),
        headers={"User-Agent": "claude-review/1.0", "Accept": "text/x-diff"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310: user-requested public PR diff fetch
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching PR diff") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff: {exc.reason}") from exc


def iter_changed_files(diff_text: str) -> Iterable[str]:
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                yield parts[3][2:] if parts[3].startswith("b/") else parts[3]


def analyze_diff(diff_text: str) -> DiffStats:
    files = list(dict.fromkeys(iter_changed_files(diff_text)))
    added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    lowered = [f.lower() for f in files]
    tests_touched = sum(1 for f in lowered if "test" in f or f.endswith(".spec.ts") or f.endswith(".spec.js"))
    config_touched = sum(1 for f in lowered if f.startswith(".github/") or f.endswith((".yml", ".yaml", ".toml", ".json")))
    dependency_touched = sum(1 for f in lowered if Path(f).name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "requirements.txt", "package.json"})
    return DiffStats(
        files_changed=len(files),
        added=added,
        removed=removed,
        tests_touched=tests_touched,
        config_touched=config_touched,
        dependency_touched=dependency_touched,
        has_deletions=removed > 0,
        has_large_change=(added + removed) > 600 or len(files) > 15,
    )


def summarize(stats: DiffStats) -> str:
    parts = [f"This PR changes {stats.files_changed} file(s) with approximately +{stats.added}/-{stats.removed} lines."]
    if stats.tests_touched:
        parts.append("It includes test-related changes, which improves review confidence.")
    else:
        parts.append("I do not see test files in the diff, so behavior verification should be checked before merge.")
    if stats.config_touched or stats.dependency_touched:
        parts.append("The diff also touches configuration or dependency surfaces that may affect CI/runtime behavior.")
    return " ".join(parts[:3])


def risks(stats: DiffStats) -> list[str]:
    items: list[str] = []
    if not stats.tests_touched:
        items.append("No obvious test updates detected in the diff.")
    if stats.dependency_touched:
        items.append("Dependency/lockfile changes can introduce supply-chain or version compatibility risk.")
    if stats.config_touched:
        items.append("Configuration/workflow changes may affect CI, deployment, or local setup.")
    if stats.has_large_change:
        items.append("Large diff size increases regression and missed-edge-case risk.")
    if stats.has_deletions:
        items.append("Removed code should be checked for backwards-compatibility or migration impact.")
    return items or ["No high-signal structural risks detected from the diff metadata alone."]


def suggestions(stats: DiffStats) -> list[str]:
    items = ["Run the relevant test suite and include the exact command/output in the PR before merge."]
    if not stats.tests_touched:
        items.append("Add or update focused tests for the changed behavior.")
    if stats.config_touched or stats.dependency_touched:
        items.append("Verify CI and installation from a clean checkout after the config/dependency changes.")
    if stats.has_large_change:
        items.append("Consider splitting unrelated changes into smaller PRs or documenting the review path.")
    items.append("Ask for maintainer confirmation on any product behavior or API contract changes.")
    return items


def confidence(stats: DiffStats, diff_text: str) -> str:
    if not diff_text.strip():
        return "Low"
    score = 1
    if stats.tests_touched:
        score += 1
    if not stats.has_large_change:
        score += 1
    if not (stats.config_touched or stats.dependency_touched):
        score += 1
    return "High" if score >= 4 else "Medium" if score >= 2 else "Low"


def render_review(source: str, diff_text: str) -> str:
    stats = analyze_diff(diff_text)
    risk_lines = "\n".join(f"- {item}" for item in risks(stats))
    suggestion_lines = "\n".join(f"- {item}" for item in suggestions(stats))
    return (
        "## Claude PR Review\n\n"
        f"**Source:** {source}\n\n"
        "### Summary of changes\n"
        f"{summarize(stats)}\n\n"
        "### Identified risks\n"
        f"{risk_lines}\n\n"
        "### Improvement suggestions\n"
        f"{suggestion_lines}\n\n"
        "### Confidence score\n"
        f"{confidence(stats, diff_text)}\n"
    )


def read_diff(args: argparse.Namespace) -> tuple[str, str]:
    if args.diff_file:
        path = Path(args.diff_file)
        return str(path), path.read_text(encoding="utf-8", errors="replace")
    if args.pr:
        return args.pr, fetch_pr_diff(args.pr, timeout=args.timeout)
    if not sys.stdin.isatty():
        return "stdin", sys.stdin.read()
    raise SystemExit("Provide --pr, --diff-file, or pipe a unified diff to stdin.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print a structured Markdown comment.")
    parser.add_argument("--pr", help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Local unified diff file to review")
    parser.add_argument("--timeout", type=float, default=20.0, help="Network timeout for --pr fetch")
    args = parser.parse_args(argv)
    source, diff_text = read_diff(args)
    print(render_review(source, diff_text), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
