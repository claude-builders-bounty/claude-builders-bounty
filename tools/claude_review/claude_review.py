#!/usr/bin/env python3
"""Review a GitHub pull request diff and emit a structured Markdown comment."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


PR_URL = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)")
SENSITIVE_PATHS = (
    ".github/workflows/",
    "dockerfile",
    "package-lock.json",
    "requirements",
    "pyproject.toml",
    "settings",
    "config",
    "auth",
    "security",
    "hook",
    "migration",
    "database",
)
RISK_PATTERNS = (
    (re.compile(r"\beval\s*\("), "Uses eval-like execution, which needs tight input control."),
    (re.compile(r"\bexec\s*\("), "Uses dynamic execution, which can be hard to reason about safely."),
    (re.compile(r"shell\s*=\s*True"), "Runs subprocesses through a shell, increasing injection risk."),
    (re.compile(r"rm\s+-[^\n]*[rf][^\n]*", re.IGNORECASE), "Contains recursive or force deletion commands."),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "Contains destructive SQL schema operations."),
    (re.compile(r"\bDELETE\s+FROM\b(?![^\n;]*\bWHERE\b)", re.IGNORECASE), "Contains DELETE FROM without an obvious WHERE clause."),
    (re.compile(r"chmod\s+777"), "Grants world-writable permissions."),
    (re.compile(r"(api[_-]?key|secret|token|password)\s*=", re.IGNORECASE), "May introduce hard-coded secret-like values."),
)


@dataclass(frozen=True)
class ChangedFile:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    new_file: bool = False
    deleted_file: bool = False
    risky_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DiffAnalysis:
    files: tuple[ChangedFile, ...]
    additions: int
    deletions: int
    risks: tuple[str, ...]
    suggestions: tuple[str, ...]
    confidence: str


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_URL.fullmatch(url.strip().rstrip("/"))
    if not match:
        raise ValueError("expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return match.group(1), int(match.group(2))


def fetch_pr_diff(pr_url: str, max_bytes: int) -> str:
    repo, number = parse_pr_url(pr_url)
    diff_url = f"https://github.com/{repo}/pull/{number}.diff"
    request = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read(max_bytes + 1)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to fetch PR diff: {exc}") from exc
    if len(data) > max_bytes:
        raise RuntimeError(f"PR diff is larger than --max-diff-bytes ({max_bytes})")
    return data.decode("utf-8", errors="replace")


def _finalize_file(raw: dict[str, object] | None) -> ChangedFile | None:
    if not raw:
        return None
    return ChangedFile(
        path=str(raw["path"]),
        additions=int(raw.get("additions", 0)),
        deletions=int(raw.get("deletions", 0)),
        hunks=int(raw.get("hunks", 0)),
        new_file=bool(raw.get("new_file", False)),
        deleted_file=bool(raw.get("deleted_file", False)),
        risky_lines=tuple(raw.get("risky_lines", ())),
    )


def parse_diff(diff: str) -> tuple[ChangedFile, ...]:
    files: list[ChangedFile] = []
    current: dict[str, object] | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            finished = _finalize_file(current)
            if finished:
                files.append(finished)
            current = {"path": line.rsplit(" b/", 1)[-1], "risky_lines": []}
            continue
        if current is None:
            continue
        if line.startswith("+++ b/"):
            current["path"] = line[6:]
        elif line.startswith("new file mode"):
            current["new_file"] = True
        elif line.startswith("deleted file mode"):
            current["deleted_file"] = True
        elif line.startswith("@@"):
            current["hunks"] = int(current.get("hunks", 0)) + 1
        elif line.startswith("+") and not line.startswith("+++"):
            current["additions"] = int(current.get("additions", 0)) + 1
            for pattern, message in RISK_PATTERNS:
                if pattern.search(line[1:]):
                    risky = list(current.get("risky_lines", []))
                    risky.append(message)
                    current["risky_lines"] = risky
        elif line.startswith("-") and not line.startswith("---"):
            current["deletions"] = int(current.get("deletions", 0)) + 1

    finished = _finalize_file(current)
    if finished:
        files.append(finished)
    return tuple(files)


def _path_is_test(path: str) -> bool:
    lowered = path.lower()
    return "/test" in lowered or "\\test" in lowered or lowered.startswith("test") or "_test." in lowered or ".spec." in lowered


def _path_is_doc(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".md", ".rst", ".txt")) or "docs/" in lowered


def _path_is_sensitive(path: str) -> bool:
    lowered = path.lower()
    return any(marker in lowered for marker in SENSITIVE_PATHS)


def analyze_diff(diff: str) -> DiffAnalysis:
    files = parse_diff(diff)
    additions = sum(file.additions for file in files)
    deletions = sum(file.deletions for file in files)
    test_files = [file.path for file in files if _path_is_test(file.path)]
    doc_files = [file.path for file in files if _path_is_doc(file.path)]
    sensitive_files = [file.path for file in files if _path_is_sensitive(file.path)]
    deleted_files = [file.path for file in files if file.deleted_file]
    risky_messages = sorted({message for file in files for message in file.risky_lines})

    risks: list[str] = []
    if not files:
        risks.append("No changed files were found in the diff, so the review cannot validate behavior.")
    if additions + deletions > 600:
        risks.append("Large diff size makes manual review harder; split or add focused verification if possible.")
    if sensitive_files:
        risks.append("Touches sensitive paths: " + ", ".join(sensitive_files[:5]) + ".")
    if deleted_files:
        risks.append("Deletes files: " + ", ".join(deleted_files[:5]) + ".")
    risks.extend(risky_messages)
    if not test_files:
        risks.append("No test files were changed, so regression coverage may be missing.")
    if not risks:
        risks.append("No significant risks detected by the heuristic review.")

    suggestions: list[str] = []
    if not test_files:
        suggestions.append("Add or reference tests that exercise the changed behavior.")
    if doc_files and len(doc_files) == len(files):
        suggestions.append("If this is documentation-only, state that explicitly in the PR summary.")
    if sensitive_files:
        suggestions.append("Document the expected runtime behavior for sensitive configuration or hook changes.")
    if additions + deletions > 300:
        suggestions.append("Summarize the highest-risk files in the PR body to speed up reviewer validation.")
    if not suggestions:
        suggestions.append("Keep the PR body aligned with the implementation and include the exact verification command.")

    if not files or additions + deletions > 900:
        confidence = "Low"
    elif test_files and not risky_messages and additions + deletions <= 300:
        confidence = "High"
    else:
        confidence = "Medium"

    return DiffAnalysis(
        files=files,
        additions=additions,
        deletions=deletions,
        risks=tuple(risks),
        suggestions=tuple(suggestions),
        confidence=confidence,
    )


def _top_paths(files: Iterable[ChangedFile], limit: int = 4) -> str:
    paths = [file.path for file in files]
    if not paths:
        return "no files"
    if len(paths) <= limit:
        return ", ".join(paths)
    return ", ".join(paths[:limit]) + f", and {len(paths) - limit} more"


def render_markdown(analysis: DiffAnalysis, pr_url: str | None = None) -> str:
    subject = f" for {pr_url}" if pr_url else ""
    file_count = len(analysis.files)
    summary = (
        f"This review analyzed {file_count} changed file(s){subject}, with "
        f"{analysis.additions} additions and {analysis.deletions} deletions."
    )
    detail = f"The main changed paths are {_top_paths(analysis.files)}."

    lines = [
        "## PR Review",
        "",
        "### Summary",
        f"{summary} {detail}",
        "",
        "### Identified risks",
    ]
    lines.extend(f"- {risk}" for risk in analysis.risks)
    lines.extend(["", "### Improvement suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in analysis.suggestions)
    lines.extend(["", "### Confidence score", analysis.confidence, ""])
    return "\n".join(lines)


def review_diff(diff: str, pr_url: str | None = None) -> str:
    return render_markdown(analyze_diff(diff), pr_url)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Read a unified diff from this local file instead of GitHub")
    parser.add_argument("--output", help="Write the Markdown review to this file instead of stdout")
    parser.add_argument("--max-diff-bytes", type=int, default=1_000_000, help="Maximum PR diff size to download")
    args = parser.parse_args()

    try:
        if args.pr:
            diff = fetch_pr_diff(args.pr, args.max_diff_bytes)
            markdown = review_diff(diff, args.pr)
        else:
            diff = Path(args.diff_file).read_text(encoding="utf-8")
            markdown = review_diff(diff)
    except Exception as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
