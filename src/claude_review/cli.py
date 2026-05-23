from __future__ import annotations

import argparse
import dataclasses
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib import error, request


PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)/?$"
)
DIFF_FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
HUNK_RE = re.compile(r"^@@")
SOURCE_RE = re.compile(r"\.(py|js|jsx|ts|tsx|go|rs|java|rb|php|cs|cpp|c|h|hpp|swift|kt)$")
TEST_RE = re.compile(r"(^|/)(test|tests|spec|specs|__tests__)(/|$)|(_test|\.test|\.spec)\.")
DOC_RE = re.compile(r"\.(md|mdx|rst|txt)$|(^|/)docs?/")
UI_RE = re.compile(r"\.(css|scss|sass|less|html|jsx|tsx|vue|svelte)$")
CONFIG_RE = re.compile(r"(^|/)(package\.json|pyproject\.toml|requirements.*\.txt|poetry\.lock|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|go\.mod|go\.sum|Cargo\.toml|Cargo\.lock)$|(^|/)\.github/workflows/")
SECURITY_RE = re.compile(
    r"\b(auth|oauth|jwt|token|secret|password|credential|permission|rbac|session|cookie|csrf|cors|crypto|encrypt|decrypt)\b",
    re.I,
)
DATABASE_RE = re.compile(r"\b(sql|migration|schema|database|postgres|mysql|sqlite|redis|transaction)\b", re.I)


@dataclasses.dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def diff_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}.diff"

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


@dataclasses.dataclass
class FileChange:
    old_path: str
    new_path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    added_lines: list[str] = dataclasses.field(default_factory=list)
    removed_lines: list[str] = dataclasses.field(default_factory=list)

    @property
    def path(self) -> str:
        return self.new_path if self.new_path != "/dev/null" else self.old_path

    @property
    def changed_lines(self) -> int:
        return self.additions + self.deletions


@dataclasses.dataclass
class Review:
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str
    files: list[FileChange]
    additions: int
    deletions: int


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")

    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
    )


