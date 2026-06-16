#!/usr/bin/env python3
"""Review a GitHub pull request diff and emit a structured Markdown comment."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$")
SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".ts",
    ".tsx",
}
TEST_MARKERS = (
    "/test/",
    "/tests/",
    "__tests__",
    ".spec.",
    ".test.",
    "test_",
    "_test.",
)
CONFIG_MARKERS = (
    ".github/workflows/",
    "dockerfile",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "cargo.toml",
    "cargo.lock",
)


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


@dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    added_lines: list[tuple[str, str]]
    removed_lines: list[tuple[str, str]]
    truncated: bool = False

    @property
    def total_lines(self) -> int:
        return self.additions + self.deletions

    @property
    def has_tests(self) -> bool:
        return any(is_test_path(path) for path in self.files)

    @property
    def has_source_changes(self) -> bool:
        return any(is_source_path(path) and not is_test_path(path) for path in self.files)


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number))


def fetch_pr_diff(ref: PullRequestRef, token: str | None = None, timeout: int = 30) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(ref.diff_url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {ref.diff_url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch {ref.diff_url}: {exc.reason}") from exc


def parse_diff(diff_text: str, max_chars: int | None = None) -> DiffStats:
    truncated = False
    if max_chars and len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars]
        truncated = True

    files: list[str] = []
    additions = 0
    deletions = 0
    added_lines: list[tuple[str, str]] = []
    removed_lines: list[tuple[str, str]] = []
    current_file = ""

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            current_file = extract_file_from_git_header(raw_line)
            if current_file and current_file not in files:
                files.append(current_file)
            continue
        if raw_line.startswith("+++ ") or raw_line.startswith("--- "):
            continue
        if raw_line.startswith("+"):
            additions += 1
            added_lines.append((current_file, raw_line[1:]))
        elif raw_line.startswith("-"):
            deletions += 1
            removed_lines.append((current_file, raw_line[1:]))

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        added_lines=added_lines,
        removed_lines=removed_lines,
        truncated=truncated,
    )


def extract_file_from_git_header(line: str) -> str:
    # Example: diff --git a/src/app.py b/src/app.py
    parts = line.split()
    if len(parts) >= 4:
        path = parts[3]
        return path[2:] if path.startswith("b/") else path
    return ""


def is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(marker in normalized for marker in TEST_MARKERS)


def is_source_path(path: str) -> bool:
    return Path(path).suffix.lower() in SOURCE_EXTENSIONS


def is_config_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(marker in normalized for marker in CONFIG_MARKERS)


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def detect_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    file_list = ", ".join(stats.files[:8]) if stats.files else "no parsed files"

    if not stats.files:
        risks.append("No files could be parsed from the diff, so the review may be incomplete.")

    if stats.truncated:
        risks.append("The diff was truncated before analysis; inspect the remaining hunks manually.")

    if stats.has_source_changes and not stats.has_tests:
        risks.append("Source code changed without matching test files in the diff.")

    if any(is_config_path(path) for path in stats.files):
        risks.append("Configuration, dependency, or CI files changed and may affect runtime or deployment behavior.")

    if stats.total_lines > 800:
        risks.append(f"Large diff size ({stats.total_lines} changed lines) increases review and regression risk.")

    if stats.deletions > stats.additions * 2 and stats.deletions > 40:
        risks.append("The PR deletes substantially more code than it adds; confirm removed behavior is intentionally retired.")

    risky_added = find_risky_patterns(stats.added_lines)
    for path, label in risky_added:
        risks.append(f"Potentially risky pattern `{label}` appears in `{path or 'unknown file'}`.")

    if len(stats.files) > 12:
        risks.append(f"The PR touches {len(stats.files)} files; split verification by subsystem before merge.")

    if not risks:
        risks.append(f"No obvious high-risk pattern was found in the parsed diff ({file_list}).")

    return unique(risks)


def find_risky_patterns(lines: list[tuple[str, str]]) -> list[tuple[str, str]]:
    checks = [
        (re.compile(r"\beval\s*\("), "eval(...)"),
        (re.compile(r"\bexec\s*\("), "exec(...)"),
        (re.compile(r"shell\s*=\s*True"), "shell=True"),
        (re.compile(r"\brm\s+-rf\b|\brm\s+-fr\b"), "rm -rf"),
        (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
        (re.compile(r"\bDELETE\s+FROM\b(?![\s\S]{0,80}\bWHERE\b)", re.IGNORECASE), "DELETE FROM without nearby WHERE"),
        (re.compile(r"\bSECRET\b|\bTOKEN\b|\bPASSWORD\b", re.IGNORECASE), "secret-like variable"),
    ]
    matches: list[tuple[str, str]] = []
    for path, line in lines:
        for pattern, label in checks:
            if pattern.search(line):
                matches.append((path, label))
    return matches[:8]


def make_suggestions(stats: DiffStats, risks: list[str]) -> list[str]:
    suggestions: list[str] = []

    if stats.has_source_changes and not stats.has_tests:
        suggestions.append("Add or update tests that exercise the changed source paths before merging.")

    if any(is_config_path(path) for path in stats.files):
        suggestions.append("Document any new environment variables, permissions, or CI behavior introduced by the config changes.")

    if stats.total_lines > 800 or len(stats.files) > 12:
        suggestions.append("Consider splitting the PR or adding a reviewer checklist by subsystem to reduce merge risk.")

    if any("risky pattern" in risk.lower() for risk in risks):
        suggestions.append("Audit the flagged risky lines manually and add guardrails or input validation where applicable.")

    if stats.has_tests:
        suggestions.append("Run the touched test suite and include the exact command/output in the PR conversation.")
    else:
        suggestions.append("Include a short manual verification note in the PR so reviewers can reproduce the result.")

    suggestions.append("Keep the final review comment focused on merge-blocking issues first, then non-blocking improvements.")
    return unique(suggestions)


def confidence_for(stats: DiffStats, risks: list[str]) -> str:
    if not stats.files or stats.truncated:
        return "Low"
    risk_count = len([risk for risk in risks if not risk.startswith("No obvious")])
    if stats.total_lines <= 250 and risk_count <= 1 and (stats.has_tests or not stats.has_source_changes):
        return "High"
    if risk_count >= 4 or stats.total_lines > 800:
        return "Low"
    return "Medium"


def summarize(stats: DiffStats, ref: PullRequestRef | None = None) -> str:
    subject = ref.url if ref else "the supplied diff"
    if not stats.files:
        return f"The review inspected {subject}, but no files could be parsed from the diff. Treat the findings as incomplete until the diff source is checked."

    file_phrase = ", ".join(stats.files[:5])
    if len(stats.files) > 5:
        file_phrase += f", and {len(stats.files) - 5} more"
    return (
        f"This review inspected {subject} across {len(stats.files)} changed file(s): {file_phrase}. "
        f"The parsed diff contains {stats.additions} added line(s) and {stats.deletions} removed line(s), with emphasis on tests, configuration changes, and risky code patterns."
    )


def build_markdown_review(stats: DiffStats, ref: PullRequestRef | None = None) -> str:
    risks = detect_risks(stats)
    suggestions = make_suggestions(stats, risks)
    confidence = confidence_for(stats, risks)
    files = [f"`{path}`" for path in stats.files[:20]] or ["No files parsed"]

    sections = [
        "## Claude PR Review",
        "",
        "### Summary of changes",
        summarize(stats, ref),
        "",
        "### Identified risks",
        format_bullets(risks),
        "",
        "### Improvement suggestions",
        format_bullets(suggestions),
        "",
        "### Changed files",
        format_bullets(files),
        "",
        f"### Confidence score: {confidence}",
    ]
    return "\n".join(sections) + "\n"


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_claude_prompt(diff_text: str, ref: PullRequestRef | None) -> str:
    target = ref.url if ref else "a local diff"
    return textwrap.dedent(
        f"""\
        You are reviewing {target}. Return only Markdown with exactly these sections:
        ## Claude PR Review
        ### Summary of changes
        Write 2-3 concise sentences.
        ### Identified risks
        Bulleted list.
        ### Improvement suggestions
        Bulleted list.
        ### Confidence score: Low / Medium / High
        Pick one score and explain briefly.

        Focus on correctness, security, maintainability, test coverage, and CI risk.

        Diff:
        ```diff
        {diff_text}
        ```
        """
    )


def try_claude_review(diff_text: str, ref: PullRequestRef | None, timeout: int) -> str | None:
    if not shutil.which("claude"):
        return None
    prompt = build_claude_prompt(diff_text, ref)
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stdout.strip()
    if result.returncode == 0 and "### Identified risks" in output and "### Improvement suggestions" in output:
        return output + "\n"
    return None


def post_github_comment(ref: PullRequestRef, markdown: str, token: str) -> str:
    api_url = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments"
    payload = json.dumps({"body": markdown}).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "claude-pr-review-agent",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("html_url", api_url)


def read_diff(args: argparse.Namespace) -> tuple[str, PullRequestRef | None]:
    if args.pr:
        ref = parse_pr_url(args.pr)
        return fetch_pr_diff(ref, token=args.github_token, timeout=args.timeout), ref
    if args.diff_file:
        return Path(args.diff_file).read_text(encoding="utf-8"), None
    raise ValueError("Provide either --pr or --diff-file")


def create_review(args: argparse.Namespace) -> tuple[str, PullRequestRef | None]:
    diff_text, ref = read_diff(args)
    stats = parse_diff(diff_text, max_chars=args.max_diff_chars)
    markdown = None
    if args.use_claude:
        clipped = diff_text[: args.max_diff_chars] if args.max_diff_chars else diff_text
        markdown = try_claude_review(clipped, ref, timeout=args.claude_timeout)
    return markdown or build_markdown_review(stats, ref), ref


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request and emit a structured Markdown comment.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Path to a local unified diff file")
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review as a GitHub PR comment")
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token for private PRs or posting comments")
    parser.add_argument("--max-diff-chars", type=int, default=120_000, help="Maximum diff characters to analyze")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds")
    parser.add_argument("--use-claude", action="store_true", help="Use Claude CLI when available, otherwise fall back to heuristic review")
    parser.add_argument("--claude-timeout", type=int, default=120, help="Claude CLI timeout in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        markdown, ref = create_review(args)
        write_output(markdown, args.output)
        if args.post_comment:
            if ref is None:
                raise ValueError("--post-comment requires --pr")
            if not args.github_token:
                raise ValueError("--post-comment requires --github-token or GITHUB_TOKEN")
            comment_url = post_github_comment(ref, markdown, args.github_token)
            print(f"Posted review comment: {comment_url}", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
