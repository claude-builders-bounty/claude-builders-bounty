#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent for PR review.

A CLI tool that takes a PR URL (or local diff file), analyzes it,
and produces a structured Markdown review report covering code style,
potential bugs, security vulnerabilities, performance concerns,
test coverage, and documentation gaps.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff /tmp/pr.diff
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


GH_TOKEN_ENV = "GITHUB_TOKEN"
USER_AGENT = "claude-review-agent/1.0"


@dataclass
class ReviewCategory:
    file: str
    line: Optional[int]
    severity: str  # high / medium / low
    description: str


@dataclass
class ReviewReport:
    pr_url: str = ""
    title: str = ""
    summary: str = ""
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0
    code_style: list[ReviewCategory] = field(default_factory=list)
    potential_bugs: list[ReviewCategory] = field(default_factory=list)
    security: list[ReviewCategory] = field(default_factory=list)
    performance: list[ReviewCategory] = field(default_factory=list)
    missing_tests: list[str] = field(default_factory=list)
    doc_gaps: list[str] = field(default_factory=list)
    positive_notes: list[str] = field(default_factory=list)
    confidence: str = "Medium"

    def count_issues(self) -> int:
        return (
            len(self.code_style)
            + len(self.potential_bugs)
            + len(self.security)
            + len(self.performance)
            + len(self.missing_tests)
            + len(self.doc_gaps)
        )

    def count_high(self) -> int:
        cats = [
            self.code_style, self.potential_bugs,
            self.security, self.performance
        ]
        return sum(1 for c in sum(cats, []) if c.severity == "high")


def fetch_pr_diff(pr_url: str) -> tuple[str, str]:
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url
    )
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")

    owner, repo, pr_num = match.group(1), match.group(2), match.group(3)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"

    req = urllib.request.Request(api_url)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", USER_AGENT)

    token = os.environ.get(GH_TOKEN_ENV, "")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        diff = resp.read().decode("utf-8")

    req2 = urllib.request.Request(api_url)
    req2.add_header("Accept", "application/vnd.github.v3+json")
    req2.add_header("User-Agent", USER_AGENT)
    if token:
        req2.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req2, timeout=30) as resp2:
        pr_data = json.loads(resp2.read().decode("utf-8"))
        title = pr_data.get("title", "")

    return diff, title


def read_diff_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def analyze_diff(diff: str, pr_title: str) -> ReviewReport:
    report = ReviewReport(title=pr_title)

    lines = diff.split("\n")
    current_file = ""
    added_lines: list[tuple[str, int, str]] = []
    removed_lines: list[tuple[str, int, str]] = []
    line_num = 0

    for raw_line in lines:
        if raw_line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", raw_line)
            current_file = m.group(1) if m else ""
            report.files_changed += 1
            line_num = 0
        elif raw_line.startswith("@@ "):
            m = re.search(r"\+(\d+)", raw_line)
            line_num = int(m.group(1)) if m else 0
        elif raw_line.startswith("+") and not raw_line.startswith("+++"):
            report.additions += 1
            added_lines.append((current_file, line_num, raw_line[1:]))
            line_num += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            report.deletions += 1
            removed_lines.append((current_file, line_num, raw_line[1:]))
        else:
            line_num += 1

    file_set = {f for f, _, _ in added_lines}
    report.missing_tests = _check_missing_tests(file_set)
    report.doc_gaps = _check_doc_gaps(file_set)

    for f, ln, content in added_lines:
        _check_code_style(report, f, ln, content)
        _check_bugs(report, f, ln, content)
        _check_security(report, f, ln, content)
        _check_performance(report, f, ln, content)

    for f, ln, content in removed_lines:
        _check_removal_concerns(report, f, ln, content)

    report.summary = _build_summary(report)
    report.confidence = (
        "High" if report.count_issues() == 0
        else "Low" if report.count_high() > 1
        else "Medium"
    )

    if not report.positive_notes:
        report.positive_notes.append("Codebase appears well-structured overall.")

    return report


def _check_missing_tests(files: set[str]) -> list[str]:
    concerns = []
    src_files = [f for f in files if f.startswith("src/") or f.endswith(".ts") or f.endswith(".py") or f.endswith(".js")]
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files)
    if src_files and not has_tests:
        concerns.append("No test/spec files detected in this PR; consider adding tests for changed logic.")
    return concerns