def fetch_pr_diff(ref: PullRequestRef) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-reviewer/0.1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(ref.diff_url, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching {ref.diff_url}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not fetch {ref.diff_url}: {exc}") from exc


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        file_match = DIFF_FILE_RE.match(line)
        if file_match:
            current = FileChange(old_path=file_match.group(1), new_path=file_match.group(2))
            files.append(current)
            continue

        if current is None:
            continue

        if line.startswith("+++ b/"):
            current.new_path = line.removeprefix("+++ b/")
            continue
        if line.startswith("--- a/"):
            current.old_path = line.removeprefix("--- a/")
            continue
        if HUNK_RE.match(line):
            current.hunks += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
            continue
        if line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            current.removed_lines.append(line[1:])

    return files


def has_match(files: Iterable[FileChange], pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(file.path) for file in files)


def format_file_list(files: list[FileChange], limit: int = 5) -> str:
    names = [file.path for file in files[:limit]]
    suffix = "" if len(files) <= limit else f", and {len(files) - limit} more"
    return ", ".join(f"`{name}`" for name in names) + suffix


def plural(count: int, singular: str, plural_word: str | None = None) -> str:
    word = singular if count == 1 else plural_word or f"{singular}s"
    return f"{count} {word}"


def analyze_diff(diff_text: str) -> Review:
    files = parse_diff(diff_text)
    additions = sum(file.additions for file in files)
    deletions = sum(file.deletions for file in files)
    changed_lines = additions + deletions
    code_files = [file for file in files if SOURCE_RE.search(file.path)]
    test_files = [file for file in files if TEST_RE.search(file.path)]
    doc_files = [file for file in files if DOC_RE.search(file.path)]
    config_files = [file for file in files if CONFIG_RE.search(file.path)]
    ui_files = [file for file in files if UI_RE.search(file.path)]

    summary = build_summary(files, code_files, test_files, doc_files, additions, deletions)
    risks: list[str] = []
    suggestions: list[str] = []

    if not files:
        risks.append("No file-level changes were found in the diff, so the review may be incomplete.")
        suggestions.append("Re-run the review with a full GitHub PR URL or an untruncated `.diff` file.")
        return Review(summary, risks, suggestions, "Low", files, additions, deletions)

    if changed_lines > 800:
        risks.append(f"Large change set ({changed_lines} changed lines) raises review risk and may hide regressions.")
        suggestions.append("Split the PR or add a reviewer guide that explains the riskiest files first.")
    elif changed_lines > 300:
        risks.append(f"Medium-sized change set ({changed_lines} changed lines) needs focused regression testing.")

    if code_files and not test_files:
        risks.append("Production code changed without an accompanying test file.")
        suggestions.append("Add or update tests that cover the changed behavior before merge.")

    if config_files:
        risks.append(f"Build, dependency, or workflow configuration changed in {format_file_list(config_files)}.")
        suggestions.append("Run the full CI matrix and check lockfile or workflow changes for supply-chain impact.")

    security_touched = [
        file
        for file in files
        if SECURITY_RE.search(file.path)
        or any(SECURITY_RE.search(line) for line in file.added_lines + file.removed_lines)
    ]
    if security_touched:
        risks.append(f"Security-sensitive logic or naming appears in {format_file_list(security_touched)}.")
        suggestions.append("Confirm auth, permissions, secrets handling, and error paths with targeted tests.")

    database_touched = [
        file
        for file in files
        if DATABASE_RE.search(file.path)
        or any(DATABASE_RE.search(line) for line in file.added_lines + file.removed_lines)
    ]
    if database_touched:
        risks.append(f"Database or persistence behavior appears to change in {format_file_list(database_touched)}.")
        suggestions.append("Document migration, rollback, and data compatibility expectations.")

    if ui_files:
        suggestions.append("Include screenshots or recordings for UI-visible changes.")

    if doc_files and len(doc_files) == len(files):
        risks.append("Documentation-only change; implementation risk is low, but accuracy depends on project context.")
        suggestions.append("Ask a maintainer or domain owner to confirm the wording matches current behavior.")

    if not risks:
        risks.append("No obvious structural risks detected from the diff alone.")
    if not suggestions:
        suggestions.append("Keep the PR description focused on behavior changed, tests run, and rollout notes.")

    confidence = confidence_for(files, changed_lines, test_files, security_touched)
    return Review(summary, risks, suggestions, confidence, files, additions, deletions)


def build_summary(
    files: list[FileChange],
    code_files: list[FileChange],
    test_files: list[FileChange],
    doc_files: list[FileChange],
    additions: int,
    deletions: int,
) -> list[str]:
    if not files:
        return ["The supplied diff did not contain recognizable file changes."]

    file_sentence = (
        f"This PR changes {plural(len(files), 'file')} with "
        f"{plural(additions, 'addition')} and {plural(deletions, 'deletion')}."
    )
    areas: list[str] = []
    if code_files:
        areas.append(plural(len(code_files), "source file"))
    if test_files:
        areas.append(plural(len(test_files), "test file"))
    if doc_files:
        areas.append(plural(len(doc_files), "documentation file"))

    if areas:
        area_sentence = "The main touched areas are " + ", ".join(areas) + "."
    else:
        area_sentence = "The touched files are mostly configuration, generated, or non-source assets."

    focus_sentence = f"Highest-review files: {format_file_list(sorted(files, key=lambda f: f.changed_lines, reverse=True), 4)}."
    return [file_sentence, area_sentence, focus_sentence]


def confidence_for(
    files: list[FileChange],
    changed_lines: int,
    test_files: list[FileChange],
    security_touched: list[FileChange],
) -> str:
    if not files or changed_lines > 800 or security_touched:
        return "Low"
    if changed_lines <= 250 and test_files:
        return "High"
    return "Medium"


def render_markdown(review: Review, source: str) -> str:
    lines: list[str] = []
    lines.append("# PR Review")
    lines.append("")
    lines.append(f"Source: {source}")
    lines.append("")
    lines.append("## Summary of Changes")
    lines.append("")
    for sentence in review.summary[:3]:
        lines.append(f"- {sentence}")
    lines.append("")
    lines.append("## Identified Risks")
    lines.append("")
    for risk in review.risks:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("## Improvement Suggestions")
    lines.append("")
    for suggestion in review.suggestions:
        lines.append(f"- {suggestion}")
    lines.append("")
    lines.append(f"## Confidence Score: {review.confidence}")
    lines.append("")
    lines.append(
        f"Reviewed {plural(len(review.files), 'file')}, {plural(review.additions, 'addition')}, "
        f"and {plural(review.deletions, 'deletion')}. Confidence is based on diff size, "
        "test coverage signals, and sensitive-area heuristics."
    )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub pull request diff and print structured Markdown.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    input_group.add_argument("--diff-file", type=Path, help="Path to a local .diff file")
    parser.add_argument("--output", type=Path, help="Write Markdown review to this file instead of stdout")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.pr:
            ref = parse_pr_url(args.pr)
            diff_text = fetch_pr_diff(ref)
            source = ref.html_url
        else:
            diff_text = args.diff_file.read_text(encoding="utf-8")
            source = str(args.diff_file)

        markdown = render_markdown(analyze_diff(diff_text), source)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
