#!/usr/bin/env python3
"""Review GitHub PR diffs and print structured Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)/?$")
FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*)$")
HUNK_RE = re.compile(r"^@@")


@dataclass
class ChangedFile:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0

    @property
    def ext(self) -> str:
        return pathlib.Path(self.path).suffix.lower() or "[none]"


@dataclass
class DiffStats:
    files: dict[str, ChangedFile] = field(default_factory=dict)
    total_additions: int = 0
    total_deletions: int = 0
    raw_lines: int = 0

    @property
    def changed_files(self) -> list[ChangedFile]:
        return list(self.files.values())


@dataclass
class Finding:
    severity: str
    title: str
    detail: str
    files: list[str]


def fetch_pr_diff(pr_url: str, max_bytes: int) -> tuple[str, str]:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")

    owner, repo, number = match.groups()
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    request = urllib.request.Request(
        diff_url,
        headers={
            "Accept": "text/x-diff",
            "User-Agent": "claude-pr-reviewer/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {diff_url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff: {exc.reason}") from exc

    if len(payload) > max_bytes:
        raise RuntimeError(f"Diff exceeds {max_bytes} bytes; rerun with --max-diff-bytes if needed")

    return payload.decode("utf-8", errors="replace"), diff_url


def read_diff_file(path: str, max_bytes: int) -> tuple[str, str]:
    diff_path = pathlib.Path(path)
    payload = diff_path.read_bytes()
    if len(payload) > max_bytes:
        raise RuntimeError(f"Diff exceeds {max_bytes} bytes; rerun with --max-diff-bytes if needed")
    return payload.decode("utf-8", errors="replace"), str(diff_path)


def parse_diff(diff_text: str) -> DiffStats:
    stats = DiffStats(raw_lines=len(diff_text.splitlines()))
    current: ChangedFile | None = None

    for line in diff_text.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            path = file_match.group(2)
            current = ChangedFile(path=path)
            stats.files[path] = current
            continue

        if current is None:
            continue

        if HUNK_RE.match(line):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            stats.total_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            stats.total_deletions += 1

    return stats


def _paths(files: Iterable[ChangedFile]) -> list[str]:
    return sorted({file.path for file in files})


def _contains(diff_text: str, pattern: str) -> bool:
    return re.search(pattern, diff_text, re.IGNORECASE | re.MULTILINE) is not None


def build_findings(stats: DiffStats, diff_text: str) -> tuple[list[Finding], list[str]]:
    files = stats.changed_files
    paths = [file.path for file in files]
    test_files = [file for file in files if re.search(r"(^|/)(test|tests|spec|__tests__)/|(_test|\.test|\.spec)\.", file.path, re.I)]
    source_files = [file for file in files if file.ext in {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".php"}]
    findings: list[Finding] = []
    suggestions: list[str] = []

    dependency_files = [file for file in files if pathlib.Path(file.path).name.lower() in {"package-lock.json", "package.json", "poetry.lock", "requirements.txt", "gemfile.lock", "go.mod", "go.sum", "cargo.lock"}]
    if dependency_files:
        findings.append(Finding(
            "Medium",
            "Dependency surface changed",
            "Lockfile or dependency metadata changed. Confirm the version bump is intentional, audit transitive changes, and check compatibility in CI.",
            _paths(dependency_files),
        ))

    migration_files = [file for file in files if re.search(r"(migration|migrations|schema|prisma|alembic|sequelize)", file.path, re.I)]
    if migration_files:
        findings.append(Finding(
            "High",
            "Database or schema path changed",
            "Schema-adjacent changes can be hard to roll back. Verify migration order, rollback behavior, and production data compatibility.",
            _paths(migration_files),
        ))

    workflow_files = [file for file in files if file.path.startswith(".github/workflows/")]
    if workflow_files:
        findings.append(Finding(
            "Medium",
            "CI workflow modified",
            "Workflow changes can reduce coverage or alter release behavior. Review permissions, trigger scope, and secret exposure carefully.",
            _paths(workflow_files),
        ))

    if source_files and not test_files:
        findings.append(Finding(
            "Medium",
            "Source changed without tests in the diff",
            "No obvious test files changed alongside implementation files. Ask for coverage or a clear explanation if behavior changed.",
            _paths(source_files[:8]),
        ))

    if stats.total_additions + stats.total_deletions > 800 or len(files) > 20:
        findings.append(Finding(
            "Medium",
            "Large review surface",
            "The diff is broad enough that splitting the PR or adding a reviewer guide would reduce review risk.",
            _paths(files[:12]),
        ))

    if _contains(diff_text, r"\b(eval|exec|child_process|subprocess|shell=True|innerHTML|dangerouslySetInnerHTML)\b"):
        risky = [file for file in files if file.ext in {".py", ".js", ".ts", ".tsx", ".jsx"}]
        findings.append(Finding(
            "High",
            "Potential code execution or injection sink",
            "The diff contains patterns that can execute code, spawn commands, or render untrusted HTML. Confirm inputs are constrained and escaped.",
            _paths(risky) or paths[:8],
        ))

    if _contains(diff_text, r"\b(token|secret|password|api[_-]?key|private[_-]?key)\b"):
        findings.append(Finding(
            "High",
            "Credential-sensitive code touched",
            "Credential-related strings appear in the diff. Confirm no secrets are committed and that logs, errors, and tests do not leak sensitive values.",
            paths[:10],
        ))

    if _contains(diff_text, r"\b(TODO|FIXME|XXX)\b"):
        suggestions.append("Resolve or explicitly track new TODO/FIXME comments before merge.")
    if test_files:
        suggestions.append("Run the changed test files directly in addition to the full project suite.")
    if dependency_files:
        suggestions.append("Include package manager audit output or lockfile rationale in the PR description.")
    if migration_files:
        suggestions.append("Add migration rollback notes and a staging verification step.")
    if not suggestions:
        suggestions.append("Add a short reviewer note explaining the expected behavior change and validation commands.")

    return findings, suggestions


def confidence_score(stats: DiffStats, findings: list[Finding], diff_text: str) -> int:
    score = 82
    if not stats.changed_files:
        return 20
    if stats.total_additions + stats.total_deletions > 800:
        score -= 12
    if len(stats.changed_files) > 20:
        score -= 8
    if any(item.severity == "High" for item in findings):
        score -= 8
    if "Binary files " in diff_text:
        score -= 15
    return max(35, min(95, score))


def render_markdown(source: str, stats: DiffStats, findings: list[Finding], suggestions: list[str], diff_url: str | None, diff_text: str) -> str:
    changed = stats.changed_files
    file_summary = ", ".join(f"{file.path} (+{file.additions}/-{file.deletions})" for file in changed[:8])
    if len(changed) > 8:
        file_summary += f", and {len(changed) - 8} more"
    if not file_summary:
        file_summary = "No changed files detected."

    risk_level = "Low"
    if any(item.severity == "High" for item in findings):
        risk_level = "High"
    elif any(item.severity == "Medium" for item in findings):
        risk_level = "Medium"

    lines = [
        "# Claude PR Review",
        "",
        f"**Source:** {source}",
    ]
    if diff_url:
        lines.append(f"**Diff:** {diff_url}")
    lines.extend([
        "",
        "## Summary",
        f"- Changed files: {len(changed)}",
        f"- Lines changed: +{stats.total_additions} / -{stats.total_deletions}",
        f"- Review surface: {file_summary}",
        "",
        "## Risk Assessment",
        f"- Overall risk: **{risk_level}**",
    ])

    if findings:
        for item in findings:
            file_list = ", ".join(item.files) if item.files else "General diff"
            lines.extend([
                f"- **{item.severity}: {item.title}**",
                f"  - Files: {file_list}",
                f"  - Detail: {item.detail}",
            ])
    else:
        lines.append("- No high-confidence risk patterns were detected from the diff alone.")

    lines.extend(["", "## Suggested Improvements"])
    lines.extend(f"- {suggestion}" for suggestion in suggestions)

    lines.extend([
        "",
        "## Confidence",
        f"- Score: **{confidence_score(stats, findings, diff_text)}/100**",
        "- Basis: Static diff inspection only; final confidence depends on repository context and test results.",
        "",
        "## Review Metadata",
        f"- Generated at: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        f"- Diff lines inspected: {stats.raw_lines}",
        "- Tool: agents/pr-reviewer/claude-review.py",
    ])

    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR diff and output structured Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              python agents/pr-reviewer/claude-review.py --pr https://github.com/psf/requests/pull/7048
              python agents/pr-reviewer/claude-review.py --diff-file /tmp/pr.diff --output review.md
            """
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL")
    source.add_argument("--diff-file", help="Path to a unified diff file")
    parser.add_argument("--output", help="Write Markdown to this file instead of stdout")
    parser.add_argument("--max-diff-bytes", type=int, default=2_000_000, help="Maximum diff size to read")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        diff_url = None
        if args.pr:
            diff_text, diff_url = fetch_pr_diff(args.pr, args.max_diff_bytes)
            source = args.pr
        else:
            diff_text, source = read_diff_file(args.diff_file, args.max_diff_bytes)

        stats = parse_diff(diff_text)
        findings, suggestions = build_findings(stats, diff_text)
        report = render_markdown(source, stats, findings, suggestions, diff_url, diff_text)

        if args.output:
            pathlib.Path(args.output).write_text(report, encoding="utf-8")
        else:
            print(report, end="")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
