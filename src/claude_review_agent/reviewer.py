from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangedFile:
    path: str
    additions: int
    deletions: int


@dataclass(frozen=True)
class ReviewInput:
    number: int
    title: str
    author: str
    url: str
    base_ref: str
    head_ref: str
    additions: int
    deletions: int
    changed_files: int
    body: str
    diff: str

    @classmethod
    def from_payload(cls, payload: dict[str, object], diff: str) -> "ReviewInput":
        author = payload.get("author")
        login = author.get("login") if isinstance(author, dict) else None
        return cls(
            number=int(payload.get("number", 0) or 0),
            title=str(payload.get("title", "Untitled PR")),
            author=str(login or "unknown"),
            url=str(payload.get("url", "")),
            base_ref=str(payload.get("baseRefName", "")),
            head_ref=str(payload.get("headRefName", "")),
            additions=int(payload.get("additions", 0) or 0),
            deletions=int(payload.get("deletions", 0) or 0),
            changed_files=int(payload.get("changedFiles", 0) or 0),
            body=str(payload.get("body", "") or ""),
            diff=diff,
        )


@dataclass(frozen=True)
class DiffStats:
    files: list[ChangedFile]
    extensions: Counter[str]
    added_lines: list[str]
    deleted_lines: list[str]
    has_tests: bool
    has_docs: bool
    has_workflow: bool
    has_config: bool


def render_review(pr: ReviewInput) -> str:
    stats = analyze_diff(pr.diff)
    risks = identify_risks(pr, stats)
    suggestions = identify_suggestions(pr, stats, risks)
    confidence = confidence_score(pr, stats, risks)

    return "\n".join(
        [
            f"# PR Review: #{pr.number} {pr.title}",
            "",
            "## Summary of Changes",
            summary(pr, stats),
            "",
            "## Identified Risks",
            bullet_list(risks),
            "",
            "## Improvement Suggestions",
            bullet_list(suggestions),
            "",
            f"## Confidence Score: {confidence}",
            "",
            review_metadata(pr, stats),
            "",
        ]
    )


def analyze_diff(diff: str) -> DiffStats:
    files: list[ChangedFile] = []
    extensions: Counter[str] = Counter()
    added_lines: list[str] = []
    deleted_lines: list[str] = []
    current_path = ""
    additions = 0
    deletions = 0

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if current_path:
                files.append(ChangedFile(current_path, additions, deletions))
                extensions[file_extension(current_path)] += 1
            current_path = parse_diff_path(line)
            additions = 0
            deletions = 0
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
            added_lines.append(line[1:])
        elif line.startswith("-"):
            deletions += 1
            deleted_lines.append(line[1:])

    if current_path:
        files.append(ChangedFile(current_path, additions, deletions))
        extensions[file_extension(current_path)] += 1

    changed_paths = [file.path.lower() for file in files]
    return DiffStats(
        files=files,
        extensions=extensions,
        added_lines=added_lines,
        deleted_lines=deleted_lines,
        has_tests=any(is_test_path(path) for path in changed_paths),
        has_docs=any(path.endswith((".md", ".rst", ".txt")) or "docs/" in path for path in changed_paths),
        has_workflow=any(".github/workflows/" in path for path in changed_paths),
        has_config=any(
            path.endswith((".yml", ".yaml", ".json", ".toml", ".ini", ".env.example"))
            for path in changed_paths
        ),
    )


def is_docs_only(stats: DiffStats) -> bool:
    return bool(stats.files) and all(
        file.path.lower().endswith((".md", ".rst", ".txt")) or "docs/" in file.path.lower()
        for file in stats.files
    )


def parse_diff_path(line: str) -> str:
    parts = line.split()
    if len(parts) >= 4:
        return parts[3].removeprefix("b/")
    return "unknown"


