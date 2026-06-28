from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<num>\d+)/?$")


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    removed: int
    hunks: int


@dataclass(frozen=True)
class DiffSummary:
    pr_url: str
    files: list[FileChange]
    total_added: int
    total_removed: int
    raw_diff: str


def parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("num")


def diff_url_for(pr_url: str) -> str:
    owner, repo, num = parse_pr_url(pr_url)
    return f"https://github.com/{owner}/{repo}/pull/{num}.diff"


def fetch_diff(pr_url: str) -> str:
    url = diff_url_for(pr_url)
    request = urllib.request.Request(url, headers={"User-Agent": "claude-review-cli/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch pull request diff: {exc.reason}") from exc


def parse_diff(raw_diff: str, pr_url: str) -> DiffSummary:
    files: list[FileChange] = []
    current_path: str | None = None
    added = 0
    removed = 0
    hunks = 0

    def finish_current() -> None:
        nonlocal added, removed, hunks, current_path
        if current_path is not None:
            files.append(FileChange(current_path, added, removed, hunks))
        current_path = None
        added = 0
        removed = 0
        hunks = 0

    for line in raw_diff.splitlines():
        if line.startswith("diff --git "):
            finish_current()
            parts = line.split(" b/", 1)
            current_path = parts[1] if len(parts) == 2 else line.removeprefix("diff --git ")
        elif line.startswith("@@"):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    finish_current()
    return DiffSummary(
        pr_url=pr_url,
        files=files,
        total_added=sum(file.added for file in files),
        total_removed=sum(file.removed for file in files),
        raw_diff=raw_diff,
    )


def classify_file(path: str) -> str:
    lowered = path.lower()
    if lowered.endswith((".md", ".rst", ".txt")):
        return "documentation"
    if lowered.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
        return "configuration"
    if "test" in lowered or lowered.endswith(("_test.py", ".test.ts", ".spec.ts", ".spec.js")):
        return "tests"
    if lowered.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java")):
        return "runtime code"
    return "other"


def top_files(files: Iterable[FileChange], limit: int = 5) -> list[FileChange]:
    return sorted(files, key=lambda file: file.added + file.removed, reverse=True)[:limit]


def identify_risks(summary: DiffSummary) -> list[str]:
    risks: list[str] = []
    categories = {classify_file(file.path) for file in summary.files}
    changed_paths = [file.path.lower() for file in summary.files]

    if not summary.files:
        return ["No file-level changes were detected in the fetched diff."]
    if "runtime code" in categories and "tests" not in categories:
        risks.append("Runtime code changed without obvious test file updates in this diff.")
    if any("auth" in path or "security" in path or "permission" in path for path in changed_paths):
        risks.append("Security- or permission-adjacent files changed; review authorization and failure paths carefully.")
    if any(path.endswith((".yml", ".yaml")) and (".github/workflows" in path or "deploy" in path) for path in changed_paths):
        risks.append("Workflow or deployment configuration changed; verify secrets handling and trigger scope.")
    if summary.total_added + summary.total_removed > 800:
        risks.append("Large diff size increases review risk; consider splitting or requesting focused reviewer attention.")
    if all(classify_file(file.path) == "documentation" for file in summary.files):
        risks.append("Documentation-only change; primary risk is stale or misleading guidance rather than runtime behavior.")
    if not risks:
        risks.append("No high-signal structural risk detected from the diff metadata alone.")
    return risks


def suggest_improvements(summary: DiffSummary) -> list[str]:
    suggestions: list[str] = []
    categories = {classify_file(file.path) for file in summary.files}

    if "runtime code" in categories:
        suggestions.append("Add or link targeted tests that exercise the changed runtime behavior.")
    if "configuration" in categories:
        suggestions.append("Document how the configuration change was validated in a local or CI environment.")
    if "documentation" in categories:
        suggestions.append("Check links, headings, and examples so readers can follow the updated guidance.")
    if summary.total_added + summary.total_removed > 400:
        suggestions.append("Add a concise PR description that calls out the main files and review order.")
    suggestions.append("Include manual verification notes or screenshots when behavior is user-facing.")
    return suggestions


def confidence(summary: DiffSummary) -> str:
    if not summary.files:
        return "Low"
    if summary.total_added + summary.total_removed > 800:
        return "Low"
    if any(classify_file(file.path) == "runtime code" for file in summary.files):
        return "Medium"
    return "High"


def render_review(summary: DiffSummary) -> str:
    changed_count = len(summary.files)
    largest = top_files(summary.files)
    categories = sorted({classify_file(file.path) for file in summary.files})
    category_text = ", ".join(categories) if categories else "none"

    lines = [
        "## Summary of changes",
        "",
        (
            f"This PR changes {changed_count} file(s), with {summary.total_added} added line(s) "
            f"and {summary.total_removed} removed line(s). The detected change areas are: {category_text}."
        ),
        (
            "The largest files in the diff are "
            + (", ".join(f"`{file.path}`" for file in largest) if largest else "not available")
            + "."
        ),
        "",
        "## Identified risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in identify_risks(summary))
    lines.extend(["", "## Improvement suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in suggest_improvements(summary))
    lines.extend(["", f"## Confidence score: {confidence(summary)}", ""])
    lines.append(
        "This review is based on diff metadata and lightweight heuristics; it should complement, not replace, a human review."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request diff and print structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL, e.g. https://github.com/owner/repo/pull/123")
    args = parser.parse_args(argv)

    try:
        raw_diff = fetch_diff(args.pr)
        summary = parse_diff(raw_diff, args.pr)
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2

    print(render_review(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
