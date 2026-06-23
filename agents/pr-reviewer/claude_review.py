#!/usr/bin/env python3
"""Structured pull request review comment generator."""

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


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str

    @property
    def diff_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}.diff"

    @property
    def comments_api_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.number}/comments"


@dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    risk_signals: list[str]
    test_files: list[str]
    docs_files: list[str]


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number), url=f"https://github.com/{owner}/{repo}/pull/{number}")


def fetch_url(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "claude-review-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Failed to fetch {url}: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc.reason}") from exc


def parse_diff(diff: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0
    risk_signals: list[str] = []

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                files.append(path)
        elif line.startswith("@@"):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    test_files = [path for path in files if is_test_path(path)]
    docs_files = [path for path in files if is_doc_path(path)]

    joined = "\n".join(files).lower()
    body = diff.lower()
    signal_rules = [
        ("Authentication or authorization code changed", ["authentication", "authorization", "authorize", "/auth", "auth/", "jwt", "access token", "github_token", "bearer ", "permission", "session"]),
        ("Secrets or environment handling changed", [".env", "secret", "api_key", "apikey", "password"]),
        ("Database or migration code changed", ["migration", "schema", "sql", "prisma", "sqlite"]),
        ("CI or automation workflow changed", [".github/workflows", "workflow", "action.yml"]),
        ("Shell, hook, or command execution code changed", ["hook", "bash", "shell", "subprocess", "exec("]),
        ("Generated or binary assets changed", ["binary files", ".png", ".jpg", ".jpeg", ".svg"]),
        ("Public API or route behavior changed", ["route", "api/", "controller", "handler", "endpoint"]),
    ]
    for label, needles in signal_rules:
        if any(needle in joined or needle in body for needle in needles):
            risk_signals.append(label)

    if len(files) > 12:
        risk_signals.append("Large surface area touched")
    if additions + deletions > 800:
        risk_signals.append("Large patch size")
    if not test_files:
        risk_signals.append("No test files changed")

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        hunks=hunks,
        risk_signals=dedupe(risk_signals),
        test_files=test_files,
        docs_files=docs_files,
    )


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    if lowered.startswith("test/") or lowered.startswith("tests/"):
        return True
    return any(
        marker in lowered
        for marker in [
            "/test/",
            "/tests/",
            "__tests__",
            ".test.",
            ".spec.",
            "test_",
            "_test.",
        ]
    )


def is_doc_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith(".md") or "/docs/" in lowered or "readme" in lowered


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def summarize_areas(files: list[str]) -> str:
    if not files:
        return "no files"
    roots: dict[str, int] = {}
    for path in files:
        root = path.split("/", 1)[0]
        roots[root] = roots.get(root, 0) + 1
    parts = [f"{root} ({count})" for root, count in sorted(roots.items(), key=lambda item: (-item[1], item[0]))[:4]]
    return ", ".join(parts)


def build_risks(stats: DiffStats) -> list[str]:
    if not stats.risk_signals:
        return ["No obvious high-risk areas were detected from the diff alone."]

    risks: list[str] = []
    for signal in stats.risk_signals:
        if signal == "No test files changed":
            risks.append("No test files changed, so behavior depends on manual validation or existing coverage.")
        elif signal == "Generated or binary assets changed":
            risks.append("Generated or binary assets need visual or artifact-level review because text diff coverage is limited.")
        elif signal == "Large surface area touched":
            risks.append("The patch touches many files, which increases regression and review-scope risk.")
        elif signal == "Large patch size":
            risks.append("The patch is large enough that reviewers should sample key paths instead of relying only on summary text.")
        else:
            risks.append(f"{signal}; verify boundary cases and failure modes in that area.")
    return dedupe(risks)


def build_suggestions(stats: DiffStats) -> list[str]:
    suggestions = [
        "Run the repository's focused tests and include the exact command output in the PR thread.",
    ]

    if not stats.test_files:
        suggestions.append("Add or reference tests for the main behavior changed by this PR.")
    if stats.docs_files:
        suggestions.append("Confirm documentation examples match the final file paths and commands.")
    if any("Authentication" in signal for signal in stats.risk_signals):
        suggestions.append("Add negative-path checks for unauthorized, expired, or malformed credentials.")
    if any("Database" in signal for signal in stats.risk_signals):
        suggestions.append("Verify migration rollback or recovery notes and run the change on a fresh database.")
    if any("workflow" in signal.lower() for signal in stats.risk_signals):
        suggestions.append("Check workflow permissions and avoid granting broader token scopes than required.")
    if any("binary" in signal.lower() or "Generated" in signal for signal in stats.risk_signals):
        suggestions.append("Open the generated asset or rendered output directly before merge.")

    suggestions.append("Keep the final PR description aligned with the files actually changed.")
    return dedupe(suggestions)


