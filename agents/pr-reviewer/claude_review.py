#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request diff."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
RISK_PATTERNS = [
    ("Shell execution", re.compile(r"\b(subprocess\.[^(]+\(.*shell\s*=\s*True|os\.system\(|exec\(|eval\()")),
    (
        "Destructive command",
        re.compile(
            r"\brm\b"
            r"(?=[^;&|#\n]*(?:-[A-Za-z]*r[A-Za-z]*|--recursive\b))"
            r"(?=[^;&|#\n]*(?:-[A-Za-z]*f[A-Za-z]*|--force\b))"
        ),
    ),
    ("Private key material", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Credential handling", re.compile(r"\b(secret|token|password|api[_-]?key)\b", re.I)),
    ("DOM injection", re.compile(r"\b(?:innerHTML|outerHTML)\s*=|dangerouslySetInnerHTML")),
    ("Plain HTTP URL", re.compile(r"(?<![A-Za-z0-9+.-])http://(?!localhost\b|127\.0\.0\.1\b|\[::1\])", re.I)),
    ("Silent exception handler", re.compile(r"\b(?:except\s+[^:\n]*:\s*pass|catch\s*\([^)]*\)\s*\{\s*\})")),
    ("Debug output", re.compile(r"\b(?:console\.(?:log|debug)|debugger;)\b")),
    ("Permissive CORS", re.compile(r"Access-Control-Allow-Origin['\"]?\s*[:=]\s*['\"]\*")),
    ("Database mutation", re.compile(r"\b(delete\s+from|update\s+\w+\s+set)\b(?![^;\n]*\bwhere\b)", re.I)),
    (
        "Privileged workflow trigger",
        re.compile(r"^\s*pull_request_target\s*:", re.I),
    ),
    (
        "Broad workflow permission",
        re.compile(
            r"^\s*(?:permissions\s*:\s*write-all|"
            r"(?:contents|actions|checks|deployments|id-token|packages|pull-requests)\s*:\s*write)\s*$",
            re.I,
        ),
    ),
]
MAX_DIFF_CHARS = 120_000


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    risky_lines: list[str] = field(default_factory=list)


@dataclass
class ReviewAnalysis:
    files: list[FileChange]
    total_additions: int
    total_deletions: int
    risks: list[str]
    suggestions: list[str]
    confidence: str
    truncated: bool = False
    original_chars: int = 0
    analyzed_chars: int = 0


def pr_to_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise ValueError("expected a GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def pr_to_api_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise ValueError("expected a GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"


def pr_to_issue_comments_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise ValueError("expected a GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"


def github_token(required: bool = False) -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip() or os.environ.get("GH_TOKEN", "").strip()
    if required and not token:
        raise RuntimeError("--post-comment requires GITHUB_TOKEN or GH_TOKEN")
    return token


def build_diff_request(pr_url: str) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent",
    }
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(pr_to_api_diff_url(pr_url), headers=headers)


def fetch_pr_diff(pr_url: str) -> str:
    request = build_diff_request(pr_url)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching PR diff") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not fetch PR diff: {exc.reason}") from exc


def post_pr_comment(pr_url: str, body: str) -> None:
    data = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(pr_to_issue_comments_url(pr_url), data=data, method="POST")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Authorization", f"Bearer {github_token(required=True)}")
    request.add_header("Content-Type", "application/json")
    request.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while posting PR comment") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not post PR comment: {exc.reason}") from exc


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"diff --git a/(.*?) b/(.*)", line)
            path = match.group(2) if match else line.rsplit(" ", 1)[-1].removeprefix("b/")
            current = FileChange(path=path)
            files.append(current)
            continue

        if current is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            added = line[1:]
            for label, pattern in RISK_PATTERNS:
                if pattern.search(added):
                    current.risky_lines.append(f"{label}: `{added.strip()[:140]}`")
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1

    return files


