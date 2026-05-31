#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub pull request diff.

The implementation is intentionally dependency-free so it can run in CI,
inside Claude Code, or on a fresh developer machine with only Python 3.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$")
PR_SHORTHAND_RE = re.compile(r"^([^/\s]+)/([^/#\s]+)(?:/|#)(\d+)$")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
DIFF_GIT_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
HUNK_RE = re.compile(r"^@@")
COMMENT_MARKER = "<!-- claude-review:bot -->"


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    added_lines: list[str]
    deleted_lines: list[str]


@dataclass(frozen=True)
class Finding:
    title: str
    detail: str


def parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    value = pr_url.strip()
    match = PR_URL_RE.match(value) or PR_SHORTHAND_RE.match(value)
    if not match:
        raise ValueError("PR must look like https://github.com/owner/repo/pull/123, owner/repo/123, or owner/repo#123")
    return match.group(1), match.group(2), match.group(3)


def fetch_diff(pr_url: str, timeout: int = 30) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    request = urllib.request.Request(
        diff_url,
        headers={"User-Agent": "claude-review/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError):
        return fetch_diff_with_gh(owner, repo, number, timeout)


def fetch_diff_with_gh(owner: str, repo: str, number: str, timeout: int) -> str:
    command = ["gh", "pr", "diff", number, "--repo", f"{owner}/{repo}"]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not fetch PR diff from GitHub: {exc}") from exc
    return completed.stdout


def read_diff(path: str | None, pr_url: str | None, timeout: int) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    if pr_url:
        return fetch_diff(pr_url, timeout)
    raise ValueError("Provide either --pr or --diff-file")


def summarize_diff(diff_text: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0
    added_lines: list[str] = []
    deleted_lines: list[str] = []

    for line in diff_text.splitlines():
        git_match = DIFF_GIT_RE.match(line)
        if git_match:
            old_path, new_path = git_match.groups()
            files.append(new_path if new_path != "/dev/null" else old_path)
            continue

        file_match = DIFF_FILE_RE.match(line)
        if file_match and file_match.group(1) != "/dev/null":
            file_name = file_match.group(1)
            if file_name not in files:
                files.append(file_name)
        elif HUNK_RE.match(line):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            deleted_lines.append(line[1:])

    return DiffStats(files, additions, deletions, hunks, added_lines, deleted_lines)


def unique_top(values: Iterable[str], limit: int) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
            if len(output) == limit:
                break
    return output


def classify_files(files: list[str]) -> list[str]:
    groups: list[str] = []
    for file_name in files:
        lower = file_name.lower()
        if lower.endswith((".md", ".mdx", ".rst", ".txt")) or "/docs/" in lower:
            groups.append("documentation")
        elif (
            lower.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", "_test.py"))
            or lower.rsplit("/", 1)[-1].startswith("test_") and lower.endswith(".py")
            or "/__test__/" in lower
            or "/__tests__/" in lower
            or "/test/" in lower
            or "/tests/" in lower
        ):
            groups.append("tests")
        elif lower.endswith((".yml", ".yaml")) or ".github/workflows/" in lower:
            groups.append("automation")
        elif lower.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go")):
            groups.append("application code")
        elif lower.endswith((".json", ".toml", ".lock")):
            groups.append("configuration")
        else:
            groups.append("project files")
    return unique_top(groups, 3)


def find_risks(stats: DiffStats) -> list[Finding]:
    added = "\n".join(stats.added_lines)
    deleted = "\n".join(stats.deleted_lines)
    risks: list[Finding] = []

    patterns = [
        (r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}", "Possible secret added", "A credential-like value appears in added lines; verify it is not a real secret."),
        (r"(?i)\beval\s*\(|new Function\s*\(", "Dynamic code execution", "The diff adds dynamic execution; confirm inputs cannot be attacker-controlled."),
        (r"(?i)innerHTML\s*=", "Raw HTML rendering", "The diff writes raw HTML; check escaping and XSS protections."),
        (r"(?i)verify\s*[:=]\s*false", "TLS verification disabled", "The diff appears to disable verification; this is rarely safe outside tests."),
        (r"(?i)except\s*:\s*$|catch\s*\([^)]*\)\s*\{\s*\}", "Broad or empty error handling", "The diff may hide failures; preserve useful errors for users and logs."),
        (r"(?i)TODO|FIXME|HACK", "Unfinished marker added", "The diff adds an unfinished marker; decide whether it blocks merging."),
        (r"(?i)delete\s+from\s+\w+(?![\s\S]{0,120}\bwhere\b)", "Potential unscoped delete", "A DELETE statement appears without a nearby WHERE clause."),
    ]
    for pattern, title, detail in patterns:
        if re.search(pattern, added):
            risks.append(Finding(title, detail))

    if stats.additions + stats.deletions > 500:
        risks.append(
            Finding(
                "Large review surface",
                "The PR changes more than 500 lines; split or request focused reviewer attention if possible.",
            )
        )
    if stats.files and not any("test" in file_name.lower() or "spec" in file_name.lower() for file_name in stats.files):
        code_files = [file_name for file_name in stats.files if file_name.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go"))]
        if code_files:
            risks.append(
                Finding(
                    "No test file changed",
                    "Application code changed without an obvious test update in the diff.",
                )
            )
    if deleted and not added:
        risks.append(Finding("Deletion-only diff", "Confirm the removed behavior is obsolete and not still referenced."))

    return unique_findings(risks, 6)


def unique_findings(findings: list[Finding], limit: int) -> list[Finding]:
    seen: set[str] = set()
    output: list[Finding] = []
    for finding in findings:
        if finding.title in seen:
            continue
        seen.add(finding.title)
        output.append(finding)
        if len(output) == limit:
            break
    return output


def suggestions(stats: DiffStats, risks: list[Finding]) -> list[str]:
    output: list[str] = []
    if stats.files:
        output.append(f"Ask a maintainer familiar with `{stats.files[0]}` to sanity-check the main behavior change.")
    if any(risk.title == "No test file changed" for risk in risks):
        output.append("Add or update a focused regression test before merge.")
    if any(risk.title == "Large review surface" for risk in risks):
        output.append("Consider splitting mechanical, test, and behavior changes into separate PRs.")
    if any(risk.title == "Possible secret added" for risk in risks):
        output.append("Rotate the value if it is real and replace it with documented configuration.")
    if not output:
        output.append("Run the project test suite and include the relevant command output in the PR thread.")
    output.append("Confirm user-facing behavior against the issue acceptance criteria, not only static checks.")
    return unique_top(output, 5)


def confidence(stats: DiffStats, risks: list[Finding]) -> str:
    changed_lines = stats.additions + stats.deletions
    if any(risk.title in {"Possible secret added", "Dynamic code execution", "TLS verification disabled"} for risk in risks):
        return "Low"
    if changed_lines > 500 or len(risks) >= 3:
        return "Medium"
    if not stats.files:
        return "Low"
    return "High"


def render_review(pr_url: str | None, stats: DiffStats) -> str:
    risks = find_risks(stats)
    groups = classify_files(stats.files)
    files_preview = ", ".join(f"`{name}`" for name in unique_top(stats.files, 5)) or "no files detected"
    group_text = ", ".join(groups) if groups else "unknown areas"
    source = f" for {pr_url}" if pr_url else ""

    lines = [
        "## Summary",
        "",
        f"This PR{source} changes {len(stats.files)} file(s), with {stats.additions} additions and {stats.deletions} deletions across {stats.hunks} diff hunk(s).",
        f"The touched areas look like {group_text}; primary files include {files_preview}.",
        "",
        "## Identified Risks",
        "",
    ]
    if risks:
        lines.extend(f"- **{risk.title}:** {risk.detail}" for risk in risks)
    else:
        lines.append("- No obvious static risk patterns were detected in the diff.")

    lines.extend(["", "## Improvement Suggestions", ""])
    lines.extend(f"- {item}" for item in suggestions(stats, risks))
    lines.extend(["", f"## Confidence: {confidence(stats, risks)}", ""])
    return "\n".join(lines)


def run_gh_api(args: list[str], timeout: int) -> str:
    command = ["gh", "api", *args]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not call GitHub API with gh: {exc}") from exc
    return completed.stdout


def post_review(pr_url: str, review_body: str, timeout: int) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    payload = f"{COMMENT_MARKER}\n{review_body}"
    comments_path = f"repos/{owner}/{repo}/issues/{number}/comments"
    comments_raw = run_gh_api([comments_path, "--paginate"], timeout)
    comments = json.loads(comments_raw or "[]")

    existing_id: int | None = None
    for comment in comments:
        body = comment.get("body", "")
        if COMMENT_MARKER in body:
            existing_id = comment["id"]
            break

    if existing_id is not None:
        result_raw = run_gh_api(
            ["--method", "PATCH", f"repos/{owner}/{repo}/issues/comments/{existing_id}", "-f", f"body={payload}"],
            timeout,
        )
    else:
        result_raw = run_gh_api(["--method", "POST", comments_path, "-f", f"body={payload}"], timeout)

    result = json.loads(result_raw or "{}")
    return result.get("html_url", pr_url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print structured Markdown.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL or shorthand, e.g. https://github.com/owner/repo/pull/123 or owner/repo#123")
    source.add_argument("--diff-file", help="Path to a local .diff file")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds for --pr")
    parser.add_argument("--output", help="Write the generated Markdown review to this file")
    parser.add_argument("--post", action="store_true", help="Post or update an idempotent comment on the PR")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.post and not args.pr:
            raise ValueError("--post requires --pr so the target PR is known")
        diff_text = read_diff(args.diff_file, args.pr, args.timeout)
        stats = summarize_diff(diff_text)
        review = render_review(args.pr, stats)
        if args.output:
            Path(args.output).write_text(review, encoding="utf-8")
        if args.post:
            comment_url = post_review(args.pr, review, args.timeout)
            print(f"Posted review comment: {comment_url}", file=sys.stderr)
        print(review)
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