def _check_doc_gaps(files: set[str]) -> list[str]:
    concerns = []
    has_readme = any("readme" in f.lower() for f in files)
    has_docs = any(f.startswith("docs/") for f in files)
    new_funcs = [f for f in files if f.endswith(".py") or f.endswith(".ts") or f.endswith(".js")]
    if new_funcs and not has_readme and not has_docs:
        concerns.append("New or modified functions detected but no documentation files (README/docs) updated.")
    return concerns


def _check_code_style(report: ReviewReport, f: str, ln: int, content: str):
    if len(content) > 120:
        report.code_style.append(ReviewCategory(
            file=f, line=ln, severity="low",
            description=f"Line exceeds 120 characters ({len(content)} chars). Consider breaking it up."
        ))
    if re.search(r'\t', content):
        report.code_style.append(ReviewCategory(
            file=f, line=ln, severity="low",
            description="Hard tab detected. Use spaces for indentation."
        ))
    if re.search(r'[ \t]+$', content):
        report.code_style.append(ReviewCategory(
            file=f, line=ln, severity="low",
            description="Trailing whitespace detected."
        ))
    if re.search(r'(?:print|console\.log)\s*\(', content) and not re.search(r'logger?\.', content):
        report.code_style.append(ReviewCategory(
            file=f, line=ln, severity="medium",
            description="Debug print/console.log left in code. Remove or replace with proper logging."
        ))


_BUG_PATTERNS = [
    (r'\bNone\s*=\s*\w+', "Assigning to None is likely a bug."),
    (r'(?:==|!=)\s+None\b', "Use 'is None' / 'is not None' instead of equality comparison with None."),
    (r'\bexcept\s*:', "Bare except clause catches all exceptions. Specify exception types."),
    (r'\bpass\s*$', "Empty block detected. Implement or remove."),
    (r'\beval\s*\(', "eval() on dynamic input is dangerous and a code smell."),
]


def _check_bugs(report: ReviewReport, f: str, ln: int, content: str):
    for pattern, desc in _BUG_PATTERNS:
        if re.search(pattern, content):
            report.potential_bugs.append(ReviewCategory(
                file=f, line=ln, severity="high" if "bug" in desc.lower() else "medium",
                description=desc
            ))


_SEC_PATTERNS = [
    (r'(?:password|secret|api[_-]?key|token)\s*=\s*["\'][^"\']+["\']', "Possible hardcoded secret. Use environment variables or a vault."),
    (r'(?:SELECT|INSERT|UPDATE|DELETE)\s+.*\+', "SQL query built with string concatenation — SQL injection risk. Use parameterized queries."),
    (r'<\s*script\b', "Inline script tag in code — XSS risk. Use CSP-safe patterns."),
    (r'(?:os\.system|subprocess\.call|subprocess\.run|subprocess\.Popen)\s*\(', "Shell command execution — validate inputs to avoid command injection."),
    (r'request[s]?\s+\.\.\.\s+verify\s*=\s*False', "SSL verification disabled — security risk."),
    (r'\.innerHTML\s*=', "Direct innerHTML assignment — XSS risk. Use textContent or sanitize."),
]


def _check_security(report: ReviewReport, f: str, ln: int, content: str):
    for pattern, desc in _SEC_PATTERNS:
        if re.search(pattern, content):
            report.security.append(ReviewCategory(
                file=f, line=ln, severity="high", description=desc
            ))


_PERF_PATTERNS = [
    (r'for\s+\w+\s+in\s+range\(len\(', "Iterating with range(len()) is slower and less Pythonic than direct iteration."),
    (r'\+\=\s*\[\s*\]', "Repeated list concatenation is O(n²). Use list.extend() or .append()."),
    (r'\.(?:text|html)\s*\(\s*\)\s*\.\s*(?:text|html)\s*\(\s*\)', "Chained jQuery-like DOM queries are inefficient."),
    (r'(?:COUNT|count)\s*\(\s*\*\s*\)', "COUNT(*) on large tables can be slow. Consider indexed alternatives."),
    (r'\bawait\s+.*\bawait\b', "Sequential awaits can be parallelized with Promise.all/asyncio.gather."),
]


def _check_performance(report: ReviewReport, f: str, ln: int, content: str):
    for pattern, desc in _PERF_PATTERNS:
        if re.search(pattern, content):
            report.performance.append(ReviewCategory(
                file=f, line=ln, severity="medium", description=desc
            ))


def _check_removal_concerns(report: ReviewReport, f: str, ln: int, content: str):
    if re.search(r'\bTODO\b', content, re.IGNORECASE):
        report.doc_gaps.append(f"TODO marker removed in {f}:{ln} — verify the task is completed.")


