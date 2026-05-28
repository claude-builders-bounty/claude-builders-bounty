#!/usr/bin/env python3
"""Review a GitHub pull request diff and emit a structured Markdown comment."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_PR_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?$"
)
FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*)$")
HUNK_RE = re.compile(r"^@@")
GENERATED_HINTS = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "go.sum",
)
TEST_HINTS = ("/test", "test_", "_test.", ".spec.", ".test.", "__tests__", "tests/")
SECURITY_HINTS = (
    "auth",
    "permission",
    "token",
    "secret",
    "password",
    "csrf",
    "xss",
    "sql",
    "session",
    "cookie",
)
CONFIG_HINTS = (".github/", "dockerfile", "compose", ".env", "config", "settings", ".gitignore")


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: str
    url: str


@dataclass
class FileChange:
    old_path: str
    new_path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    is_deleted: bool = False
    is_new: bool = False

    @property
    def path(self) -> str:
        return self.new_path if self.new_path != "/dev/null" else self.old_path


@dataclass
class DiffStats:
    files: list[FileChange]
    additions: int
    deletions: int
    truncated: bool = False


def parse_pr_url(url: str) -> PullRequest:
    match = GITHUB_PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    parts = match.groupdict()
    return PullRequest(parts["owner"], parts["repo"], parts["number"], url.rstrip("/"))


def diff_url_for(pr: PullRequest) -> str:
    return f"https://github.com/{pr.owner}/{pr.repo}/pull/{pr.number}.diff"


def fetch_url(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": "claude-review-agent/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def parse_diff(diff: str, max_chars: int | None = None) -> DiffStats:
    truncated = False
    if max_chars is not None and len(diff) > max_chars:
        diff = diff[:max_chars]
        truncated = True

    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            current = FileChange(file_match.group(1), file_match.group(2))
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("new file mode"):
            current.is_new = True
        elif line.startswith("deleted file mode"):
            current.is_deleted = True
        elif line.startswith("--- /dev/null"):
            current.is_new = True
        elif line.startswith("+++ /dev/null"):
            current.is_deleted = True
        elif HUNK_RE.match(line):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1

    return DiffStats(
        files=files,
        additions=sum(item.additions for item in files),
        deletions=sum(item.deletions for item in files),
        truncated=truncated,
    )


def load_diff(pr_url: str | None, diff_file: str | None, max_chars: int | None) -> tuple[str, str]:
    if diff_file:
        source = Path(diff_file)
        return source.read_text(encoding="utf-8"), f"local diff file {source}"
    if not pr_url:
        raise ValueError("Provide --pr or --diff-file")
    pr = parse_pr_url(pr_url)
    url = diff_url_for(pr)
    return fetch_url(url), pr.url


def summarize_files(files: list[FileChange], limit: int = 8) -> str:
    if not files:
        return "No changed files were detected in the supplied diff."
    visible = files[:limit]
    names = ", ".join(change.path for change in visible)
    remaining = len(files) - len(visible)
    if remaining > 0:
        names += f", and {remaining} more"
    return names


def has_any(path: str, hints: Iterable[str]) -> bool:
    lower = path.lower()
    return any(hint in lower for hint in hints)


def build_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    paths = [change.path for change in stats.files]
    code_files = [
        path
        for path in paths
        if not path.endswith((".md", ".txt", ".rst", ".gitignore")) and not has_any(path, GENERATED_HINTS)
    ]
    test_files = [path for path in paths if has_any(path, TEST_HINTS)]

    if stats.truncated:
        risks.append("The diff was truncated for analysis, so later files or hunks may be missing from this review.")
    if len(stats.files) >= 20 or stats.additions + stats.deletions >= 800:
        risks.append("The PR has broad change volume, increasing the chance of missed regressions during manual review.")
    if code_files and not test_files:
        risks.append("Code files changed without an obvious accompanying test file in the diff.")
    if any(has_any(path, SECURITY_HINTS) for path in paths):
        risks.append("Authentication, authorization, credential, or query-related paths changed and deserve security-focused review.")
    if any(has_any(path, CONFIG_HINTS) for path in paths):
        risks.append("Configuration or automation files changed; deployment behavior may differ from local behavior.")
    if any(has_any(path, GENERATED_HINTS) for path in paths):
        risks.append("Dependency lockfiles changed; dependency resolution and supply-chain impact should be checked.")
    if any(change.is_deleted for change in stats.files):
        risks.append("At least one file was deleted, so downstream imports or documentation links may break.")
    if not risks:
        risks.append("No major structural risks were detected from the diff shape; review should still validate behavior and tests.")
    return risks


def build_suggestions(stats: DiffStats) -> list[str]:
    suggestions: list[str] = []
    paths = [change.path for change in stats.files]

    if any(not has_any(path, TEST_HINTS) for path in paths) and not any(has_any(path, TEST_HINTS) for path in paths):
        suggestions.append("Add or reference focused tests that exercise the changed behavior before merging.")
    if stats.additions + stats.deletions >= 300:
        suggestions.append("Split unrelated changes or add a short reviewer guide in the PR description to reduce review load.")
    if any(has_any(path, SECURITY_HINTS) for path in paths):
        suggestions.append("Include negative-path checks for unauthorized users, malformed input, and secret handling.")
    if any(has_any(path, GENERATED_HINTS) for path in paths):
        suggestions.append("Confirm dependency changes are intentional and generated by the expected package manager version.")
    if any(path.endswith((".md", ".rst")) for path in paths):
        suggestions.append("Preview the rendered documentation to catch broken links, headings, or formatting regressions.")
    if not suggestions:
        suggestions.append("Keep the PR description aligned with the final behavior and include the commands used to verify it.")
    return suggestions


def confidence(stats: DiffStats) -> str:
    if stats.truncated or len(stats.files) == 0:
        return "Low"
    if len(stats.files) > 15 or stats.additions + stats.deletions > 600:
        return "Medium"
    return "High"


def render_local_review(source: str, diff: str, max_chars: int | None) -> str:
    stats = parse_diff(diff, max_chars=max_chars)
    file_count = len(stats.files)
    change_word = "file" if file_count == 1 else "files"
    addition_word = "addition" if stats.additions == 1 else "additions"
    deletion_word = "deletion" if stats.deletions == 1 else "deletions"
    summary = (
        f"This PR changes {file_count} {change_word} with {stats.additions} {addition_word} "
        f"and {stats.deletions} {deletion_word}. The touched paths include {summarize_files(stats.files)}. "
        "The review below is based on the public diff and highlights structural risks for a human reviewer to confirm."
    )

    lines = [
        "## PR Review",
        "",
        "### Summary of Changes",
        summary,
        "",
        "### Identified Risks",
    ]
    lines.extend(f"- {risk}" for risk in build_risks(stats))
    lines.extend(["", "### Improvement Suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in build_suggestions(stats))
    lines.extend(["", f"### Confidence Score: {confidence(stats)}", "", f"_Source: {source}_"])
    return "\n".join(lines).rstrip() + "\n"


def claude_prompt(source: str, diff: str, max_chars: int | None) -> str:
    if max_chars is not None and len(diff) > max_chars:
        diff = diff[:max_chars] + "\n\n[Diff truncated by claude-review before sending to Claude.]\n"
    return f"""You are a Claude Code pull request reviewer sub-agent.

