#!/usr/bin/env python3
"""
PR Reviewer — Automated GitHub Pull Request Code Review Agent

Posts a structured review comment on a GitHub PR with:
  • Overall summary of changes
  • Code quality score (1–10)
  • Security concerns
  • Performance suggestions
  • Line-by-line feedback
  • Suggested improvements

Usage:
    python pr-reviewer.py --repo owner/repo --pr 123
    python pr-reviewer.py --repo owner/repo --pr 123 --post
    python pr-reviewer.py --repo owner/repo --pr 123 --output review.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class FileChange:
    filename: str
    status: str  # added, removed, modified, renamed
    additions: int
    deletions: int
    patch: str = ""
    previous_filename: Optional[str] = None


@dataclass
class ReviewFeedback:
    severity: str  # "error", "warning", "suggestion", "info"
    file: str
    line: Optional[int]
    message: str


@dataclass
class PRReview:
    summary: str
    quality_score: int
    security_concerns: list[str]
    performance_suggestions: list[str]
    line_feedback: list[ReviewFeedback]
    improvements: list[str]
    stats: dict


# ─── GitHub API client ──────────────────────────────────────────────────────

class GitHubClient:
    """Thin wrapper around the GitHub REST API."""

    API = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _get(self, path: str, **params) -> dict | list:
        url = f"{self.API}{path}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.API}{path}"
        resp = self.session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_pr(self, repo: str, pr_number: int) -> dict:
        return self._get(f"/repos/{repo}/pulls/{pr_number}")

    def get_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        files: list[dict] = []
        page = 1
        while True:
            batch = self._get(f"/repos/{repo}/pulls/{pr_number}/files", per_page=100, page=page)
            if not batch:
                break
            files.extend(batch)
            page += 1
        return files

    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"{self.API}/repos/{repo}/pulls/{pr_number}"
        resp = self.session.get(url, headers={"Accept": "application/vnd.github.v3.diff"})
        resp.raise_for_status()
        return resp.text

    def post_comment(self, repo: str, pr_number: int, body: str) -> dict:
        return self._post(f"/repos/{repo}/issues/{pr_number}/comments", {"body": body})


# ─── Diff parser ─────────────────────────────────────────────────────────────

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_patch(patch: str) -> list[tuple[int, str]]:
    """Return list of (new_line_number, content) for added/modified lines."""
    results: list[tuple[int, str]] = []
    current_line = 0
    for raw in patch.splitlines():
        m = _HUNK_RE.match(raw)
        if m:
            current_line = int(m.group(2))
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            results.append((current_line, raw[1:]))
            current_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            pass  # removed line — don't increment new line counter
        else:
            current_line += 1
    return results


# ─── Static analysis heuristics ─────────────────────────────────────────────

_SECURITY_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, severity, message)
    (r"(?i)(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]+['\"]",
     "error", "Hardcoded secret or credential detected."),
    (r"(?i)eval\s*\(", "warning", "Use of `eval()` — potential code injection risk."),
    (r"(?i)exec\s*\(", "warning", "Use of `exec()` — potential code injection risk."),
    (r"(?i)subprocess\..*shell\s*=\s*True", "warning", "Shell injection risk: `shell=True` in subprocess call."),
    (r"(?i)os\.system\s*\(", "warning", "Use of `os.system()` — prefer `subprocess.run()` for safety."),
    (r"(?i)pickle\.load", "warning", "Deserializing with `pickle.load` on untrusted data can execute arbitrary code."),
    (r"(?i)tempfile\.mktemp\b", "suggestion", "Use `tempfile.mkstemp()` instead — `mktemp()` has a race condition."),
    (r"(?i)SELECT\s+.*\bFROM\b.*\bWHERE\b.*(%s|\?)", "warning", "Possible SQL injection — use parameterised queries."),
    (r"(?i)__import__\s*\(", "warning", "Dynamic import — verify input is trusted."),
    (r"(?i)innerHTML\s*=", "suggestion", "Setting `innerHTML` directly can lead to XSS — consider textContent or sanitisation."),
    (r"(?i)dangerouslySetInnerHTML", "warning", "`dangerouslySetInnerHTML` — ensure input is sanitised."),
    (r"(?i)disable.*ssl.*verif", "error", "SSL verification disabled — this allows MITM attacks."),
    (r"(?i)CORS.*\*\s*", "suggestion", "Wildcard CORS origin — restrict to trusted domains."),
]

_PERF_PATTERNS: list[tuple[str, str]] = [
    (r"for\s+.*\s+in\s+.*:\s*$", "Check for O(n²) patterns: nested loops over large collections."),
    (r"\.append\(.*\)\s*$", "Consider list comprehension or `extend()` for bulk appends."),
    (r"time\.sleep\s*\(", "Sleeping in code — consider async waits or polling with backoff."),
    (r"(?i)SELECT\s+\*\s+FROM", "Avoid `SELECT *` — select only the columns you need."),
    (r"(?i)requests\.get\(|requests\.post\(|requests\.put\(|requests\.delete\(",
     "HTTP call in a loop? Consider batching or async requests (`aiohttp`, `httpx`)."),
    (r"(?i)open\(.*\)(?!.*with)", "File opened without context manager — may leak file descriptors."),
]

_STYLE_PATTERNS: list[tuple[str, str, str]] = [
    (r"TODO|FIXME|HACK|XXX", "info", "Contains a TODO/FIXME comment — track it in your issue tracker."),
    (r"print\s*\(", "suggestion", "Debug `print()` left in code — use `logging` for production."),
    (r"console\.log\s*\(", "suggestion", "Debug `console.log()` left in code — remove or use a logger."),
    (r"(?i)# ?noqa", "info", "Linter suppression comment — ensure the suppression is justified."),
    (r"\t", "info", "Tabs detected — ensure this matches project conventions."),
    (r"(?<=\S)\s{4,}", "info", "Multiple consecutive spaces — check indentation style."),
]


def _check_patterns(
    line: str,
    patterns: list[tuple],
    filename: str,
    line_no: int,
) -> list[ReviewFeedback]:
    hits: list[ReviewFeedback] = []
    for pattern, *rest in patterns:
        if re.search(pattern, line):
            if len(rest) == 2:
                severity, msg = rest
            else:
                severity, msg = "suggestion", rest[0]
            hits.append(ReviewFeedback(severity=severity, file=filename, line=line_no, message=msg))
    return hits


# ─── Review engine ───────────────────────────────────────────────────────────

def _classify_changes(files: list[FileChange]) -> dict:
    categories = {
        "source": [], "tests": [], "docs": [], "config": [], "ci": [], "other": [],
    }
    for f in files:
        name = f.filename.lower()
        if any(name.endswith(ext) for ext in (".test.", ".spec.", "_test.", "test_", "tests/")):
            categories["tests"].append(f)
        elif any(name.endswith(ext) for ext in (".md", ".rst", ".txt", ".adoc")):
            categories["docs"].append(f)
        elif any(seg in name for seg in ("ci/", ".github/workflows/", "dockerfile", "docker-compose")):
            categories["ci"].append(f)
        elif any(name.endswith(ext) for ext in (".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env")):
            categories["config"].append(f)
        elif any(name.endswith(ext) for ext in (
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".c", ".cpp",
            ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".bash", ".zsh",
        )):
            categories["source"].append(f)
        else:
            categories["other"].append(f)
    return categories


def _score_quality(
    files: list[FileChange],
    feedback: list[ReviewFeedback],
    categories: dict,
) -> tuple[int, str]:
    """Return (score 1–10, rationale)."""
    score = 10
    reasons: list[str] = []

    total_adds = sum(f.additions for f in files)
    total_dels = sum(f.deletions for f in files)

    # Large PR penalty
    if total_adds + total_dels > 1000:
        score -= 2
        reasons.append("Very large PR (>1000 changed lines) — consider splitting.")
    elif total_adds + total_dels > 500:
        score -= 1
        reasons.append("Large PR (>500 changed lines) — consider splitting into smaller PRs.")

    # Many files penalty
    if len(files) > 30:
        score -= 2
        reasons.append(f"Touches {len(files)} files — high blast radius.")
    elif len(files) > 15:
        score -= 1
        reasons.append(f"Touches {len(files)} files — moderate blast radius.")

    # No tests
    if not categories["tests"]:
        score -= 1
        reasons.append("No test files changed — ensure adequate test coverage.")

    # Security issues penalty
    sec_errors = sum(1 for f in feedback if f.severity == "error")
    sec_warnings = sum(1 for f in feedback if f.severity == "warning")
    score -= min(sec_errors * 2, 3)
    score -= min(sec_warnings, 2)
    if sec_errors:
        reasons.append(f"{sec_errors} security error(s) found.")
    if sec_warnings:
        reasons.append(f"{sec_warnings} security warning(s) found.")

    # General feedback penalty
    suggestions = sum(1 for f in feedback if f.severity == "suggestion")
    if suggestions > 10:
        score -= 1
        reasons.append(f"{suggestions} code quality suggestions.")

    score = max(1, min(10, score))
    rationale = " | ".join(reasons) if reasons else "Clean diff with no major concerns."
    return score, rationale


def review_pr(repo: str, pr_number: int, client: GitHubClient) -> tuple[PRReview, dict]:
    """Perform full analysis and return a PRReview + raw PR metadata."""
    # Fetch PR metadata
    pr_meta = client.get_pr(repo, pr_number)
    files_raw = client.get_pr_files(repo, pr_number)

    files: list[FileChange] = []
    for f in files_raw:
        files.append(FileChange(
            filename=f["filename"],
            status=f["status"],
            additions=f["additions"],
            deletions=f["deletions"],
            patch=f.get("patch", ""),
            previous_filename=f.get("previous_filename"),
        ))

    categories = _classify_changes(files)

    # Line-by-line analysis
    all_feedback: list[ReviewFeedback] = []
    for fc in files:
        if not fc.patch:
            continue
        for line_no, line_content in parse_patch(fc.patch):
            all_feedback.extend(_check_patterns(line_content, _SECURITY_PATTERNS, fc.filename, line_no))
            all_feedback.extend(_check_patterns(line_content, _PERF_PATTERNS, fc.filename, line_no))
            all_feedback.extend(_check_patterns(line_content, _STYLE_PATTERNS, fc.filename, line_no))

    security_concerns = sorted({f.message for f in all_feedback if f.severity in ("error", "warning")})
    perf_suggestions = sorted({f.message for f in all_feedback if f.severity == "suggestion"
                               and "perf" in f.message.lower() or "loop" in f.message.lower()
                               or "select" in f.message.lower() or "batch" in f.message.lower()
                               or "http" in f.message.lower() or "append" in f.message.lower()
                               or "sleep" in f.message.lower() or "open(" in f.message.lower()})

    # If heuristic didn't catch perf suggestions separately, gather them
    if not perf_suggestions:
        perf_suggestions = sorted({f.message for f in all_feedback
                                   if any(kw in f.message.lower() for kw in (
                                       "loop", "batch", "select", "http", "append", "sleep",
                                       "nested", "o(n", "comprehension", "async", "file descript",
                                   ))})

    score, score_rationale = _score_quality(files, all_feedback, categories)

    # Build summary
    summary_parts: list[str] = []
    summary_parts.append(f"**PR #{pr_number}**: {pr_meta.get('title', 'N/A')}")
    summary_parts.append(f"**Author**: {pr_meta.get('user', {}).get('login', 'N/A')}")
    summary_parts.append(f"**Base → Head**: `{pr_meta.get('base', {}).get('ref', '?')}` ← `{pr_meta.get('head', {}).get('ref', '?')}`")
    summary_parts.append("")

    total_adds = sum(f.additions for f in files)
    total_dels = sum(f.deletions for f in files)
    summary_parts.append(f"**{len(files)} file(s) changed**: +{total_adds} / -{total_dels} lines")
    summary_parts.append("")

    cat_summary = []
    for cat, items in categories.items():
        if items:
            cat_summary.append(f"  • {cat}: {len(items)} file(s)")
    if cat_summary:
        summary_parts.append("**Change categories**:")
        summary_parts.extend(cat_summary)

    # Improvements
    improvements: list[str] = []
    if not categories["tests"]:
        improvements.append("Add or update tests to cover the changed logic.")
    if any(f.filename.endswith((".py",)) for f in files):
        improvements.append("Run `ruff check` or `flake8` to catch style/lint issues.")
    if any(f.filename.endswith((".js", ".ts", ".tsx", ".jsx")) for f in files):
        improvements.append("Run `eslint` and `prettier` to ensure consistent style.")
    if total_adds + total_dels > 500:
        improvements.append("Consider breaking this PR into smaller, focused PRs for easier review.")
    if any(f.status == "added" and f.filename.endswith((".py",)) for f in files):
        improvements.append("Add docstrings and type hints to new Python modules.")
    improvements.append("Ensure CI passes before requesting review.")
    improvements.append("Update CHANGELOG or release notes if user-facing.")

    stats = {
        "files_changed": len(files),
        "additions": total_adds,
        "deletions": total_dels,
        "categories": {k: len(v) for k, v in categories.items()},
        "feedback_count": len(all_feedback),
    }

    review = PRReview(
        summary="\n".join(summary_parts),
        quality_score=score,
        security_concerns=security_concerns,
        performance_suggestions=perf_suggestions,
        line_feedback=sorted(all_feedback, key=lambda f: (f.file, f.line or 0)),
        improvements=improvements,
        stats=stats,
    )
    return review, pr_meta


# ─── Markdown formatter ─────────────────────────────────────────────────────

_SEVERITY_EMOJI = {"error": "🔴", "warning": "🟡", "suggestion": "💡", "info": "ℹ️"}


def format_review_markdown(review: PRReview, repo: str, pr_number: int) -> str:
    """Render the review as a GitHub-flavoured Markdown comment."""
    lines: list[str] = []

    lines.append("## 🤖 Automated PR Review")
    lines.append("")
    lines.append(review.summary)
    lines.append("")

    # Score
    bar_filled = "█" * review.quality_score
    bar_empty = "░" * (10 - review.quality_score)
    lines.append(f"### Code Quality: {review.quality_score}/10  `{bar_filled}{bar_empty}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Security
    lines.append("### 🔒 Security Concerns")
    if review.security_concerns:
        for concern in review.security_concerns:
            lines.append(f"- ⚠️ {concern}")
    else:
        lines.append("- ✅ No security concerns detected.")
    lines.append("")

    # Performance
    lines.append("### ⚡ Performance Suggestions")
    if review.performance_suggestions:
        for s in review.performance_suggestions:
            lines.append(f"- 💡 {s}")
    else:
        lines.append("- ✅ No performance issues detected.")
    lines.append("")

    # Line-by-line feedback
    if review.line_feedback:
        lines.append("### 📝 Line-by-Line Feedback")
        lines.append("")
        # Group by file
        by_file: dict[str, list[ReviewFeedback]] = {}
        for fb in review.line_feedback:
            by_file.setdefault(fb.file, []).append(fb)
        for fname, items in by_file.items():
            lines.append(f"**`{fname}`**")
            lines.append("")
            lines.append("| Line | Severity | Comment |")
            lines.append("|------|----------|---------|")
            for fb in items:
                emoji = _SEVERITY_EMOJI.get(fb.severity, "")
                line_str = f"L{fb.line}" if fb.line else "—"
                lines.append(f"| {line_str} | {emoji} {fb.severity} | {fb.message} |")
            lines.append("")
    else:
        lines.append("### 📝 Line-by-Line Feedback")
        lines.append("")
        lines.append("_No line-level issues found._")
        lines.append("")

    # Improvements
    lines.append("### ✨ Suggested Improvements")
    for i, imp in enumerate(review.improvements, 1):
        lines.append(f"{i}. {imp}")
    lines.append("")

    # Stats footer
    lines.append("---")
    lines.append(f"<sub>📊 {review.stats['files_changed']} files · +{review.stats['additions']} / -{review.stats['deletions']} · {review.stats['feedback_count']} feedback item(s)</sub>")
    lines.append("")
    lines.append("<sub>Generated by [PR Reviewer](https://github.com/nousresearch/bounty-pr-reviewer) 🤖</sub>")

    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Automated GitHub PR code reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python pr-reviewer.py --repo owner/repo --pr 42
              python pr-reviewer.py --repo owner/repo --pr 42 --post
              python pr-reviewer.py --repo owner/repo --pr 42 --output review.md
        """),
    )
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/repo format")
    parser.add_argument("--pr", required=True, type=int, help="Pull request number")
    parser.add_argument("--post", action="store_true", help="Post the review as a PR comment")
    parser.add_argument("--output", "-o", type=str, help="Write review to a file instead of stdout")
    parser.add_argument("--json", action="store_true", help="Output raw review data as JSON")
    parser.add_argument("--token", type=str, help="GitHub token (or set GITHUB_TOKEN / GH_TOKEN)")

    args = parser.parse_args(argv)

    # Validate repo format
    if "/" not in args.repo:
        print("Error: --repo must be in owner/repo format", file=sys.stderr)
        return 1

    client = GitHubClient(token=args.token)

    if not client.token and args.post:
        print("Error: --post requires authentication. Set GITHUB_TOKEN or pass --token.", file=sys.stderr)
        return 1

    print(f"🔍 Fetching PR #{args.pr} from {args.repo}...", file=sys.stderr)

    try:
        review, pr_meta = review_pr(args.repo, args.pr, client)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        print(f"Error: GitHub API returned {status}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        output = json.dumps({
            "summary": review.summary,
            "quality_score": review.quality_score,
            "security_concerns": review.security_concerns,
            "performance_suggestions": review.performance_suggestions,
            "line_feedback": [
                {"severity": f.severity, "file": f.file, "line": f.line, "message": f.message}
                for f in review.line_feedback
            ],
            "improvements": review.improvements,
            "stats": review.stats,
        }, indent=2)
    else:
        output = format_review_markdown(review, args.repo, args.pr)

    if args.output:
        Path(args.output).write_text(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.post:
        print(f"📤 Posting review comment on PR #{args.pr}...", file=sys.stderr)
        md = format_review_markdown(review, args.repo, args.pr)
        try:
            client.post_comment(args.repo, args.pr, md)
            print(f"✅ Review posted on https://github.com/{args.repo}/pull/{args.pr}", file=sys.stderr)
        except requests.HTTPError as exc:
            print(f"Error posting comment: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