def analyze_diff(diff_text: str) -> ReviewAnalysis:
    original_chars = len(diff_text)
    analyzed_chars = min(original_chars, MAX_DIFF_CHARS)
    truncated = original_chars > MAX_DIFF_CHARS
    if truncated:
        diff_text = diff_text[:MAX_DIFF_CHARS]

    files = parse_diff(diff_text)
    total_additions = sum(file.additions for file in files)
    total_deletions = sum(file.deletions for file in files)
    risks: list[str] = []
    suggestions: list[str] = []

    if truncated:
        risks.append(
            f"Diff was truncated to {analyzed_chars:,} of {original_chars:,} characters; "
            "later files or lines were not analyzed."
        )
        suggestions.append("Run a narrower follow-up review for the omitted portion before relying on this result.")

    if not files:
        risks.append("The diff appears to be empty or could not be parsed.")
        suggestions.append("Confirm the PR branch contains committed changes before review.")

    for file in files:
        lowered = file.path.lower()
        if file.risky_lines:
            risks.extend(f"{file.path}: {line}" for line in file.risky_lines[:5])
        if any(part in lowered for part in ("auth", "security", "permission", "payment", "secret")):
            risks.append(f"{file.path}: touches a security-sensitive area and needs focused regression coverage.")
        if lowered.endswith(("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "package.json")):
            risks.append(f"{file.path}: dependency or package metadata changed; verify install and supply-chain impact.")
        if ".github/workflows/" in lowered:
            risks.append(f"{file.path}: CI workflow changed; verify permissions and trigger scope are minimal.")
        if "migration" in lowered or lowered.endswith(".sql"):
            risks.append(f"{file.path}: database schema or migration logic changed; verify rollback and idempotency.")

    if total_additions + total_deletions > 800:
        risks.append("Large diff size increases review risk; split or add focused test evidence if possible.")
    elif not risks:
        risks.append("No obvious high-risk patterns were detected in the added lines.")

    if not any("test" in file.path.lower() for file in files):
        suggestions.append("Add or reference targeted tests for the changed behavior.")
    if any(file.risky_lines for file in files):
        suggestions.append("Document why flagged risky lines are safe, or replace them with narrower helpers.")
    if any(".github/workflows/" in file.path.lower() for file in files):
        suggestions.append("Pin workflow permissions and include a dry-run or workflow-dispatch validation note.")
    if any(file.path.lower().endswith((".md", ".mdx", ".rst")) for file in files):
        suggestions.append("Preview the rendered documentation to catch broken links, formatting, or stale examples.")
    if not suggestions:
        suggestions.append("Include exact validation commands in the PR description for reviewer reproducibility.")

    confidence = "High"
    if total_additions + total_deletions > 800 or any(file.risky_lines for file in files):
        confidence = "Medium"
    if not files or total_additions + total_deletions > 2000 or truncated:
        confidence = "Low"

    return ReviewAnalysis(
        files,
        total_additions,
        total_deletions,
        risks,
        suggestions,
        confidence,
        truncated=truncated,
        original_chars=original_chars,
        analyzed_chars=analyzed_chars,
    )


def render_markdown(analysis: ReviewAnalysis, pr_url: str | None = None) -> str:
    changed = ", ".join(file.path for file in analysis.files[:5])
    if len(analysis.files) > 5:
        changed += f", and {len(analysis.files) - 5} more"
    changed = changed or "no parsed files"

    lines = [
        "## PR Review",
        "",
        "### Summary of changes",
        "",
        (
            f"This PR changes {len(analysis.files)} file(s): {changed}. "
            f"The parsed diff contains {analysis.total_additions} additions and "
            f"{analysis.total_deletions} deletions."
        ),
        (
            "The review below is generated from the pull request diff and should be "
            "combined with project-specific test results before merge."
        ),
    ]
    if analysis.truncated:
        lines.extend(
            [
                "",
                (
                    f"Only the first {analysis.analyzed_chars:,} of {analysis.original_chars:,} diff "
                    "characters were analyzed, so this review intentionally uses low confidence."
                ),
            ]
        )
    lines.extend(["", "### Identified risks", ""])
    lines.extend(f"- {risk}" for risk in analysis.risks)
    lines.extend(["", "### Improvement suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in analysis.suggestions)
    lines.extend(["", f"### Confidence score: {analysis.confidence}"])
    if pr_url:
        lines.extend(["", f"_Reviewed PR: {pr_url}_"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review comment.")
    parser.add_argument("--pr", help="GitHub pull request URL to fetch and review")
    parser.add_argument(
        "--diff-file",
        "--diff",
        dest="diff_file",
        help="Local unified diff file to review, useful for offline checks and tests",
    )
    parser.add_argument("--output", help="Write the Markdown review to this file instead of stdout")
    parser.add_argument(
        "--post-comment",
        "--post",
        action="store_true",
        help="Post the generated review to the PR using GITHUB_TOKEN or GH_TOKEN",
    )
    args = parser.parse_args(argv)

    if bool(args.pr) == bool(args.diff_file):
        parser.error("provide exactly one of --pr or --diff-file")
    if args.post_comment and not args.pr:
        parser.error("--post-comment requires --pr")

    try:
        if args.pr:
            diff_text = fetch_pr_diff(args.pr)
            pr_url = args.pr
        else:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
            pr_url = None
        rendered = render_markdown(analyze_diff(diff_text), pr_url=pr_url)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        if args.post_comment:
            post_pr_comment(args.pr, rendered)
    except Exception as exc:  # noqa: BLE001 - CLI error boundary
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
