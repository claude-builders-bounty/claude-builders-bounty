#!/usr/bin/env python3
"""生成结构化 PR review 的轻量 Claude Code 风格 CLI。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable


GITHUB_PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str


@dataclass
class PullRequestMetadata:
    title: str
    author: str
    base: str
    head: str
    additions: int
    deletions: int
    changed_files: int


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)

    @property
    def extension(self) -> str:
        if "." not in self.path:
            return ""
        return self.path.rsplit(".", 1)[-1].lower()

    @property
    def is_test(self) -> bool:
        lowered = self.path.lower()
        return any(
            marker in lowered
            for marker in (
                "test",
                "spec",
                "__tests__",
                "fixtures",
                "snapshot",
            )
        )

    @property
    def is_documentation(self) -> bool:
        lowered = self.path.lower()
        return lowered.endswith((".md", ".rst", ".txt", ".adoc")) or "/docs/" in lowered

    @property
    def is_config(self) -> bool:
        lowered = self.path.lower()
        return lowered.endswith(
            (
                ".yml",
                ".yaml",
                ".toml",
                ".json",
                ".ini",
                ".env",
                ".properties",
            )
        ) or lowered in {"dockerfile", "makefile"}


@dataclass
class ReviewResult:
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> PullRequestRef:
    match = GITHUB_PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number), url=url.strip())


def request_text(url: str, *, accept: str = "application/vnd.github+json") -> str:
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub request failed: {exc.reason}") from exc


def fetch_metadata(pr: PullRequestRef) -> PullRequestMetadata:
    api_url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}"
    payload = json.loads(request_text(api_url))
    return PullRequestMetadata(
        title=payload.get("title", "(untitled)"),
        author=payload.get("user", {}).get("login", "unknown"),
        base=payload.get("base", {}).get("ref", "unknown"),
        head=payload.get("head", {}).get("ref", "unknown"),
        additions=int(payload.get("additions") or 0),
        deletions=int(payload.get("deletions") or 0),
        changed_files=int(payload.get("changed_files") or 0),
    )


def fetch_diff(pr: PullRequestRef) -> str:
    diff_url = f"https://patch-diff.githubusercontent.com/raw/{pr.owner}/{pr.repo}/pull/{pr.number}.diff"
    return request_text(diff_url, accept="application/vnd.github.diff")


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None
    new_path: str | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current is not None:
                files.append(current)
            current = None
            new_path = None
            continue

        if line.startswith("+++ "):
            raw_path = line[4:].strip()
            if raw_path == "/dev/null":
                new_path = "/dev/null"
            else:
                new_path = raw_path[2:] if raw_path.startswith("b/") else raw_path
            current = FileChange(path=new_path)
            continue

        if current is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            current.deleted_lines.append(line[1:])

    if current is not None:
        files.append(current)

    return [file for file in files if file.path != "/dev/null"]


def language_summary(files: Iterable[FileChange]) -> str:
    counts: dict[str, int] = {}
    for file in files:
        key = file.extension or "other"
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return "no files"
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:4]
    return ", ".join(f"{ext} ({count})" for ext, count in top)


def changed_area_summary(files: list[FileChange]) -> str:
    if not files:
        return "No changed files were detected in the PR diff."
    docs = sum(1 for file in files if file.is_documentation)
    tests = sum(1 for file in files if file.is_test)
    configs = sum(1 for file in files if file.is_config)
    code = len(files) - docs - tests
    parts = []
    if code > 0:
        parts.append(f"{code} code file{'s' if code != 1 else ''}")
    if tests > 0:
        parts.append(f"{tests} test file{'s' if tests != 1 else ''}")
    if docs > 0:
        parts.append(f"{docs} documentation file{'s' if docs != 1 else ''}")
    if configs > 0:
        parts.append(f"{configs} config file{'s' if configs != 1 else ''}")
    return ", ".join(parts) if parts else f"{len(files)} file{'s' if len(files) != 1 else ''}"


def contains_any(lines: Iterable[str], patterns: Iterable[str]) -> bool:
    joined = "\n".join(lines)
    return any(re.search(pattern, joined, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def build_risks(files: list[FileChange], metadata: PullRequestMetadata) -> list[str]:
    risks: list[str] = []
    total_changes = metadata.additions + metadata.deletions
    code_files = [file for file in files if not file.is_documentation and not file.is_test]
    test_files = [file for file in files if file.is_test]

    if total_changes > 500 or metadata.changed_files > 15:
        risks.append(
            f"Large review surface: {metadata.changed_files} files and {total_changes} changed lines increase the chance of missed regressions."
        )

    if code_files and not test_files:
        risks.append(
            "No test files were changed alongside code changes, so regression coverage may be missing."
        )

    sensitive_paths = [
        file.path
        for file in files
        if re.search(r"(auth|login|token|secret|payment|billing|permission|security)", file.path, re.IGNORECASE)
    ]
    if sensitive_paths:
        risks.append(
            "Sensitive area touched: "
            + ", ".join(sensitive_paths[:5])
            + ". Authentication, authorization, payment, or secret-handling changes need focused review."
        )

    dependency_files = [
        file.path
        for file in files
        if re.search(r"(package-lock|yarn.lock|pnpm-lock|poetry.lock|requirements|go.sum|cargo.lock|composer.lock)", file.path, re.IGNORECASE)
    ]
    if dependency_files:
        risks.append(
            "Dependency or lockfile changes detected: "
            + ", ".join(dependency_files[:5])
            + ". Verify transitive updates and supply-chain impact."
        )

    migration_files = [
        file.path
        for file in files
        if re.search(r"(migration|schema|database|db/|prisma|alembic)", file.path, re.IGNORECASE)
    ]
    if migration_files:
        risks.append(
            "Database or schema-related files changed: "
            + ", ".join(migration_files[:5])
            + ". Confirm forward/backward migration safety."
        )

    dangerous_patterns = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"shell\s*=\s*True",
        r"pickle\.loads?\s*\(",
        r"yaml\.load\s*\(",
        r"dangerouslySetInnerHTML",
        r"\binnerHTML\s*=",
        r"\brm\s+-rf\b",
        r"\bchmod\s+777\b",
        r"\bDROP\s+TABLE\b",
        r"\bTRUNCATE\b",
    ]
    flagged_files = [
        file.path
        for file in files
        if not file.is_documentation and not file.is_test and contains_any(file.added_lines, dangerous_patterns)
    ]
    if flagged_files:
        risks.append(
            "Potentially dangerous added code patterns found in "
            + ", ".join(flagged_files[:5])
            + ". Manually inspect command execution, SQL, and DOM injection surfaces."
        )

    env_files = [file.path for file in files if re.search(r"(^|/)\.env|secret|credential|private[_-]?key", file.path, re.IGNORECASE)]
    if env_files:
        risks.append(
            "Environment or secret-like files changed: "
            + ", ".join(env_files[:5])
            + ". Ensure no credentials or private keys are committed."
        )

    if not risks:
        risks.append(
            "No high-risk patterns were detected from the diff alone; this does not replace domain-specific review."
        )

    return risks


def build_suggestions(files: list[FileChange], risks: list[str], metadata: PullRequestMetadata) -> list[str]:
    suggestions: list[str] = []
    has_tests = any(file.is_test for file in files)
    has_code = any(not file.is_test and not file.is_documentation for file in files)

    if has_code and not has_tests:
        suggestions.append("Add or reference automated tests that cover the changed behavior before merging.")

    if any("Large review surface" in risk for risk in risks):
        suggestions.append("Split the change or add a reviewer checklist focused on the riskiest files.")

    if any("Dependency or lockfile" in risk for risk in risks):
        suggestions.append("Run dependency audit tooling and document why each dependency update is required.")

    if any("Database or schema" in risk for risk in risks):
        suggestions.append("Document migration rollback behavior and verify it against a copy of production-like data.")

    if any("dangerous added code" in risk for risk in risks):
        suggestions.append("Replace dangerous primitives with safer APIs or add validation around all untrusted inputs.")

    if not suggestions:
        suggestions.append("Verify the PR locally and include the command output in the merge discussion.")

    suggestions.append("Ask the author to confirm the intended user-visible behavior and any deployment steps.")
    return suggestions


def confidence_score(files: list[FileChange], risks: list[str], metadata: PullRequestMetadata) -> str:
    total_changes = metadata.additions + metadata.deletions
    if not files:
        return "Low"
    if total_changes > 800 or metadata.changed_files > 25:
        return "Low"
    if any("Large review surface" in risk or "dangerous added code" in risk for risk in risks):
        return "Medium"
    return "High"


def analyze(pr: PullRequestRef, metadata: PullRequestMetadata, files: list[FileChange]) -> ReviewResult:
    area = changed_area_summary(files)
    languages = language_summary(files)
    summary = (
        f"This PR changes {area}, with the largest file groups being {languages}. "
        f"It contains {metadata.additions} additions and {metadata.deletions} deletions across {metadata.changed_files} files. "
        f"The branch `{metadata.head}` targets `{metadata.base}`, so reviewers should focus on whether the changed areas match the PR intent."
    )
    risks = build_risks(files, metadata)
    suggestions = build_suggestions(files, risks, metadata)
    confidence = confidence_score(files, risks, metadata)
    return ReviewResult(summary=summary, risks=risks, suggestions=suggestions, confidence=confidence)


def render_markdown(pr: PullRequestRef, metadata: PullRequestMetadata, result: ReviewResult) -> str:
    risks = "\n".join(f"- {risk}" for risk in result.risks)
    suggestions = "\n".join(f"- {suggestion}" for suggestion in result.suggestions)
    return (
        "# Claude Review\n\n"
        f"**PR:** [{metadata.title}]({pr.url})  \n"
        f"**Author:** `{metadata.author}`  \n"
        f"**Base -> Head:** `{metadata.base}` -> `{metadata.head}`\n\n"
        "## Summary\n"
        f"{result.summary}\n\n"
        "## Identified Risks\n"
        f"{risks}\n\n"
        "## Improvement Suggestions\n"
        f"{suggestions}\n\n"
        "## Confidence Score\n"
        f"{result.confidence}\n"
    )


def run(pr_url: str) -> str:
    pr = parse_pr_url(pr_url)
    metadata = fetch_metadata(pr)
    files = parse_diff(fetch_diff(pr))
    result = analyze(pr, metadata, files)
    return render_markdown(pr, metadata, result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Analyze a GitHub pull request diff and print a structured Markdown review.",
    )
    parser.add_argument("--pr", required=True, help="GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    args = parser.parse_args(argv)

    try:
        print(run(args.pr), end="")
    except Exception as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
