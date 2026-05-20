#!/usr/bin/env python3
"""Deterministic PR review agent for Claude Code bounty #4.

The tool fetches or reads a GitHub PR diff and emits a structured Markdown
review comment. It is intentionally dependency-free so it can run inside a
fresh Claude Code workspace without package setup.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?$"
)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str

    @property
    def api_base(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    @property
    def diff_url(self) -> str:
        return f"{self.url}.diff"

    @property
    def comments_url(self) -> str:
        return f"{self.api_base}/issues/{self.number}/comments"


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0

    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower() or "[none]"

    @property
    def area(self) -> str:
        parts = Path(self.path).parts
        return parts[0] if len(parts) > 1 else "."

    @property
    def is_test(self) -> bool:
        lowered = self.path.lower()
        return any(token in lowered for token in ("test", "spec", "__tests__"))

    @property
    def is_doc(self) -> bool:
        lowered = self.path.lower()
        return lowered.endswith((".md", ".rst", ".txt")) or "/docs/" in lowered

    @property
    def is_config(self) -> bool:
        lowered = self.path.lower()
        names = (
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "cargo.toml",
            "go.mod",
            "dockerfile",
            ".github/workflows/",
        )
        return any(name in lowered for name in names)

    @property
    def is_sensitive(self) -> bool:
        lowered = self.path.lower()
        markers = (
            "auth",
            "login",
            "permission",
            "security",
            "payment",
            "billing",
            "stripe",
            "migration",
            "schema",
            "database",
            "secret",
            ".env",
        )
        return any(marker in lowered for marker in markers)


@dataclass
class Review:
    pr: PullRequestRef | None
    files: list[FileChange]
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str

    def to_markdown(self) -> str:
        pr_line = self.pr.url if self.pr else "local diff input"
        lines = [
            "## Claude PR Review",
            "",
            f"**PR:** {pr_line}",
            "",
            "### Summary of Changes",
        ]
        lines.extend(f"- {item}" for item in self.summary)
        lines.extend(["", "### Identified Risks"])
        lines.extend(f"- {item}" for item in self.risks)
        lines.extend(["", "### Improvement Suggestions"])
        lines.extend(f"- {item}" for item in self.suggestions)
        lines.extend(["", "### Confidence", self.confidence])
        return "\n".join(lines) + "\n"

    def to_json(self) -> str:
        payload = {
            "pr": self.pr.url if self.pr else None,
            "files": [
                {
                    "path": change.path,
                    "additions": change.additions,
                    "deletions": change.deletions,
                    "hunks": change.hunks,
                }
                for change in self.files
            ],
            "summary": self.summary,
            "risks": self.risks,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
        }
        return json.dumps(payload, indent=2)


def parse_pr_url(raw_url: str) -> PullRequestRef:
    match = PR_URL_RE.match(raw_url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))
    return PullRequestRef(owner=owner, repo=repo, number=number, url=raw_url.rstrip("/"))


def http_request(url: str, *, method: str = "GET", body: bytes | None = None, token: str | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github+json, text/plain",
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub request failed: {exc.reason}") from exc


def fetch_diff(pr: PullRequestRef) -> str:
    return http_request(pr.diff_url)


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            path = line.split(" b/", 1)[-1] if " b/" in line else line.rsplit(" ", 1)[-1]
            current = FileChange(path=path.strip())
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("+++ b/"):
            current.path = line[6:].strip()
        elif line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1

    return files


def summarize_areas(files: Iterable[FileChange]) -> str:
    counts: dict[str, int] = {}
    for change in files:
        counts[change.area] = counts.get(change.area, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{area} ({count})" for area, count in ranked[:5]) or "none"


def build_review(diff_text: str, pr: PullRequestRef | None = None) -> Review:
    files = parse_diff(diff_text)
    total_additions = sum(change.additions for change in files)
    total_deletions = sum(change.deletions for change in files)
    total_hunks = sum(change.hunks for change in files)
    test_files = [change for change in files if change.is_test]
    doc_files = [change for change in files if change.is_doc]
    config_files = [change for change in files if change.is_config]
    sensitive_files = [change for change in files if change.is_sensitive]

    summary = [
        (
            f"This PR changes {len(files)} file(s), with +{total_additions}/-{total_deletions} "
            f"across {total_hunks} diff hunk(s)."
        ),
        f"The largest touched areas are: {summarize_areas(files)}.",
    ]
    if test_files or doc_files:
        summary.append(
            f"It includes {len(test_files)} test-related file(s) and {len(doc_files)} documentation file(s)."
        )
    else:
        summary.append("No test or documentation files are visible in the diff.")

    risks: list[str] = []
    if not files:
        risks.append("The diff is empty or could not be parsed, so the review has low signal.")
    if not test_files:
        risks.append("No test file changed; behavior could regress without automated coverage.")
    if sensitive_files:
        paths = ", ".join(change.path for change in sensitive_files[:4])
        risks.append(f"Sensitive areas are touched ({paths}); verify permissions, data flow, and rollback safety.")
    if config_files:
        paths = ", ".join(change.path for change in config_files[:4])
        risks.append(f"Configuration or dependency files changed ({paths}); confirm install and CI behavior.")
    if total_additions + total_deletions > 600 or len(files) > 20:
        risks.append("The change is broad enough that local smoke testing and reviewer sampling are important.")
    if total_deletions > total_additions and total_deletions > 50:
        risks.append("The PR removes more code than it adds; check for deleted edge-case handling or docs.")
    if not risks:
        risks.append("No obvious high-risk pattern is visible from the diff shape alone.")

    suggestions: list[str] = []
    if not test_files:
        suggestions.append("Add or point reviewers to a focused regression test for the changed behavior.")
    if sensitive_files:
        suggestions.append("Document the security, migration, or payment path that was manually verified.")
    if config_files:
        suggestions.append("Include the exact build or install command used after the configuration change.")
    suggestions.append("Ask reviewers to focus on the files with the largest hunk counts first.")
    suggestions.append("Include screenshots or command output when the PR affects user-visible behavior.")

    score = 2
    if files and test_files:
        score += 1
    if len(files) <= 8 and total_additions + total_deletions <= 300:
        score += 1
    if sensitive_files or config_files:
        score -= 1
    if total_additions + total_deletions > 800 or len(files) > 25:
        score -= 1
    if not files:
        score = 0

    confidence = "High" if score >= 4 else "Medium" if score >= 2 else "Low"
    return Review(
        pr=pr,
        files=files,
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
    )


def post_comment(pr: PullRequestRef, markdown: str, token: str) -> str:
    body = json.dumps({"body": markdown}).encode("utf-8")
    response = http_request(pr.comments_url, method="POST", body=body, token=token)
    data = json.loads(response)
    return data.get("html_url", pr.url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and emit a structured Markdown comment.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL, e.g. https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Local diff file to review")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    parser.add_argument("--save", help="Write the generated output to this path")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the Markdown review as a GitHub PR comment using GITHUB_TOKEN",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pr: PullRequestRef | None = None
    if args.pr:
        pr = parse_pr_url(args.pr)
        diff_text = fetch_diff(pr)
    else:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")

    review = build_review(diff_text, pr)
    output = review.to_markdown() if args.format == "markdown" else review.to_json()

    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text(output, encoding="utf-8")

    if args.post_comment:
        if args.format != "markdown":
            raise SystemExit("--post-comment requires --format markdown")
        if pr is None:
            raise SystemExit("--post-comment requires --pr")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is required for --post-comment")
        url = post_comment(pr, output, token)
        print(f"Posted review comment: {url}", file=sys.stderr)

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
