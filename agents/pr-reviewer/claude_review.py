#!/usr/bin/env python3
"""Heuristic PR diff reviewer that emits structured Markdown."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
import urllib.request


@dataclass
class ChangedFile:
    path: str
    old_path: str = ""
    added: int = 0
    deleted: int = 0
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)
    status: str = "modified"
    binary: bool = False


@dataclass
class ParsedDiff:
    files: list[ChangedFile]
    raw_line_count: int


@dataclass
class ReviewResult:
    pr_url: str | None
    files: list[ChangedFile]
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str
    notes: list[str]


def parse_diff(diff_text: str) -> ParsedDiff:
    files: list[ChangedFile] = []
    current: ChangedFile | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            old_path = _strip_git_prefix(parts[2]) if len(parts) > 2 else ""
            new_path = _strip_git_prefix(parts[3]) if len(parts) > 3 else old_path
            current = ChangedFile(path=new_path, old_path=old_path)
            files.append(current)
            continue

        if current is None:
            continue

        if line.startswith("new file mode"):
            current.status = "added"
        elif line.startswith("deleted file mode"):
            current.status = "deleted"
        elif line.startswith("similarity index") or line.startswith("rename from "):
            current.status = "renamed"
        elif line.startswith("Binary files "):
            current.binary = True
        elif line.startswith("--- "):
            current.old_path = _normalize_diff_path(line[4:])
        elif line.startswith("+++ "):
            new_path = _normalize_diff_path(line[4:])
            if new_path != "/dev/null":
                current.path = new_path
        elif line.startswith("+") and not line.startswith("+++"):
            current.added += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deleted += 1
            current.deleted_lines.append(line[1:])

    return ParsedDiff(files=files, raw_line_count=len(diff_text.splitlines()))


def analyze_diff(parsed: ParsedDiff, pr_url: str | None = None) -> ReviewResult:
    risks: list[str] = []
    suggestions: list[str] = []
    notes: list[str] = []

    files = parsed.files
    total_added = sum(item.added for item in files)
    total_deleted = sum(item.deleted for item in files)
    changed_paths = {item.path for item in files}
    added_text_by_file = {item.path: "\n".join(item.added_lines) for item in files}
    summary = [
        f"This PR changes {len(files)} file(s), adding {total_added} line(s) and deleting {total_deleted} line(s).",
        _summarize_file_mix(files),
    ]

    if not files:
        risks.append("No changed files were found in the provided diff; the review may have received an empty or unsupported input.")

    if len(files) > 12 or total_added + total_deleted > 800:
        risks.append("Large diff size reduces review precision; split or add focused reviewer notes for high-risk areas.")

    if any(item.binary for item in files):
        risks.append("Binary changes cannot be inspected by this text-only reviewer.")

    tests_changed = any(_is_test_path(path) for path in changed_paths)
    docs_changed = any(_is_doc_path(path) for path in changed_paths)

    for item in files:
        path = item.path
        added = added_text_by_file[path]
        lower_added = added.lower()

        if path.startswith(".github/workflows/"):
            if "pull_request_target" in added:
                risks.append(f"{path} adds `pull_request_target`, which can expose elevated permissions to forked PR code.")
            if "secrets." in added or "secrets[" in added:
                risks.append(f"{path} references GitHub secrets; verify they are unavailable to untrusted fork code paths.")
            if "permissions:" not in added:
                suggestions.append(f"Declare minimal `permissions:` in {path} so workflow tokens are least-privilege.")

        if _looks_like_shell(item):
            if "set -euo pipefail" not in added:
                suggestions.append(f"Add `set -euo pipefail` to {path} to fail fast on shell errors and unset variables.")
            if re.search(r"\brm\s+-rf\b", added):
                risks.append(f"{path} includes `rm -rf`; ensure the target path is validated and cannot expand unexpectedly.")
            if re.search(r"curl\b.*\|\s*(ba)?sh\b", lower_added):
                risks.append(f"{path} uses `curl | bash`; pin and verify downloaded scripts before execution.")

        if path.endswith((".js", ".jsx", ".ts", ".tsx")):
            if "dangerouslysetinnerhtml" in lower_added:
                risks.append(f"{path} uses `dangerouslySetInnerHTML`; ensure content is sanitized before rendering.")
            if re.search(r"\beval\s*\(", added):
                risks.append(f"{path} introduces `eval`; prefer a parser or explicit command map.")
            if re.search(r":\s*any\b|as\s+any\b", added):
                suggestions.append(f"Replace broad `any` usage in {path} with narrower types before relying on the review.")

        if path.endswith(".py"):
            if re.search(r"except\s+Exception\s*:", added):
                suggestions.append(f"Narrow broad `except Exception` handling in {path} or re-raise with context.")
            if re.search(r"subprocess\.[a-z_]+\([^\\n]*shell=True", added):
                risks.append(f"{path} calls subprocess with `shell=True`; pass argv lists where possible.")

        if _looks_like_database_change(path):
            risks.append(f"{path} appears to change database schema or SQL; verify migrations are reversible and covered by tests.")

    if not tests_changed and any(_is_code_path(path) for path in changed_paths):
        suggestions.append("Add or update tests for the changed code paths before merging.")

    if not docs_changed and any(path.startswith("agents/") or path.startswith("scripts/") for path in changed_paths):
        suggestions.append("Document command setup, inputs, and expected output for new automation or agent code.")

    if not risks:
        risks.append("No obvious high-risk patterns were detected by the heuristic diff scan.")

    if not suggestions:
        suggestions.append("No targeted improvements were detected beyond normal maintainer review.")

    notes.append("This is a deterministic heuristic review of the diff, not a substitute for running the project test suite.")
    notes.append("Confidence reflects diff size and detectable risk signals, not semantic understanding of the whole repository.")

    confidence = _confidence_for(files, risks, total_added + total_deleted)
    return ReviewResult(
        pr_url=pr_url,
        files=files,
        summary=summary,
        risks=_dedupe(risks),
        suggestions=_dedupe(suggestions),
        confidence=confidence,
        notes=notes,
    )


def render_review(result: ReviewResult) -> str:
    lines: list[str] = ["# Claude PR Review", ""]

    if result.pr_url:
        lines.extend([f"PR: {result.pr_url}", ""])

    lines.extend(["## Summary", ""])
    for sentence in result.summary:
        lines.append(sentence)
    lines.append("")

    lines.extend(["## Files Changed", ""])
    for item in result.files:
        binary_note = " binary" if item.binary else ""
        lines.append(f"- `{item.path}` ({item.status}, +{item.added}/-{item.deleted}{binary_note})")
    if not result.files:
        lines.append("- No files detected.")
    lines.append("")

    lines.extend(["## Identified Risks", ""])
    lines.extend(_bullet_list(result.risks))
    lines.append("")

    lines.extend(["## Improvement Suggestions", ""])
    lines.extend(_bullet_list(result.suggestions))
    lines.append("")

    lines.extend(["## Confidence Score", "", result.confidence, ""])

    lines.extend(["## Review Notes", ""])
    lines.extend(_bullet_list(result.notes))
    lines.append("")

    return "\n".join(lines)


def fetch_pr_diff(pr_url: str) -> str:
    diff_url = _pr_url_to_diff_url(pr_url)
    request = urllib.request.Request(
        diff_url,
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review-agent",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and emit structured Markdown.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Path to a local unified diff file")
    parser.add_argument("--output", "-o", help="Write Markdown review to this file instead of stdout")
    args = parser.parse_args(argv)

    if args.pr:
        diff_text = fetch_pr_diff(args.pr)
        pr_url = args.pr
    else:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        pr_url = None

    review = render_review(analyze_diff(parse_diff(diff_text), pr_url=pr_url))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)
    return 0


def _strip_git_prefix(path: str) -> str:
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def _normalize_diff_path(path: str) -> str:
    path = path.strip()
    if path == "/dev/null":
        return path
    return _strip_git_prefix(path)


def _summarize_file_mix(files: list[ChangedFile]) -> str:
    if not files:
        return "There are no file-level changes to summarize."

    buckets: list[str] = []
    if any(item.path.startswith(".github/workflows/") for item in files):
        buckets.append("GitHub Actions workflow")
    if any(_looks_like_shell(item) for item in files):
        buckets.append("shell automation")
    if any(item.path.endswith((".js", ".jsx", ".ts", ".tsx")) for item in files):
        buckets.append("JavaScript/TypeScript")
    if any(item.path.endswith(".py") for item in files):
        buckets.append("Python")
    if any(_is_doc_path(item.path) for item in files):
        buckets.append("documentation")
    if any(_looks_like_database_change(item.path) for item in files):
        buckets.append("database")

    if not buckets:
        return "The diff touches files outside the built-in language and workflow categories."

    return "The main areas touched are " + ", ".join(buckets) + "."


def _looks_like_shell(item: ChangedFile) -> bool:
    return item.path.endswith((".sh", ".bash")) or any(line.startswith("#!") and "sh" in line for line in item.added_lines[:2])


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in ("/test", "tests/", "__tests__", ".test.", ".spec."))


def _is_doc_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".md", ".mdx", ".rst", ".txt")) or lowered.startswith("docs/")


def _is_code_path(path: str) -> bool:
    return path.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".sh", ".bash"))


def _looks_like_database_change(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith(".sql") or "migration" in lowered or "schema" in lowered


def _confidence_for(files: list[ChangedFile], risks: list[str], churn: int) -> str:
    if not files or churn > 800 or len(files) > 20 or any(item.binary for item in files):
        return "Low"
    if any("No obvious high-risk" not in item for item in risks):
        return "Medium"
    return "High"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None."]


def _pr_url_to_diff_url(pr_url: str) -> str:
    if pr_url.endswith(".diff"):
        return pr_url
    cleaned = pr_url.rstrip("/")
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/pull/\d+$", cleaned):
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    return cleaned + ".diff"


if __name__ == "__main__":
    raise SystemExit(run())
