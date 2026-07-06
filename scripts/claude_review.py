#!/usr/bin/env python3
"""Review a GitHub pull request and print a structured Markdown comment."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISKY_PATH_PATTERNS = (
    ".github/workflows/",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "dockerfile",
    "docker-compose",
    ".env",
    "auth",
    "security",
    "migration",
    "migrations/",
    "schema",
    "infra",
    "terraform",
)
TEST_PATH_PATTERNS = (
    "test",
    "tests/",
    "__tests__",
    ".spec.",
    ".test.",
)
LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".sql": "SQL",
}


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


@dataclass(frozen=True)
class ChangedFile:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str = ""

    @property
    def churn(self) -> int:
        return self.additions + self.deletions


@dataclass(frozen=True)
class ReviewData:
    title: str
    author: str
    url: str
    files: list[ChangedFile]

    @property
    def additions(self) -> int:
        return sum(file.additions for file in self.files)

    @property
    def deletions(self) -> int:
        return sum(file.deletions for file in self.files)

    @property
    def churn(self) -> int:
        return self.additions + self.deletions


def parse_pr_url(url: str) -> PullRequestRef:
    match = re.match(
        r"^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)(?:[/?#].*)?$",
        url.strip(),
    )
    if not match:
        raise ValueError("expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    return PullRequestRef(match.group(1), match.group(2), int(match.group(3)))


def request_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed ({exc.code}): {detail}") from exc


def fetch_review_data(pr_url: str) -> ReviewData:
    ref = parse_pr_url(pr_url)
    base = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    pr = request_json(base)
    files: list[ChangedFile] = []
    page = 1
    while True:
        batch = request_json(f"{base}/files?per_page=100&page={page}")
        if not batch:
            break
        for item in batch:
            files.append(
                ChangedFile(
                    filename=item["filename"],
                    status=item.get("status", "modified"),
                    additions=int(item.get("additions", 0)),
                    deletions=int(item.get("deletions", 0)),
                    patch=item.get("patch", ""),
                )
            )
        if len(batch) < 100:
            break
        page += 1

    return ReviewData(
        title=pr.get("title") or f"PR #{ref.number}",
        author=(pr.get("user") or {}).get("login", "unknown"),
        url=pr.get("html_url") or pr_url,
        files=files,
    )


def load_fixture(path: Path) -> ReviewData:
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = [ChangedFile(**item) for item in payload["files"]]
    return ReviewData(
        title=payload["title"],
        author=payload.get("author", "fixture"),
        url=payload.get("url", "fixture"),
        files=files,
    )


def area_for_file(filename: str) -> str:
    lower = filename.lower()
    if lower.startswith(".github/workflows/"):
        return "CI workflow"
    if "test" in lower:
        return "test"
    if lower.startswith("docs/") or lower.endswith(".md"):
        return "documentation"
    suffix = Path(filename).suffix.lower()
    return LANGUAGE_BY_EXTENSION.get(suffix, "source")


def most_common_areas(files: list[ChangedFile]) -> list[str]:
    counts: dict[str, int] = {}
    for file in files:
        area = area_for_file(file.filename)
        counts[area] = counts.get(area, 0) + file.churn
    return [
        area
        for area, _count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:3]
    ]


def has_tests(files: list[ChangedFile]) -> bool:
    return any(any(pattern in file.filename.lower() for pattern in TEST_PATH_PATTERNS) for file in files)


def risky_files(files: list[ChangedFile]) -> list[ChangedFile]:
    risky: list[ChangedFile] = []
    for file in files:
        lower = file.filename.lower()
        if any(pattern in lower for pattern in RISKY_PATH_PATTERNS):
            risky.append(file)
    return risky


def confidence(data: ReviewData, risks: list[str]) -> str:
    if data.churn > 1200 or len(data.files) > 25:
        return "Low"
    if len(risks) >= 4:
        return "Low"
    if data.churn <= 250 and len(data.files) <= 8 and (has_tests(data.files) or not risks):
        return "High"
    return "Medium"


def build_risks(data: ReviewData) -> list[str]:
    risks: list[str] = []
    if not data.files:
        return ["No changed files were returned by the GitHub API, so the review cannot validate behavior."]

    if data.churn > 800:
        risks.append(f"Large change size: {data.churn} total added/deleted lines across {len(data.files)} files.")
    elif len(data.files) > 15:
        risks.append(f"Wide change surface: {len(data.files)} files are modified.")

    if not has_tests(data.files):
        risks.append("No obvious test files changed, so behavior coverage may be missing.")

    risky = risky_files(data.files)
    if risky:
        examples = ", ".join(file.filename for file in risky[:4])
        risks.append(f"Sensitive paths changed: {examples}.")

    deleted_files = [file.filename for file in data.files if file.status == "removed"]
    if deleted_files:
        risks.append(f"Removed files may need migration or release-note coverage: {', '.join(deleted_files[:4])}.")

    if not risks:
        risks.append("No major structural risks detected from the changed-file metadata.")
    return risks


def build_suggestions(data: ReviewData, risks: list[str]) -> list[str]:
    suggestions: list[str] = []
    if not has_tests(data.files):
        suggestions.append("Add or reference a focused test plan that covers the changed behavior.")
    if risky_files(data.files):
        suggestions.append("Have a maintainer double-check sensitive configuration, dependency, auth, or migration changes.")
    if data.churn > 800 or len(data.files) > 15:
        suggestions.append("Consider splitting unrelated changes or calling out the review order in the PR description.")
    if any(file.filename.lower().endswith(".md") for file in data.files):
        suggestions.append("Verify documentation examples and commands against the final file paths.")
    if not suggestions:
        suggestions.append("Run the relevant project test suite and include the command output in the PR thread.")
    suggestions.append("Confirm the PR description lists user-visible behavior changes and any rollback concerns.")
    return suggestions


def sentence_list(items: list[str]) -> str:
    if not items:
        return "unknown areas"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def render_review(data: ReviewData) -> str:
    areas = most_common_areas(data.files)
    risks = build_risks(data)
    suggestions = build_suggestions(data, risks)
    score = confidence(data, risks)
    summary = [
        (
            f"This PR changes {len(data.files)} file(s) with +{data.additions}/-{data.deletions}, "
            f"mainly in {sentence_list(areas)}."
        ),
        (
            f"The review focus should be the highest-risk items below, especially tests and sensitive paths "
            f"when they appear in the diff."
        ),
        f"Confidence is {score} based on change size, touched areas, and visible test coverage.",
    ]

    lines = [
        f"# PR Review: {data.title}",
        "",
        f"- PR: {data.url}",
        f"- Author: @{data.author}",
        "",
        "## Summary of Changes",
        "",
        *[f"{index}. {sentence}" for index, sentence in enumerate(summary, start=1)],
        "",
        "## Identified Risks",
        "",
        *[f"- {risk}" for risk in risks],
        "",
        "## Improvement Suggestions",
        "",
        *[f"- {suggestion}" for suggestion in suggestions],
        "",
        "## Confidence Score",
        "",
        score,
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", help="GitHub PR URL to review.")
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Local JSON fixture for tests or offline sample generation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.pr and not args.fixture:
        print("error: provide --pr or --fixture", file=sys.stderr)
        return 2
    try:
        data = load_fixture(args.fixture) if args.fixture else fetch_review_data(args.pr)
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(render_review(data), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
