#!/usr/bin/env python3
"""CLI entrypoint for the Claude PR reviewer bounty.

The tool intentionally has no third-party runtime dependencies. It accepts a
GitHub pull request URL, downloads the diff, applies deterministic review
heuristics, and prints a structured Markdown comment that can be pasted into a
PR discussion or used by a GitHub Action.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable

PR_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")
FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*)$", re.MULTILINE)
ADDED_LINE_RE = re.compile(r"^\+(?!\+\+)(.*)$", re.MULTILINE)
REMOVED_LINE_RE = re.compile(r"^-(?!--)(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: str

    @property
    def api_diff_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{self.number}"

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_RE.fullmatch(url.rstrip("/"))
    if not match:
        raise ValueError("--pr must be a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return PullRequestRef(**match.groupdict())


def fetch_pr_diff(ref: PullRequestRef, token: str | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-reviewer/0.1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(ref.api_diff_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"GitHub API returned {exc.code}: {detail}") from exc


def summarize_diff(diff: str) -> dict[str, object]:
    files = [m.group(2) for m in FILE_RE.finditer(diff)]
    added = ADDED_LINE_RE.findall(diff)
    removed = REMOVED_LINE_RE.findall(diff)
    extensions: dict[str, int] = {}
    for path in files:
        ext = path.rsplit('.', 1)[-1] if '.' in path else '[no extension]'
        extensions[ext] = extensions.get(ext, 0) + 1
    return {
        "files": files,
        "file_count": len(files),
        "added_count": len(added),
        "removed_count": len(removed),
        "extensions": extensions,
        "added_lines": added,
    }


def find_risks(summary: dict[str, object]) -> list[str]:
    risks: list[str] = []
    files = [str(f) for f in summary["files"]]
    added_lines = [str(line) for line in summary["added_lines"]]
    joined_added = "\n".join(added_lines)

    if summary["file_count"] == 0:
        return ["No file-level diff was found; verify the PR is accessible and not empty."]
    if summary["file_count"] > 20 or summary["added_count"] > 800:
        risks.append("Large change surface; split review by subsystem and require focused tests before merge.")
    if any(path.endswith((".yml", ".yaml")) and ".github/workflows/" in path for path in files):
        risks.append("Workflow files changed; review permissions, secrets exposure, and third-party actions carefully.")
    if re.search(r"\b(eval|exec)\s*\(", joined_added):
        risks.append("Dynamic code execution appears in added lines; confirm inputs are trusted and sandboxed.")
    if re.search(r"shell\s*=\s*True|os\.system\(", joined_added):
        risks.append("Shell command execution appears in added lines; check for command-injection risk.")
    if re.search(r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}", joined_added, re.I):
        risks.append("Possible hardcoded credential pattern detected in added lines.")
    if any(path.endswith(("package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod")) for path in files):
        risks.append("Dependencies or package metadata changed; verify lockfiles and supply-chain implications.")
    if not risks:
        risks.append("No obvious high-risk patterns detected by the deterministic heuristics; still review domain logic manually.")
    return risks


def find_suggestions(summary: dict[str, object]) -> list[str]:
    files = [str(f) for f in summary["files"]]
    suggestions: list[str] = []
    has_tests = any(re.search(r"(^|/)(test|tests|__tests__)/|(_test\.|\.test\.|\.spec\.)", path) for path in files)
    has_docs = any(path.lower().endswith(("readme.md", ".md")) for path in files)

    if not has_tests:
        suggestions.append("Add or update tests that exercise the changed behavior, especially edge cases and failure paths.")
    if has_docs:
        suggestions.append("Check that documentation examples match the implemented CLI/API exactly.")
    if summary["removed_count"] and summary["added_count"]:
        suggestions.append("Confirm removed behavior is either obsolete or covered by migration notes/backward compatibility checks.")
    if not suggestions:
        suggestions.append("Keep the PR focused and include command output from the relevant test suite in the final description.")
    return suggestions


def confidence(summary: dict[str, object], risks: Iterable[str]) -> str:
    risk_text = "\n".join(risks).lower()
    if "credential" in risk_text or "shell command" in risk_text or "dynamic code" in risk_text:
        return "Low"
    if summary["file_count"] <= 5 and summary["added_count"] <= 250:
        return "High"
    return "Medium"


def render_review(ref: PullRequestRef, diff: str) -> str:
    summary = summarize_diff(diff)
    risks = find_risks(summary)
    suggestions = find_suggestions(summary)
    conf = confidence(summary, risks)
    files_preview = ", ".join(summary["files"][:8]) or "no files detected"
    if len(summary["files"]) > 8:
        files_preview += f", and {len(summary['files']) - 8} more"

    return (
        "## PR Review Summary\n\n"
        f"Reviewed {ref.html_url}. This PR changes **{summary['file_count']} file(s)** "
        f"with approximately **{summary['added_count']} added** and **{summary['removed_count']} removed** lines. "
        f"The touched files are: {files_preview}.\n\n"
        "## Identified Risks\n"
        f"{bullet_list(risks)}\n\n"
        "## Improvement Suggestions\n"
        f"{bullet_list(suggestions)}\n\n"
        "## Confidence Score\n"
        f"**{conf}**\n"
    )


def bullet_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request and emit structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    args = parser.parse_args(argv)

    try:
        ref = parse_pr_url(args.pr)
        diff = fetch_pr_diff(ref, os.getenv("GITHUB_TOKEN"))
        print(render_review(ref, diff))
    except Exception as exc:  # noqa: BLE001 - CLI should report cleanly
        print(f"claude-review: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