def file_extension(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return "[no extension]"
    return "." + name.rsplit(".", 1)[-1]


def is_test_path(path: str) -> bool:
    return (
        "/test/" in path
        or "/tests/" in path
        or path.startswith("test/")
        or path.startswith("tests/")
        or path.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"))
    )


def summary(pr: ReviewInput, stats: DiffStats) -> str:
    dominant = ", ".join(f"{ext} ({count})" for ext, count in stats.extensions.most_common(3))
    if not dominant:
        dominant = "no parsed file extensions"

    return (
        f"This PR changes {pr.changed_files or len(stats.files)} file(s) with "
        f"{pr.additions} additions and {pr.deletions} deletions, primarily across {dominant}. "
        f"The branch `{pr.head_ref}` targets `{pr.base_ref}` and appears focused on {focus_area(stats)}."
    )


def focus_area(stats: DiffStats) -> str:
    paths = " ".join(file.path.lower() for file in stats.files)
    if stats.has_workflow:
        return "automation or CI workflow updates"
    if stats.has_tests and len(stats.files) <= 3:
        return "test coverage and validation changes"
    if any(part in paths for part in ("src/", "lib/", "app/", "crates/")):
        return "application or library code"
    if stats.has_docs:
        return "documentation and usage guidance"
    if stats.has_config:
        return "configuration changes"
    return "repository content changes"


def identify_risks(pr: ReviewInput, stats: DiffStats) -> list[str]:
    risks: list[str] = []
    diff_text = "\n".join(stats.added_lines).lower()

    if pr.changed_files > 12 or len(stats.files) > 12:
        risks.append("Broad change set touches many files, increasing review and regression risk.")
    if pr.additions + pr.deletions > 800:
        risks.append("Large diff size may hide behavioral regressions without targeted tests.")
    docs_only = is_docs_only(stats)

    if not stats.has_tests and not docs_only:
        risks.append("No test files were changed, so the new behavior may not be covered by automated checks.")
    if stats.has_workflow:
        risks.append("Workflow changes can affect CI permissions, secrets exposure, or release behavior.")
    if re.search(r"\b(token|secret|password|api[_-]?key)\b", diff_text):
        risks.append("Added lines reference credentials or secret-like values; confirm they are placeholders or environment variables.")
    if re.search(r"\bsubprocess|exec\(|eval\(|shell=true\b", diff_text):
        risks.append("Added command execution path needs input validation and clear failure handling.")
    if re.search(r"\bdelete\s+from\b|\bdrop\s+table\b|\btruncate\b", diff_text):
        risks.append("Added SQL mutation statements need safeguards to avoid destructive operations.")
    if not risks:
        risks.append("No high-risk patterns were detected from the diff metadata and changed paths.")
    return risks


def identify_suggestions(pr: ReviewInput, stats: DiffStats, risks: list[str]) -> list[str]:
    suggestions: list[str] = []

    docs_only = is_docs_only(stats)

    if not stats.has_tests and not docs_only:
        suggestions.append("Add a focused test or fixture that exercises the main changed behavior.")
    if not stats.has_docs:
        suggestions.append("Add or update README/docs so users know how to run and verify the change.")
    if any("credential" in risk or "secret" in risk for risk in risks):
        suggestions.append("Replace any real credential-looking values with documented environment variables.")
    if any("command execution" in risk for risk in risks):
        suggestions.append("Validate command inputs and cover failure paths for subprocess execution.")
    if pr.body.strip() == "":
        suggestions.append("Fill in the PR description with intent, test evidence, and rollout notes.")
    if not suggestions:
        suggestions.append("Keep the PR focused and include the exact verification commands in the PR description.")
    return suggestions


def confidence_score(pr: ReviewInput, stats: DiffStats, risks: list[str]) -> str:
    if "No high-risk patterns" in risks[0] and (stats.has_tests or is_docs_only(stats)) and pr.changed_files <= 6:
        return "High"
    if stats.has_tests or pr.changed_files <= 8:
        return "Medium"
    return "Low"


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def review_metadata(pr: ReviewInput, stats: DiffStats) -> str:
    file_list = ", ".join(file.path for file in stats.files[:6])
    if len(stats.files) > 6:
        file_list += f", and {len(stats.files) - 6} more"
    if not file_list:
        file_list = "No files parsed from diff"
    return (
        "<sub>"
        f"Reviewed {file_list}. "
        f"Source: {pr.url or 'offline fixture'}."
        "</sub>"
    )
