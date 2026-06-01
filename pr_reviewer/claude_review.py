#!/usr/bin/env python3
"""Review a GitHub pull request diff and emit a structured Markdown comment."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


DOC_EXTENSIONS = {
    ".adoc",
    ".md",
    ".mdx",
    ".rst",
    ".txt",
}
DOC_BASENAMES = {
    "changelog",
    "license",
    "readme",
}
CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
}
TEST_MARKERS = ("test", "tests", "spec", "__tests__")
DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "poetry.lock",
    "pyproject.toml",
    "cargo.toml",
    "cargo.lock",
    "go.mod",
    "go.sum",
}
SECURITY_WORDS = (
    "auth",
    "admin",
    "permission",
    "policy",
    "secret",
    "token",
    "password",
    "payment",
    "stripe",
    "sql",
)
RISKY_ADDITION_PATTERNS = (
    "eval(",
    "exec(",
    "dangerouslysetinnerhtml",
    "innerhtml",
    "delete from",
    "drop table",
)


@dataclass
class FileChange:
    old_path: str = ""
    new_path: str = ""
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    binary: bool = False
    added_lines: list[str] = field(default_factory=list)

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or "unknown"

    @property
    def suffix(self) -> str:
        return Path(self.path).suffix.lower()

    @property
    def basename(self) -> str:
        return Path(self.path).name.lower()


@dataclass
class DiffStats:
    files: list[FileChange]

    @property
    def additions(self) -> int:
        return sum(file.additions for file in self.files)

    @property
    def deletions(self) -> int:
        return sum(file.deletions for file in self.files)

    @property
    def changed_lines(self) -> int:
        return self.additions + self.deletions


def clean_diff_path(raw_path: str) -> str:
    path = raw_path.strip()
    if path in {"/dev/null", "dev/null"}:
        return ""
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def parse_diff(diff_text: str) -> DiffStats:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            old_path = clean_diff_path(parts[2]) if len(parts) > 2 else ""
            new_path = clean_diff_path(parts[3]) if len(parts) > 3 else old_path
            current = FileChange(old_path=old_path, new_path=new_path)
            files.append(current)
            continue

        if current is None and (line.startswith("--- ") or line.startswith("+++ ")):
            current = FileChange()
            files.append(current)

        if current is None:
            continue

        if line.startswith("--- "):
            current.old_path = clean_diff_path(line[4:])
        elif line.startswith("+++ "):
            current.new_path = clean_diff_path(line[4:])
        elif line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("Binary files "):
            current.binary = True
        elif line.startswith("+") and not line.startswith("+++ "):
            current.additions += 1
            current.added_lines.append(line[1:].strip())
        elif line.startswith("-") and not line.startswith("--- "):
            current.deletions += 1

    return DiffStats(files=files)


def is_doc_file(file: FileChange) -> bool:
    path = file.path.lower()
    return (
        file.suffix in DOC_EXTENSIONS
        or file.basename in DOC_BASENAMES
        or "docs/" in path
        or path.startswith("docs/")
    )


def is_test_file(file: FileChange) -> bool:
    lowered = file.path.lower()
    return any(marker in lowered for marker in TEST_MARKERS)


def is_code_file(file: FileChange) -> bool:
    return file.suffix in CODE_EXTENSIONS and not is_test_file(file)


def is_config_or_dependency_file(file: FileChange) -> bool:
    path = file.path.lower()
    return (
        file.basename in DEPENDENCY_FILES
        or path.startswith(".github/workflows/")
        or path.endswith(".yml")
        or path.endswith(".yaml")
        or path.endswith(".toml")
        or path.endswith(".ini")
    )


def is_security_sensitive(file: FileChange) -> bool:
    lowered = file.path.lower()
    return any(word in lowered for word in SECURITY_WORDS)


def classify_diff(stats: DiffStats) -> str:
    if not stats.files:
        return "unparsed"
    if all(is_doc_file(file) for file in stats.files):
        return "documentation-only"
    if any(is_code_file(file) for file in stats.files):
        return "code"
    if any(is_config_or_dependency_file(file) for file in stats.files):
        return "configuration"
    return "mixed"


def list_changed_files(stats: DiffStats, limit: int = 4) -> str:
    if not stats.files:
        return "none"

    ranked = sorted(
        stats.files,
        key=lambda file: (file.additions + file.deletions, file.path),
        reverse=True,
    )
    names = [
        f"{file.path} (+{file.additions}/-{file.deletions})"
        for file in ranked[:limit]
    ]
    if len(ranked) > limit:
        names.append(f"{len(ranked) - limit} more")
    return ", ".join(names)


def summarize(stats: DiffStats, source: str | None) -> list[str]:
    kind = classify_diff(stats)
    source_note = f" for `{source}`" if source else ""
    return [
        (
            f"This PR{source_note} changes {len(stats.files)} file(s) with "
            f"{stats.additions} additions and {stats.deletions} deletions."
        ),
        (
            f"The diff appears to be {kind}; the largest changed paths are "
            f"{list_changed_files(stats)}."
        ),
    ]


def identify_risks(stats: DiffStats) -> list[str]:
    if not stats.files:
        return ["No files were parsed from the diff, so the review may be incomplete."]

    risks: list[str] = []
    has_code = any(is_code_file(file) for file in stats.files)
    has_tests = any(is_test_file(file) for file in stats.files)
    has_docs_only = all(is_doc_file(file) for file in stats.files)
    has_config = any(is_config_or_dependency_file(file) for file in stats.files)
    has_security = any(is_security_sensitive(file) for file in stats.files)
    has_binary = any(file.binary for file in stats.files)
    added_text = "\n".join(line.lower() for file in stats.files for line in file.added_lines)

    if has_docs_only:
        risks.append("Low functional risk because the diff only changes documentation or text files.")
    if has_code and not has_tests:
        risks.append("Application code changed without a matching test update in the diff.")
    if has_config:
        risks.append("Configuration, dependency, or workflow files changed, so CI behavior may shift.")
    if has_security:
        risks.append("Security-sensitive paths or names changed and need authorization-focused review.")
    if has_binary:
        risks.append("Binary file changes cannot be meaningfully reviewed from a text diff.")
    if stats.changed_lines > 500:
        risks.append("The diff is large enough that hidden coupling or missed edge cases are more likely.")
    if stats.deletions > max(20, stats.additions * 2):
        risks.append("The PR removes substantially more code than it adds; check for behavior loss.")
    if any(pattern in added_text for pattern in RISKY_ADDITION_PATTERNS):
        risks.append("Added code contains patterns that deserve manual security review.")

    if not risks:
        risks.append("No obvious structural risks were detected from the diff alone.")
    return risks


def suggest_improvements(stats: DiffStats) -> list[str]:
    has_code = any(is_code_file(file) for file in stats.files)
    has_tests = any(is_test_file(file) for file in stats.files)
    has_docs_only = bool(stats.files) and all(is_doc_file(file) for file in stats.files)
    has_config = any(is_config_or_dependency_file(file) for file in stats.files)
    has_security = any(is_security_sensitive(file) for file in stats.files)

    suggestions: list[str] = []
    if has_code and not has_tests:
        suggestions.append("Add or update targeted tests for the changed behavior before merging.")
    if has_code:
        suggestions.append("Run the smallest relevant unit or integration test command for the touched area.")
    if has_docs_only:
        suggestions.append("Preview the rendered documentation and verify headings, links, and examples.")
    if has_config:
        suggestions.append("Run CI or a dry-run for the changed workflow/configuration path.")
    if has_security:
        suggestions.append("Add a regression check for denied access and invalid input cases.")

    suggestions.append("Have a maintainer compare this generated review with project-specific context.")
    return suggestions


def confidence(stats: DiffStats) -> str:
    kind = classify_diff(stats)
    if not stats.files or any(file.binary for file in stats.files):
        return "Low"
    if stats.changed_lines > 500:
        return "Low"
    if kind == "documentation-only" and stats.changed_lines <= 100:
        return "High"
    return "Medium"


def render_markdown(stats: DiffStats, source: str | None = None) -> str:
    summary = summarize(stats, source)
    risks = identify_risks(stats)
    suggestions = suggest_improvements(stats)
    score = confidence(stats)

    lines = ["## PR Review", "", "### Summary"]
    lines.extend(f"- {sentence}" for sentence in summary)
    lines.extend(["", "### Identified Risks"])
    lines.extend(f"- {risk}" for risk in risks)
    lines.extend(["", "### Improvement Suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in suggestions)
    lines.extend(["", "### Confidence", score, ""])
    return "\n".join(lines)


def build_diff_url(pr_url: str) -> str:
    parsed = urllib.parse.urlparse(pr_url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com pull request URLs are supported.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 4 or parts[2] != "pull" or not parts[3].isdigit():
        raise ValueError("Expected a URL like https://github.com/owner/repo/pull/123.")

    owner, repo, _, number = parts
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_pr_diff(pr_url: str, timeout: int = 20) -> str:
    diff_url = build_diff_url(pr_url)
    request = urllib.request.Request(
        diff_url,
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review-agent",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_github_pr_url(pr_url: str) -> tuple[str, str, int]:
    parsed = urllib.parse.urlparse(pr_url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com pull request URLs are supported.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 4 or parts[2] != "pull" or not parts[3].isdigit():
        raise ValueError("Expected a URL like https://github.com/owner/repo/pull/123.")

    owner, repo, _, number = parts
    return owner, repo, int(number)


def post_pr_comment(pr_url: str, body: str, token: str, timeout: int = 20) -> str:
    owner, repo, number = parse_github_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "claude-review-agent",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    return str(data.get("html_url", ""))


def load_diff(args: argparse.Namespace) -> tuple[str, str | None]:
    if args.diff_file:
        path = Path(args.diff_file)
        return path.read_text(encoding="utf-8"), path.as_posix()
    return fetch_pr_diff(args.pr), args.pr


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub PR diff and print a structured Markdown comment.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL to fetch and review.")
    source.add_argument("--diff-file", help="Local unified diff file to review.")
    parser.add_argument("--output", help="Write Markdown review output to this file.")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the generated Markdown review as a GitHub PR comment. Requires --pr.",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for --post-comment. Defaults to GITHUB_TOKEN.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.post_comment and not args.pr:
        parser.error("--post-comment requires --pr.")
    if args.post_comment and not args.github_token:
        parser.error("--post-comment requires --github-token or GITHUB_TOKEN.")

    try:
        diff_text, source = load_diff(args)
        review = render_markdown(parse_diff(diff_text), source)
        comment_url = (
            post_pr_comment(args.pr, review, args.github_token)
            if args.post_comment
            else None
        )
    except (OSError, TimeoutError, ValueError) as exc:
        parser.error(str(exc))
        return 2

    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)
    if comment_url:
        sys.stdout.write(f"\nPosted review comment: {comment_url}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
