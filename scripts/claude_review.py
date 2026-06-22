#!/usr/bin/env python3
"""Structured PR review agent for Claude Code workflows."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@")
ADDED_RE = re.compile(r"^\+(?!\+\+)")
REMOVED_RE = re.compile(r"^-(?!--)")

RISK_PATTERNS = (
    ("High", re.compile(r"\b(api[_-]?key|secret|password|token)\b\s*[:=]", re.I), "Potential secret or credential handling appears in the diff."),
    ("Medium", re.compile(r"\b(eval|exec|subprocess|shell=True|innerHTML)\b", re.I), "Dynamic execution or unsafe rendering deserves careful review."),
    ("Medium", re.compile(r"\b(delete|drop table|truncate|rm -rf)\b", re.I), "Destructive operation patterns appear in changed lines."),
    ("Medium", re.compile(r"\b(auth|login|jwt|session|cookie|permission)\b", re.I), "Authentication or authorization code changed."),
    ("Low", re.compile(r"\b(todo|fixme|hack)\b", re.I), "Temporary marker found in changed lines."),
)

CODE_OR_CONFIG_SUFFIXES = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".sh",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
)


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    added_lines: list[str] = field(default_factory=list)


def github_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise ValueError("expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_diff(pr_url: str) -> str:
    url = github_diff_url(pr_url)
    request = urllib.request.Request(url, headers={"User-Agent": "claude-review/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to fetch PR diff: {exc}") from exc


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            path = file_match.group(1)
            if path != "/dev/null":
                current = FileChange(path=path)
                files.append(current)
            else:
                current = None
            continue

        if current is None:
            continue
        if HUNK_RE.match(line):
            current.hunks += 1
        elif ADDED_RE.match(line):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif REMOVED_RE.match(line):
            current.deletions += 1

    return files


def classify_change(files: list[FileChange]) -> str:
    paths = [file.path.lower() for file in files]
    if any(path.endswith((".md", ".rst", ".txt")) for path in paths) and len(files) <= 3:
        return "documentation or instruction update"
    if any("test" in path or path.endswith(("_test.py", ".spec.ts", ".test.ts")) for path in paths):
        return "implementation with test coverage"
    if any(path.endswith((".yml", ".yaml", ".json", ".toml")) for path in paths):
        return "configuration or workflow update"
    if any(path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")) for path in paths):
        return "implementation update"
    return "repository update"


def article_for(text: str) -> str:
    return "an" if text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def summarize(files: list[FileChange]) -> list[str]:
    additions = sum(file.additions for file in files)
    deletions = sum(file.deletions for file in files)
    file_count = len(files)
    change_type = classify_change(files)
    largest = sorted(files, key=lambda item: item.additions + item.deletions, reverse=True)[:3]
    largest_paths = ", ".join(file.path for file in largest) if largest else "no files"

    return [
        f"This PR changes {file_count} file(s) with {additions} additions and {deletions} deletions.",
        f"The diff looks like {article_for(change_type)} {change_type}; the largest touched path(s) are {largest_paths}.",
    ]


def find_risks(files: list[FileChange]) -> list[str]:
    risks: list[str] = []
    joined = "\n".join(
        line
        for file in files
        if file.path.lower().endswith(CODE_OR_CONFIG_SUFFIXES)
        for line in file.added_lines
    )

    if joined:
        for severity, pattern, message in RISK_PATTERNS:
            if pattern.search(joined):
                risks.append(f"[{severity}] {message}")

    if sum(file.additions + file.deletions for file in files) > 500:
        risks.append("[Medium] Large diff size increases review risk; consider splitting if possible.")
    if not any("test" in file.path.lower() for file in files):
        risks.append("[Low] No test file changed; verify that existing or manual validation covers the behavior.")

    return risks or ["No obvious high-risk patterns were detected from the diff text."]


def suggestions(files: list[FileChange]) -> list[str]:
    output = [
        "Confirm the PR description maps each change to an acceptance criterion or user-facing reason.",
        "Run the narrowest relevant test or validation command and include the result in the PR thread.",
    ]

    if not any("readme" in file.path.lower() or file.path.lower().endswith(".md") for file in files):
        output.append("Add or update usage documentation if the change introduces a new command or workflow.")
    if any(file.path.endswith((".py", ".js", ".ts", ".tsx")) for file in files):
        output.append("Check error handling around external input, network calls, and file paths.")

    return output


def confidence(files: list[FileChange], risks: list[str]) -> str:
    total = sum(file.additions + file.deletions for file in files)
    has_high = any(risk.startswith("[High]") for risk in risks)
    if has_high or total > 800:
        return "Low"
    if total > 300 or any(risk.startswith("[Medium]") for risk in risks):
        return "Medium"
    return "High"


def render_review(pr_url: str, files: list[FileChange]) -> str:
    risks = find_risks(files)
    lines = [
        "## Claude PR Review",
        "",
        f"PR: {pr_url}",
        "",
        "### Summary",
        *[f"- {item}" for item in summarize(files)],
        "",
        "### Identified Risks",
        *[f"- {item}" for item in risks],
        "",
        "### Improvement Suggestions",
        *[f"- {item}" for item in suggestions(files)],
        "",
        f"### Confidence: {confidence(files, risks)}",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Read a local diff file instead of fetching from GitHub.")
    parser.add_argument("--output", help="Write the Markdown review to this file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8") if args.diff_file else fetch_diff(args.pr)
        files = parse_diff(diff_text)
        if not files:
            raise ValueError("diff did not contain any changed files")
        review = render_review(args.pr, files)
        if args.output:
            Path(args.output).write_text(review, encoding="utf-8")
        else:
            print(review)
        return 0
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