def confidence(stats: DiffStats) -> str:
    score = 0
    if stats.test_files:
        score += 2
    if stats.additions + stats.deletions <= 300:
        score += 1
    if len(stats.files) <= 6:
        score += 1
    if any(signal in stats.risk_signals for signal in ["Authentication or authorization code changed", "Secrets or environment handling changed"]):
        score -= 2
    if "Large patch size" in stats.risk_signals or "Large surface area touched" in stats.risk_signals:
        score -= 1

    if score >= 3:
        return "High"
    if score >= 1:
        return "Medium"
    return "Low"


def render_review(pr: PullRequestRef | None, stats: DiffStats) -> str:
    pr_label = pr.url if pr else "local diff"
    changed_areas = summarize_areas(stats.files)
    file_count = len(stats.files)

    summary = (
        f"This PR changes {file_count} {plural('file', file_count)} across {changed_areas}, with {stats.additions} {plural('addition', stats.additions)} and {stats.deletions} {plural('deletion', stats.deletions)}. "
        f"The diff appears to focus on {primary_focus(stats.files)}, so the main review concern is whether the submitted behavior is validated at the right boundary."
    )

    risks = build_risks(stats)
    suggestions = build_suggestions(stats)
    conf = confidence(stats)

    lines = [
        "## Claude PR Review",
        "",
        "### Summary of Changes",
        "",
        summary,
        "",
        "### Identified Risks",
        "",
        *[f"- {risk}" for risk in risks],
        "",
        "### Improvement Suggestions",
        "",
        *[f"- {suggestion}" for suggestion in suggestions],
        "",
        "### Confidence Score",
        "",
        conf,
        "",
        "### Review Metadata",
        "",
        f"- Source: {pr_label}",
        f"- Files changed: {file_count}",
        f"- Hunks: {stats.hunks}",
    ]
    return "\n".join(lines) + "\n"


def plural(word: str, count: int) -> str:
    return word if count == 1 else f"{word}s"


def primary_focus(files: list[str]) -> str:
    if not files:
        return "an empty or unavailable patch"
    if all(is_doc_path(path) for path in files):
        return "documentation"
    if any(is_test_path(path) for path in files) and len(files) <= 4:
        return "a small code-and-test change"
    if any(path.endswith((".png", ".jpg", ".jpeg", ".svg")) for path in files):
        return "asset or visual output changes"
    if any(".github/workflows" in path for path in files):
        return "automation or CI changes"
    if any(path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")) for path in files):
        return "application or tooling code"
    return "repository files"


def post_comment(pr: PullRequestRef, body: str, token: str) -> str:
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        pr.comments_api_url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "claude-review-agent",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("html_url", pr.url)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Failed to post comment: HTTP {exc.code}: {detail}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review.")
    parser.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Read a local diff file instead of fetching from GitHub")
    parser.add_argument("--output", help="Write Markdown output to this file")
    parser.add_argument("--post", action="store_true", help="Post the review as a GitHub PR conversation comment")
    args = parser.parse_args(argv)

    if not args.pr and not args.diff_file:
        parser.error("provide --pr or --diff-file")
    if args.post and not args.pr:
        parser.error("--post requires --pr")

    pr = parse_pr_url(args.pr) if args.pr else None
    token = os.environ.get("GITHUB_TOKEN")

    if args.diff_file:
        diff = Path(args.diff_file).read_text(encoding="utf-8")
    else:
        assert pr is not None
        diff = fetch_url(pr.diff_url, token=token)

    stats = parse_diff(diff)
    review = render_review(pr, stats)

    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)

    if args.post:
        if not token:
            raise RuntimeError("--post requires GITHUB_TOKEN")
        assert pr is not None
        comment_url = post_comment(pr, review, token)
        print(f"Posted review: {comment_url}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
