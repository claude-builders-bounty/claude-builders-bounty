#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")
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
    ".swift",
    ".ts",
    ".tsx",
}
TEST_MARKERS = ("test", "spec", "__tests__", "tests/")
SECURITY_MARKERS = ("auth", "token", "password", "secret", "permission", "role", "jwt", "oauth")
DATABASE_PATH_MARKERS = ("migration", "migrations/", ".sql", "database", "db/schema")
CONFIG_MARKERS = (".env", "config", "settings", "workflow", ".yml", ".yaml", ".toml", ".ini")


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: str
    title: str
    author: str
    url: str
    additions: int
    deletions: int
    changed_files: int
    diff: str


@dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    file_types: Counter[str]
    code_files: list[str]
    test_files: list[str]
    dependency_files: list[str]
    config_files: list[str]


def _github_headers(accept: str) -> dict[str, str]:
    headers = {"Accept": accept, "User-Agent": "claude-pr-review-agent"}
    return headers


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=_github_headers("application/vnd.github+json"))
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str, accept: str) -> str:
    request = urllib.request.Request(url, headers=_github_headers(accept))
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    match = PR_URL_RE.fullmatch(pr_url.rstrip("/"))
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def load_pull_request(pr_url: str) -> PullRequest:
    owner, repo, number = _parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    metadata = _fetch_json(api_url)
    diff = _fetch_text(pr_url + ".diff", "application/vnd.github.v3.diff")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=metadata.get("title") or f"PR #{number}",
        author=(metadata.get("user") or {}).get("login") or "unknown",
        url=pr_url,
        additions=int(metadata.get("additions") or 0),
        deletions=int(metadata.get("deletions") or 0),
        changed_files=int(metadata.get("changed_files") or 0),
        diff=diff,
    )


def load_diff_file(path: Path) -> PullRequest:
    diff = path.read_text(encoding="utf-8")
    return PullRequest(
        owner="local",
        repo=path.stem,
        number="0",
        title=f"Local diff: {path.name}",
        author="local",
        url=str(path),
        additions=sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")),
        deletions=sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")),
        changed_files=len(re.findall(r"^diff --git ", diff, flags=re.MULTILINE)),
        diff=diff,
    )


def analyze_diff(diff: str) -> DiffStats:
    files: list[str] = []
    additions = deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.append(line.removeprefix("+++ b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    file_types = Counter(Path(file).suffix or "[no extension]" for file in files)
    lowered = [(file, file.lower()) for file in files]
    code_files = [file for file in files if Path(file).suffix in CODE_EXTENSIONS]
    test_files = [file for file, lower in lowered if any(marker in lower for marker in TEST_MARKERS)]
    dependency_files = [
        file
        for file, lower in lowered
        if Path(lower).name in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "requirements.txt", "go.sum", "cargo.lock"}
    ]
    config_files = [file for file, lower in lowered if any(marker in lower for marker in CONFIG_MARKERS)]
    return DiffStats(files, additions, deletions, file_types, code_files, test_files, dependency_files, config_files)


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _format_file_list(files: list[str], limit: int = 5) -> str:
    if not files:
        return "none"
    visible = files[:limit]
    suffix = "" if len(files) <= limit else f", and {len(files) - limit} more"
    return ", ".join(f"`{file}`" for file in visible) + suffix


def build_review(pr: PullRequest) -> str:
    stats = analyze_diff(pr.diff)
    diff_lower = pr.diff.lower()

    risks: list[str] = []
    suggestions: list[str] = []

    if stats.code_files and not stats.test_files:
        risks.append("No test files were changed alongside code changes, so behavior may be under-verified.")
        suggestions.append("Add or update focused tests for the changed code paths before merge.")
    if stats.dependency_files:
        risks.append(f"Dependency or lock files changed: {_format_file_list(stats.dependency_files)}.")
        suggestions.append("Confirm dependency updates are intentional and run the relevant install/build checks.")
    if _contains_any(pr.diff, SECURITY_MARKERS):
        risks.append("The diff touches security-sensitive terms such as auth, tokens, secrets, permissions, or roles.")
        suggestions.append("Review the changed security flow manually and verify no credentials or broad permissions were introduced.")
    has_database_path = any(any(marker in file.lower() for marker in DATABASE_PATH_MARKERS) for file in stats.files)
    has_sql_statement = re.search(
        r"\b(drop\s+table|delete\s+from|truncate|alter\s+table|create\s+table)\b",
        pr.diff,
        flags=re.IGNORECASE,
    )
    if has_database_path or has_sql_statement:
        risks.append("Database or schema-related changes appear in the diff.")
        suggestions.append("Validate migrations or SQL changes against a realistic dataset and include rollback expectations if applicable.")
    if stats.config_files:
        risks.append(f"Configuration or workflow files changed: {_format_file_list(stats.config_files)}.")
        suggestions.append("Run the affected CI, deployment, or local configuration path end to end.")
    if "todo" in diff_lower or "fixme" in diff_lower:
        risks.append("New TODO/FIXME markers appear in the patch.")
        suggestions.append("Resolve new TODO/FIXME markers or link them to tracked follow-up issues.")
    if stats.additions + stats.deletions > 800:
        risks.append("This is a large patch, which increases review and regression risk.")
        suggestions.append("Consider splitting the PR or adding a concise reviewer guide for the highest-risk files.")

    if not risks:
        risks.append("No obvious structural risks were detected from the diff metadata and changed paths.")
    if not suggestions:
        suggestions.append("Run the repository's normal test and lint commands, then review the changed files for product-specific edge cases.")

    confidence = "High"
    if stats.additions + stats.deletions > 800 or len(risks) >= 5:
        confidence = "Low"
    elif len(risks) >= 2 or len(stats.files) > 20:
        confidence = "Medium"
    elif stats.code_files and not stats.test_files:
        confidence = "Medium"

    top_types = ", ".join(f"{ext} ({count})" for ext, count in stats.file_types.most_common(4)) or "no file extensions detected"
    summary = (
        f"PR [{pr.owner}/{pr.repo}#{pr.number}]({pr.url}) by `{pr.author}` is titled \"{pr.title}\". "
        f"It changes {pr.changed_files or len(stats.files)} file(s) with {pr.additions or stats.additions} additions "
        f"and {pr.deletions or stats.deletions} deletions; the most common file types are {top_types}. "
        f"Primary changed files include {_format_file_list(stats.files)}."
    )

    risk_lines = "\n".join(f"- {risk}" for risk in risks)
    suggestion_lines = "\n".join(f"- {suggestion}" for suggestion in suggestions)
    return textwrap.dedent(
        f"""\
        ## Claude PR Review

        ### Summary of Changes
        {summary}

        ### Identified Risks
        {risk_lines}

        ### Improvement Suggestions
        {suggestion_lines}

        ### Confidence Score
        {confidence}
        """
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", type=Path, help="Local unified diff file to review")
    parser.add_argument("--output", type=Path, help="Write Markdown review to this file instead of stdout")
    args = parser.parse_args(argv)

    try:
        pr = load_pull_request(args.pr) if args.pr else load_diff_file(args.diff_file)
        review = build_review(pr)
    except (ValueError, urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(review, encoding="utf-8")
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
