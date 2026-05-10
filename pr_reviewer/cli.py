"""Generate a structured Markdown review for a GitHub pull request diff.

The implementation is intentionally dependency-free so the agent can run in a
fresh Claude Code workspace with only Python available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


GITHUB_PR_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)(?:/.*)?$"
)

TEST_RE = re.compile(r"(^|/)(tests?|__tests__)/|([._-](test|spec))\.[A-Za-z0-9]+$")
CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt", ".adoc"}
CONFIG_EXTENSIONS = {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "Gemfile",
    "Gemfile.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
}
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}"
)
DESTRUCTIVE_RE = re.compile(
    r"(?i)(rm\s+-[^\n]*(?:r[^\n]*f|f[^\n]*r)|drop\s+table|truncate\s+table|git\s+push[^\n]*--force|delete\s+from(?![^\n]*\bwhere\b)|\beval\s*\(|\bexec\s*\()"
)


@dataclass
class FileChange:
    path: str
    old_path: str = ""
    status: str = "modified"
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)

    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower()

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def is_test(self) -> bool:
        return bool(TEST_RE.search(self.path))

    @property
    def is_code(self) -> bool:
        return self.extension in CODE_EXTENSIONS

    @property
    def is_docs(self) -> bool:
        return self.extension in DOC_EXTENSIONS

    @property
    def is_config(self) -> bool:
        return self.extension in CONFIG_EXTENSIONS or self.name in DEPENDENCY_FILES


@dataclass
class Review:
    source: str
    files: list[FileChange]
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str

    @property
    def total_additions(self) -> int:
        return sum(file.additions for file in self.files)

    @property
    def total_deletions(self) -> int:
        return sum(file.deletions for file in self.files)


def parse_github_pr_url(pr_url: str) -> tuple[str, str, str]:
    match = GITHUB_PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError(
            "Expected a GitHub pull request URL like "
            "https://github.com/owner/repo/pull/123"
        )
    return match.group("owner"), match.group("repo"), match.group("number")


def diff_url_for_pr(pr_url: str) -> str:
    owner, repo, number = parse_github_pr_url(pr_url)
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_pr_diff(pr_url: str, timeout: int = 30) -> str:
    diff_url = diff_url_for_pr(pr_url)
    request = urllib.request.Request(
        diff_url,
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review-agent/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {diff_url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff from {diff_url}: {exc.reason}") from exc


def _clean_diff_path(path: str) -> str:
    path = path.strip()
    if path == "/dev/null":
        return path
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            old_path = _clean_diff_path(parts[2]) if len(parts) > 2 else ""
            new_path = _clean_diff_path(parts[3]) if len(parts) > 3 else old_path
            current = FileChange(path=new_path, old_path=old_path)
            files.append(current)
            continue

        if current is None:
            continue

        if line.startswith("new file mode"):
            current.status = "added"
        elif line.startswith("deleted file mode"):
            current.status = "deleted"
        elif line.startswith("rename from "):
            current.status = "renamed"
            current.old_path = line.removeprefix("rename from ").strip()
        elif line.startswith("rename to "):
            current.status = "renamed"
            current.path = line.removeprefix("rename to ").strip()
        elif line.startswith("--- "):
            old_path = _clean_diff_path(line.removeprefix("--- "))
            if old_path != "/dev/null":
                current.old_path = old_path
        elif line.startswith("+++ "):
            new_path = _clean_diff_path(line.removeprefix("+++ "))
            if new_path == "/dev/null":
                current.status = "deleted"
            else:
                current.path = new_path
        elif line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            current.deleted_lines.append(line[1:])

    return files


def classify_files(files: Iterable[FileChange]) -> dict[str, int]:
    buckets = {
        "code": 0,
        "tests": 0,
        "docs": 0,
        "config": 0,
        "workflows": 0,
        "database": 0,
    }
    for file in files:
        if file.is_test:
            buckets["tests"] += 1
        if file.is_code:
            buckets["code"] += 1
        if file.is_docs:
            buckets["docs"] += 1
        if file.is_config:
            buckets["config"] += 1
        if file.path.startswith(".github/workflows/"):
            buckets["workflows"] += 1
        if file.extension == ".sql" or "migration" in file.path.lower():
            buckets["database"] += 1
    return buckets


def _human_join(items: list[str]) -> str:
    if not items:
        return "general project files"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or f"{singular}s")


def build_summary(files: list[FileChange], source: str) -> list[str]:
    total_additions = sum(file.additions for file in files)
    total_deletions = sum(file.deletions for file in files)
    buckets = classify_files(files)
    touched = [
        name
        for name, count in buckets.items()
        if count and name in {"code", "tests", "docs", "config", "workflows", "database"}
    ]
    largest = sorted(files, key=lambda file: file.additions + file.deletions, reverse=True)[:3]
    largest_names = [file.path for file in largest]

    if not files:
        return [
            f"No file changes were found in {source}.",
            "The diff may be empty, unavailable, or generated from an unsupported source.",
        ]

    file_word = _plural(len(files), "file")
    path_word = _plural(len(largest_names), "path")
    verb = "is" if len(largest_names) == 1 else "are"
    return [
        (
            f"This PR changes {len(files)} {file_word} with {total_additions} additions "
            f"and {total_deletions} deletions across {_human_join(touched)}."
        ),
        f"The largest touched {path_word} {verb} {_human_join(largest_names)}.",
        "The review below focuses on merge risk, missing verification, and follow-up work that should be handled before or shortly after merge.",
    ]


def _added_text(files: Iterable[FileChange]) -> str:
    return "\n".join(line for file in files for line in file.added_lines)


def identify_risks(files: list[FileChange]) -> list[str]:
    risks: list[str] = []
    buckets = classify_files(files)
    total_delta = sum(file.additions + file.deletions for file in files)
    added_text = _added_text(files)
    code_files = [file for file in files if file.is_code and not file.is_test]
    test_files = [file for file in files if file.is_test]
    docs_only = bool(files) and all(file.is_docs for file in files)

    if not files:
        return ["No diff content was available, so behavioral risk could not be assessed."]

    if code_files and not test_files:
        risks.append(
            "Code changed without accompanying test files, so regressions may only appear during manual QA or production use."
        )
    if any(file.status == "deleted" for file in files):
        risks.append(
            "The PR deletes files; callers, imports, documentation links, or deployment references may still depend on them."
        )
    if any(file.name in DEPENDENCY_FILES for file in files):
        risks.append(
            "Dependency or lock files changed, which can affect install reproducibility and transitive package behavior."
        )
    if buckets["workflows"]:
        risks.append(
            "GitHub workflow changes can alter CI permissions, secret exposure, or release behavior."
        )
    if buckets["database"]:
        risks.append(
            "Database or migration changes need rollback and idempotency review before they are applied to shared environments."
        )
    if SECRET_RE.search(added_text):
        risks.append(
            "New lines resemble secrets or credentials; confirm they are placeholders and not live values."
        )
    if DESTRUCTIVE_RE.search(added_text):
        risks.append(
            "New commands include potentially destructive shell, SQL, or dynamic execution patterns."
        )
    if total_delta > 1200 or len(files) > 25:
        risks.append(
            "The diff is large enough that subtle behavior changes may be hard to review in one pass."
        )
    if docs_only:
        risks.append(
            "No material code risk detected; the main risk is that the documentation may drift from actual commands or behavior."
        )

    if not risks:
        risks.append(
            "No high-signal risk pattern was detected from the diff alone; still verify the changed behavior in the target app."
        )
    return risks


def build_suggestions(files: list[FileChange], risks: list[str]) -> list[str]:
    suggestions: list[str] = []
    buckets = classify_files(files)
    code_files = [file for file in files if file.is_code and not file.is_test]
    test_files = [file for file in files if file.is_test]
    docs_only = bool(files) and all(file.is_docs for file in files)

    if not files:
        return [
            "Re-run the review with a non-empty diff or a reachable GitHub PR URL.",
            "Include the command output or fetch error in the PR discussion so reviewers know what was unavailable.",
        ]

    if code_files and not test_files:
        suggestions.append(
            "Add focused tests for the changed behavior, or document the manual verification command and result in the PR."
        )
    if any(file.name in DEPENDENCY_FILES for file in files):
        suggestions.append(
            "Run a clean install from the lockfile and include the package-manager command in the PR notes."
        )
    if buckets["workflows"]:
        suggestions.append(
            "Confirm workflow permissions are least-privilege and test the workflow on a branch before relying on it for releases."
        )
    if buckets["database"]:
        suggestions.append(
            "Document the migration order, rollback plan, and whether the migration is safe to rerun."
        )
    if docs_only:
        suggestions.append(
            "Run at least one documented command or setup path to confirm the instructions still match the repository."
        )
    if any(file.status == "deleted" for file in files):
        suggestions.append(
            "Search for references to deleted paths and include the search result in the PR evidence."
        )

    suggestions.append(
        "Before merge, run the narrowest relevant checks for this repository, such as lint, typecheck, unit tests, or a smoke test."
    )
    return _dedupe(suggestions)


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def score_confidence(files: list[FileChange]) -> str:
    if not files:
        return "Low"
    total_delta = sum(file.additions + file.deletions for file in files)
    docs_only = all(file.is_docs for file in files)
    has_tests = any(file.is_test for file in files)
    has_code = any(file.is_code and not file.is_test for file in files)
    if total_delta > 2000 or len(files) > 40:
        return "Low"
    if docs_only or (has_code and has_tests and total_delta <= 700):
        return "High"
    return "Medium"


def review_diff(diff_text: str, source: str) -> Review:
    files = parse_diff(diff_text)
    risks = identify_risks(files)
    return Review(
        source=source,
        files=files,
        summary=build_summary(files, source),
        risks=risks,
        suggestions=build_suggestions(files, risks),
        confidence=score_confidence(files),
    )


def render_markdown(review: Review) -> str:
    lines = [
        "<!-- Generated by claude-review -->",
        f"Source: {review.source}",
        "",
        "## Summary",
        " ".join(review.summary),
        "",
        "## Identified Risks",
    ]
    lines.extend(f"- {risk}" for risk in review.risks)
    lines.extend(["", "## Improvement Suggestions"])
    lines.extend(f"- {suggestion}" for suggestion in review.suggestions)
    lines.extend(["", "## Confidence", review.confidence, ""])
    return "\n".join(lines)


def review_to_json(review: Review) -> str:
    payload = {
        "source": review.source,
        "summary": review.summary,
        "risks": review.risks,
        "suggestions": review.suggestions,
        "confidence": review.confidence,
        "files": [
            {
                "path": file.path,
                "old_path": file.old_path,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "hunks": file.hunks,
            }
            for file in review.files
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Review a GitHub PR diff and print a structured Markdown comment.",
        epilog=textwrap.dedent(
            """\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --diff-file ./sample.diff --output review.md
            """
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL to fetch and review.")
    source.add_argument("--diff-file", help="Local unified diff file to review.")
    parser.add_argument("--output", help="Write the review to this file instead of stdout.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.pr:
            source = args.pr
            diff_text = fetch_pr_diff(args.pr, timeout=args.timeout)
        else:
            path = Path(args.diff_file)
            source = str(path)
            diff_text = path.read_text(encoding="utf-8")

        review = review_diff(diff_text, source)
        output = review_to_json(review) if args.json else render_markdown(review)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
            if not output.endswith("\n"):
                sys.stdout.write("\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"claude-review: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
