"""Deterministic Markdown review generation."""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath

from .diff import FileChange, parse_unified_diff
from .github import PullRequestData


TEST_MARKERS = (
    "test",
    "tests/",
    "__tests__/",
    "spec.",
    ".spec.",
    "_test.",
    "test_",
)
DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "Gemfile",
    "Gemfile.lock",
}
GENERATED_MARKERS = (
    "dist/",
    "build/",
    "coverage/",
    "vendor/",
    "generated/",
    ".min.js",
    ".lock",
)
SECURITY_MARKERS = (
    "auth",
    "password",
    "token",
    "secret",
    "credential",
    "permission",
    "crypto",
)
MIGRATION_MARKERS = ("migration", "migrations/", "schema", "sql")
CI_MARKERS = (".github/workflows/", ".gitlab-ci", "circleci", "jenkins")


def render_review(pr: PullRequestData) -> str:
    files = parse_unified_diff(pr.diff)
    additions = pr.additions or sum(file.additions for file in files)
    deletions = pr.deletions or sum(file.deletions for file in files)
    changed_files = pr.changed_files or len(files)
    total_delta = additions + deletions

    risks = _risks(pr, files, changed_files, additions, deletions)
    suggestions = _suggestions(pr, files, risks, total_delta)
    confidence = _confidence(files, total_delta, risks)

    lines = [
        "# Claude Review",
        "",
        "## Summary of Changes",
        f"- PR: [{pr.ref.owner}/{pr.ref.repo}#{pr.ref.number}]({pr.ref.url}) - {_clean(pr.title) or 'Untitled'}",
        f"- Author: `{pr.author}`; state: `{pr.state.lower()}`; base/head: `{pr.base_ref or '?'} <- {pr.head_ref or '?'}`",
        f"- Scope: {changed_files} file(s), +{additions}/-{deletions} lines, fetched via `{pr.fetch_source}`.",
    ]

    file_summary = _file_summary(files)
    if file_summary:
        lines.append(f"- Changed areas: {file_summary}.")
    if pr.is_draft:
        lines.append("- PR is marked as draft.")

    lines.extend(["", "## Risks"])
    lines.extend(f"- {risk}" for risk in risks)

    lines.extend(["", "## Improvement Suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in suggestions)

    lines.extend(["", "## Confidence", confidence])
    return "\n".join(lines)


def _risks(
    pr: PullRequestData,
    files: list[FileChange],
    changed_files: int,
    additions: int,
    deletions: int,
) -> list[str]:
    risks: list[str] = []
    total_delta = additions + deletions
    paths = [file.path for file in files]
    lowered_paths = [path.lower() for path in paths]

    if not files:
        risks.append("No parseable diff was available, so review depth is limited to metadata.")
        return risks

    if changed_files >= 25 or total_delta >= 1200:
        risks.append(
            "Large change size increases review risk; split or add strong validation evidence where possible."
        )
    elif changed_files >= 10 or total_delta >= 400:
        risks.append("Moderate change size may hide integration issues across touched files.")

    if any(file.is_binary for file in files):
        risks.append("Binary file changes cannot be meaningfully reviewed from the text diff.")

    if any(file.is_deleted for file in files) or deletions > additions * 2 and deletions > 50:
        risks.append("Substantial deletions may remove behavior or compatibility paths.")

    if _touches(lowered_paths, SECURITY_MARKERS):
        risks.append("Security-sensitive paths or identifiers changed; verify auth, secret handling, and permissions.")

    if _touches(lowered_paths, MIGRATION_MARKERS):
        risks.append("Schema or migration-related files changed; confirm rollback and data compatibility.")

    if _touches(lowered_paths, CI_MARKERS):
        risks.append("CI/workflow changes can affect release gates or repository permissions.")

    if any(PurePosixPath(path).name in DEPENDENCY_FILES for path in paths):
        risks.append("Dependency or lockfile changes can alter runtime behavior beyond the visible source diff.")

    has_code = any(_looks_like_code(path) for path in paths)
    has_tests = any(_is_test_path(path) for path in lowered_paths)
    if has_code and not has_tests:
        risks.append("Code changed without obvious test updates in the diff.")

    if pr.is_draft:
        risks.append("Draft status suggests the author may still be iterating.")

    if not risks:
        risks.append("No major heuristic risks detected from the diff.")
    return risks


def _suggestions(
    pr: PullRequestData,
    files: list[FileChange],
    risks: list[str],
    total_delta: int,
) -> list[str]:
    suggestions: list[str] = []
    paths = [file.path for file in files]
    lowered_paths = [path.lower() for path in paths]

    if any("test" in risk.lower() for risk in risks):
        suggestions.append("Add or point to focused tests that cover the changed behavior.")
    if any("dependency" in risk.lower() for risk in risks):
        suggestions.append("Document why dependency changes are needed and verify lockfile consistency.")
    if any("security" in risk.lower() for risk in risks):
        suggestions.append("Include explicit validation for authorization boundaries and secret redaction.")
    if any("schema" in risk.lower() or "migration" in risk.lower() for risk in risks):
        suggestions.append("Call out migration order, rollback behavior, and compatibility with existing data.")
    if any("ci/workflow" in risk.lower() for risk in risks):
        suggestions.append("Confirm workflow permissions and required checks still match the repository policy.")
    if total_delta >= 400:
        suggestions.append("Consider splitting mechanical or generated changes from behavior changes.")
    if any(_is_generated_path(path) for path in lowered_paths):
        suggestions.append("Identify generated artifacts and the command used to regenerate them.")
    if pr.body.strip() == "":
        suggestions.append("Fill in the PR description with intent, validation, and rollout notes.")

    if not suggestions:
        suggestions.append("Keep the PR description current with validation steps and any reviewer context.")
        suggestions.append("Run the repository's normal test and lint suite before merge.")
    return _dedupe(suggestions)


def _confidence(files: list[FileChange], total_delta: int, risks: list[str]) -> str:
    if not files or any(file.is_binary for file in files) or total_delta >= 1200:
        return "Low"
    high_risk_count = sum(
        1
        for risk in risks
        if any(word in risk.lower() for word in ("security", "schema", "ci/workflow", "large"))
    )
    if total_delta <= 200 and len(files) <= 6 and high_risk_count == 0:
        return "High"
    if high_risk_count >= 2 or total_delta >= 600:
        return "Low"
    return "Medium"


def _file_summary(files: list[FileChange]) -> str:
    if not files:
        return ""

    extensions = Counter(file.extension for file in files)
    top_extensions = ", ".join(
        f"{extension} x{count}" for extension, count in extensions.most_common(4)
    )
    top_paths = ", ".join(file.path for file in files[:5])
    if len(files) > 5:
        top_paths += f", and {len(files) - 5} more"
    return f"{top_extensions}; {top_paths}"


def _touches(paths: list[str], markers: tuple[str, ...]) -> bool:
    return any(marker in path for path in paths for marker in markers)


def _is_test_path(path: str) -> bool:
    return any(marker in path for marker in TEST_MARKERS)


def _is_generated_path(path: str) -> bool:
    return any(marker in path for marker in GENERATED_MARKERS)


def _looks_like_code(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".rb",
        ".java",
        ".kt",
        ".php",
        ".cs",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
        ".swift",
    }


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _clean(value: str) -> str:
    return " ".join(value.split())
