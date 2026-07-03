#!/usr/bin/env python3
"""Lightweight PR review agent.

Usage:
  python3 scripts/claude_review.py --pr https://github.com/owner/repo/pull/123

The script fetches a PR diff from GitHub and prints a structured Markdown review.
It is intentionally dependency-free so it can run in CI or locally.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    risky: bool = False


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.rstrip("/"))
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def github_get(url: str, accept: str = "application/vnd.github+json") -> bytes:
    headers = {"User-Agent": "claude-review-agent", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API error {exc.code}: {body[:500]}") from exc


def fetch_pr(owner: str, repo: str, number: int) -> dict:
    raw = github_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    return json.loads(raw.decode("utf-8"))


def fetch_diff(owner: str, repo: str, number: int) -> str:
    raw = github_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        accept="application/vnd.github.v3.diff",
    )
    return raw.decode("utf-8", errors="replace")


def analyze_diff(diff: str) -> tuple[list[FileChange], list[str], list[str]]:
    files: list[FileChange] = []
    risks: list[str] = []
    suggestions: list[str] = []
    current: FileChange | None = None

    risky_patterns = {
        "secrets/env handling": re.compile(r"(SECRET|TOKEN|PASSWORD|API_KEY|\.env)", re.I),
        "database/schema change": re.compile(r"(migration|schema|CREATE TABLE|ALTER TABLE|DROP TABLE)", re.I),
        "auth/permission path": re.compile(r"(auth|permission|role|session|jwt)", re.I),
        "destructive operation": re.compile(r"(rm -rf|DROP TABLE|DELETE FROM|TRUNCATE|--force)", re.I),
    }

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            path = line.split(" b/", 1)[-1]
            current = FileChange(path=path)
            files.append(current)
            for label, pattern in risky_patterns.items():
                if pattern.search(path):
                    current.risky = True
                    risks.append(f"`{path}` touches a {label}; review carefully.")
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"): current.additions += 1
        if line.startswith("-") and not line.startswith("---"): current.deletions += 1
        if line.startswith("+"):
            for label, pattern in risky_patterns.items():
                if pattern.search(line):
                    current.risky = True
                    risks.append(f"Added code/content in `{current.path}` matches {label}.")

    total_added = sum(f.additions for f in files)
    total_deleted = sum(f.deletions for f in files)
    if total_added + total_deleted > 500:
        risks.append("Large diff size may hide regressions; request focused reviewer attention.")
    if any(f.path.endswith(("package.json", "package-lock.json", "pnpm-lock.yaml")) for f in files):
        suggestions.append("Verify dependency changes are necessary and lockfiles are consistent.")
    if not any("test" in f.path.lower() for f in files):
        suggestions.append("No obvious test file changed; consider asking for regression or usage evidence.")
    if not risks:
        risks.append("No high-risk patterns detected by the static diff scan.")
    if not suggestions:
        suggestions.append("Review naming, error handling, and edge cases against the issue acceptance criteria.")
    return files, dedupe(risks), dedupe(suggestions)


def dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def confidence(files: list[FileChange], risks: list[str]) -> str:
    changed = sum(f.additions + f.deletions for f in files)
    risky_count = sum(1 for f in files if f.risky)
    if changed > 500 or risky_count >= 3:
        return "Low"
    if changed > 150 or risky_count:
        return "Medium"
    return "High"


def render(pr: dict, files: list[FileChange], risks: list[str], suggestions: list[str]) -> str:
    title = pr.get("title") or "Untitled PR"
    additions = sum(f.additions for f in files)
    deletions = sum(f.deletions for f in files)
    file_list = ", ".join(f"`{f.path}`" for f in files[:8]) or "No files parsed"
    if len(files) > 8:
        file_list += f", and {len(files) - 8} more"
    conf = confidence(files, risks)
    return "\n".join([
        "## PR Review",
        "",
        "### Summary",
        f"This PR, **{title}**, changes {len(files)} file(s) with roughly +{additions}/-{deletions} lines. "
        f"Primary files reviewed: {file_list}.",
        "The review below is generated from the PR metadata and diff and should be paired with project-specific tests before merge.",
        "",
        "### Identified Risks",
        *[f"- {risk}" for risk in risks],
        "",
        "### Improvement Suggestions",
        *[f"- {suggestion}" for suggestion in suggestions],
        "",
        f"### Confidence: {conf}",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()
    owner, repo, number = parse_pr_url(args.pr)
    pr = fetch_pr(owner, repo, number)
    diff = fetch_diff(owner, repo, number)
    files, risks, suggestions = analyze_diff(diff)
    print(render(pr, files, risks, suggestions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
