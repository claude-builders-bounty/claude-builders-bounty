#!/usr/bin/env python3
"""CLI helper for generating structured PR review comments.

The tool is intentionally dependency-free so it can run inside GitHub Actions,
Claude Code hooks, and local shells without setup beyond Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
HUNK_RE = re.compile(r"^@@", re.MULTILINE)
ADDED_RE = re.compile(r"^\+(?!\+\+)", re.MULTILINE)
REMOVED_RE = re.compile(r"^-(?!--)", re.MULTILINE)

RISK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bdelete\b|\bremove\b|\bdrop\b|DROP\s+TABLE|DROP\s+COLUMN", "Destructive operation changed or introduced."),
    (r"\beval\s*\(|exec\s*\(|subprocess|shell=True|child_process", "Command execution or dynamic evaluation touched."),
    (r"password|secret|token|api[_-]?key|credential", "Secret or credential handling touched."),
    (r"auth|permission|role|admin|rbac|oauth|session", "Authentication or authorization behavior touched."),
    (r"\b(SELECT|INSERT|UPDATE|DELETE FROM|ALTER TABLE|CREATE TABLE|DROP TABLE|DROP COLUMN)\b|\.query\(|raw\(", "Database query behavior touched."),
    (r"webhook|checkout|payment|stripe|billing", "Payment or webhook behavior touched."),
    (r"migration|schema|column|index", "Schema or migration behavior touched."),
    (r"http|fetch\(|request\(|url", "Network request behavior touched."),
)


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def diff_url(self) -> str:
        return f"{self.url}.diff"


@dataclass(frozen=True)
class DiffSummary:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    tests_changed: bool
    docs_changed: bool
    risk_flags: list[str]


def parse_pr_url(value: str) -> PullRequest:
    match = PR_RE.search(value.strip())
    if not match:
        raise ValueError(f"Unsupported GitHub PR URL: {value}")
    return PullRequest(match.group("owner"), match.group("repo"), match.group("number"))


def fetch_text(url: str, token: str | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def summarize_diff(diff: str) -> DiffSummary:
    files = sorted(set(DIFF_FILE_RE.findall(diff)))
    additions = len(ADDED_RE.findall(diff))
    deletions = len(REMOVED_RE.findall(diff))
    hunks = len(HUNK_RE.findall(diff))
    lower_files = [path.lower() for path in files]
    tests_changed = any("test" in path or "spec" in path for path in lower_files)
    docs_changed = any(path.endswith((".md", ".mdx", ".rst")) or "docs/" in path for path in lower_files)

    risk_flags: list[str] = []
    for pattern, label in RISK_PATTERNS:
        if re.search(pattern, diff, flags=re.IGNORECASE):
            risk_flags.append(label)

    return DiffSummary(
        files=files,
        additions=additions,
        deletions=deletions,
        hunks=hunks,
        tests_changed=tests_changed,
        docs_changed=docs_changed,
        risk_flags=risk_flags,
    )


def build_prompt(pr_url: str | None, diff: str, summary: DiffSummary) -> str:
    file_list = "\n".join(f"- {path}" for path in summary.files[:30]) or "- No files detected"
    return textwrap.dedent(
        f"""
        You are a senior code reviewer. Review this pull request diff and return
        only a Markdown comment with these sections: Summary, Identified risks,
        Improvement suggestions, Confidence.

        Pull request: {pr_url or "local diff"}

        Diff facts:
        - Files changed: {len(summary.files)}
        - Additions: {summary.additions}
        - Deletions: {summary.deletions}
        - Hunks: {summary.hunks}
        - Tests changed: {summary.tests_changed}
        - Docs changed: {summary.docs_changed}

        Changed files:
        {file_list}

        Diff:
        ```diff
        {diff[:24000]}
        ```
        """
    ).strip()


def run_claude(prompt: str, command: str) -> str:
    try:
        result = subprocess.run(
            [command, "-p", prompt],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Claude CLI command not found: {command}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Claude CLI timed out while reviewing the diff") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or "no stderr"
        raise RuntimeError(f"Claude CLI failed with exit {result.returncode}: {stderr}")
    return result.stdout.strip()


def offline_review(pr_url: str | None, summary: DiffSummary) -> str:
    scope = "small" if summary.additions + summary.deletions < 120 else "moderate"
    files = ", ".join(summary.files[:5]) if summary.files else "the submitted diff"

    risk_bullets: list[str] = []
    if summary.risk_flags:
        for flag in summary.risk_flags[:5]:
            risk_bullets.append(f"- {flag} Verify the changed behavior in `{files}` with focused tests.")
    if not summary.tests_changed:
        risk_bullets.append("- No test files were changed. That leaves the behavioral path dependent on manual review.")
    if not risk_bullets:
        risk_bullets.append("- No major risks found.")

    suggestions: list[str] = []
    if not summary.tests_changed:
        suggestions.append("- Add at least one regression test that fails before this patch and passes after it.")
    if summary.risk_flags:
        suggestions.append("- Include a short validation note in the PR body covering the highest-risk changed path.")
    if summary.docs_changed and not summary.tests_changed:
        suggestions.append("- If this is documentation-only, state that explicitly in the PR body.")
    if not suggestions:
        suggestions.append("- No immediate suggestions.")

    confidence = "Medium"
    if not summary.files or summary.hunks == 0:
        confidence = "Low"
    elif summary.tests_changed and len(summary.risk_flags) <= 1:
        confidence = "High"

    pr_sentence = f" for {pr_url}" if pr_url else ""
    return "\n".join(
        [
            "## Summary",
            "",
            f"This {scope} pull request{pr_sentence} changes {len(summary.files)} file(s), with {summary.additions} additions and {summary.deletions} deletions.",
            f"The main review surface appears to be `{files}`, based on the diff metadata.",
            "",
            "## Identified risks",
            "",
            *risk_bullets,
            "",
            "## Improvement suggestions",
            "",
            *suggestions,
            "",
            "## Confidence",
            "",
            confidence,
        ]
    )


def write_output(path: str | None, content: str) -> None:
    if path:
        Path(path).write_text(content + "\n", encoding="utf-8")
    else:
        print(content)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review comment.")
    parser.add_argument("--pr", help="GitHub pull request URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Path to a local unified diff file. Overrides network fetch when provided.")
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout.")
    parser.add_argument("--prompt-only", action="store_true", help="Print the review prompt instead of a review.")
    parser.add_argument("--use-claude", action="store_true", help="Use Claude CLI for the final review.")
    parser.add_argument("--claude-command", default="claude", help="Claude CLI command name. Default: claude")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary JSON instead of Markdown.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.pr and not args.diff_file:
        parser.error("Provide --pr or --diff-file")

    pr: PullRequest | None = parse_pr_url(args.pr) if args.pr else None
    if args.diff_file:
        diff = Path(args.diff_file).read_text(encoding="utf-8")
    else:
        diff = fetch_text(pr.diff_url, os.environ.get("GITHUB_TOKEN"))  # type: ignore[union-attr]

    summary = summarize_diff(diff)

    if args.json:
        write_output(args.output, json.dumps(summary.__dict__, indent=2, sort_keys=True))
        return 0

    prompt = build_prompt(pr.url if pr else None, diff, summary)
    if args.prompt_only:
        write_output(args.output, prompt)
        return 0

    if args.use_claude:
        review = run_claude(prompt, args.claude_command)
    else:
        review = offline_review(pr.url if pr else None, summary)

    write_output(args.output, review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