Review the PR diff from {source}. Return only Markdown with these sections:

## PR Review
### Summary of Changes
2-3 sentences.
### Identified Risks
Bulleted list.
### Improvement Suggestions
Bulleted list.
### Confidence Score: Low|Medium|High

Diff:
```diff
{diff}
```
"""


def run_claude_review(source: str, diff: str, max_chars: int | None, timeout: int) -> str | None:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None
    prompt = claude_prompt(source, diff, max_chars)
    completed = subprocess.run(
        [claude_bin, "-p", prompt],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    return completed.stdout.strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub PR diff and print a structured Markdown review comment.",
    )
    parser.add_argument("--pr", help="Public GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Read a local .diff file instead of fetching GitHub")
    parser.add_argument("--output", "-o", help="Write Markdown review to this file")
    parser.add_argument("--max-diff-chars", type=int, default=60000, help="Maximum diff characters to analyze")
    parser.add_argument(
        "--use-claude",
        action="store_true",
        help="Use the local Claude Code CLI when available; otherwise falls back to deterministic local review",
    )
    parser.add_argument("--claude-timeout", type=int, default=120, help="Timeout in seconds for Claude CLI")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        diff, source = load_diff(args.pr, args.diff_file, args.max_diff_chars)
        review = None
        if args.use_claude or os.getenv("CLAUDE_REVIEW_USE_CLAUDE") == "1":
            review = run_claude_review(source, diff, args.max_diff_chars, args.claude_timeout)
        if review is None:
            review = render_local_review(source, diff, args.max_diff_chars)
        if args.output:
            Path(args.output).write_text(review, encoding="utf-8")
        else:
            sys.stdout.write(review)
        return 0
    except Exception as exc:
        parser.exit(2, f"claude-review: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