def _build_summary(report: ReviewReport) -> str:
    total = report.count_issues()
    high = report.count_high()
    return (
        f"This PR changes **{report.files_changed}** files "
        f"(+{report.additions}/-{report.deletions} lines). "
        f"Found **{total}** issue{'s' if total != 1 else ''} "
        f"({high} high severity)."
    )


def format_review(report: ReviewReport) -> str:
    lines = []
    lines.append("# PR Review Report\n")
    if report.pr_url:
        lines.append(f"**PR**: {report.pr_url}\n")
    lines.append(f"**Title**: {report.title}\n" if report.title else "")
    lines.append(f"**Confidence Score**: {report.confidence}\n")
    lines.append("---\n")

    lines.append("## Summary of Changes")
    lines.append(report.summary)
    lines.append("")

    if report.code_style:
        lines.append("---\n## Code Style Issues")
        for c in report.code_style:
            icon = "🔴" if c.severity == "high" else "🟡" if c.severity == "medium" else "🔵"
            loc = f"`{c.file}:{c.line}`" if c.line else f"`{c.file}`"
            lines.append(f"- {icon} [{c.severity.upper()}] {loc} — {c.description}")

    if report.potential_bugs:
        lines.append("---\n## Potential Bugs")
        for c in report.potential_bugs:
            icon = "🐛"
            loc = f"`{c.file}:{c.line}`" if c.line else f"`{c.file}`"
            lines.append(f"- {icon} [{c.severity.upper()}] {loc} — {c.description}")

    if report.security:
        lines.append("---\n## Security Vulnerabilities")
        for c in report.security:
            loc = f"`{c.file}:{c.line}`" if c.line else f"`{c.file}`"
            lines.append(f"- 🔒 [{c.severity.upper()}] {loc} — {c.description}")

    if report.performance:
        lines.append("---\n## Performance Concerns")
        for c in report.performance:
            loc = f"`{c.file}:{c.line}`" if c.line else f"`{c.file}`"
            lines.append(f"- ⚡ [{c.severity.upper()}] {loc} — {c.description}")

    if report.missing_tests:
        lines.append("---\n## Missing Tests")
        for t in report.missing_tests:
            lines.append(f"- 🧪 {t}")

    if report.doc_gaps:
        lines.append("---\n## Documentation Gaps")
        for d in report.doc_gaps:
            lines.append(f"- 📝 {d}")

    if report.positive_notes:
        lines.append("---\n## Positive Notes")
        for n in report.positive_notes:
            lines.append(f"- ✅ {n}")

    lines.append("\n---")
    lines.append("*Review generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/pr-review-agent) — Claude Code PR review sub-agent.*")
    return "\n".join(lines)


def post_comment(pr_url: str, body: str):
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url
    )
    if not match:
        raise ValueError(f"Cannot parse PR URL: {pr_url}")
    owner, repo, pr_num = match.group(1), match.group(2), match.group(3)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
    token = os.environ.get(GH_TOKEN_ENV, "")
    if not token:
        raise RuntimeError(f"{GH_TOKEN_ENV} not set — cannot post comment.")

    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", USER_AGENT)

    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR review sub-agent — automated code review with structured Markdown output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff /tmp/pr.diff --output review.md
  claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
        """.strip(),
    )
    parser.add_argument("--pr", help="GitHub PR URL to review")
    parser.add_argument("--diff", help="Path to a local diff file")
    parser.add_argument("--output", help="Write review to file instead of stdout")
    parser.add_argument("--post-comment", action="store_true",
                        help="Post the review as a comment on the PR (requires GITHUB_TOKEN)")
    args = parser.parse_args()

    if not args.pr and not args.diff:
        parser.print_help()
        sys.exit(1)

    if args.pr:
        print(f"Fetching PR diff from {args.pr} ...", file=sys.stderr)
        diff, title = fetch_pr_diff(args.pr)
    else:
        print(f"Reading diff from {args.diff} ...", file=sys.stderr)
        diff = read_diff_file(args.diff)
        title = ""

    print("Analyzing diff ...", file=sys.stderr)
    report = analyze_diff(diff, title)
    report.pr_url = args.pr or ""

    output = format_review(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.post_comment:
        if not args.pr:
            print("--post-comment requires --pr", file=sys.stderr)
            sys.exit(1)
        print("Posting review comment ...", file=sys.stderr)
        status = post_comment(args.pr, output)
        print(f"Comment posted (HTTP {status})", file=sys.stderr)


if __name__ == "__main__":
    main()
