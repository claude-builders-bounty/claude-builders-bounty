#!/usr/bin/env python3
"""Review a GitHub pull request diff and emit structured Markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$")
FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
HUNK_RE = re.compile(r"^@@")
DELETE_WITHOUT_WHERE = re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.I)
RISK_PATTERNS = {
    "auth": re.compile(r"(auth|session|permission|policy|rbac|acl)", re.I),
    "database": re.compile(r"(migration|schema|sql|database|db/|prisma|sqlite)", re.I),
    "deploy": re.compile(r"(\.github/workflows|Dockerfile|deploy|terraform|infra|k8s)", re.I),
    "dependencies": re.compile(r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|requirements\.txt|pyproject\.toml|package\.json)", re.I),
    "tests": re.compile(r"(^|/)(test|tests|spec|__tests__)(/|_)|(\.test\.|\.spec\.)", re.I),
}


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str = ""
    author: str = ""


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    added_lines: list[str]
    removed_lines: list[str]


def parse_pr_url(url: str) -> PullRequest:
    match = PR_RE.match(url.strip())
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return PullRequest(match.group("owner"), match.group("repo"), int(match.group("number")))


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "claude-review"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise SystemExit(f"GitHub API request failed: {error.code} {error.reason}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"GitHub API request failed: {error.reason}") from error


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"Accept": "text/plain", "User-Agent": "claude-review"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"GitHub diff request failed: {error.code} {error.reason}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"GitHub diff request failed: {error.reason}") from error


def load_pr(pr_url: str) -> tuple[PullRequest, str]:
    pr = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}"
    fallback_diff_url = f"https://github.com/{pr.owner}/{pr.repo}/pull/{pr.number}.diff"
    try:
        metadata = fetch_json(api_url)
        diff_url = metadata.get("diff_url") or fallback_diff_url
        loaded = PullRequest(
            owner=pr.owner,
            repo=pr.repo,
            number=pr.number,
            title=str(metadata.get("title") or ""),
            author=str((metadata.get("user") or {}).get("login") or ""),
        )
        return loaded, fetch_text(diff_url)
    except SystemExit:
        return pr, fetch_text(fallback_diff_url)


def parse_diff(diff_text: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0
    added_lines: list[str] = []
    removed_lines: list[str] = []
    for line in diff_text.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            files.append(file_match.group(2))
        elif HUNK_RE.match(line):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            removed_lines.append(line[1:])
    return DiffStats(sorted(dict.fromkeys(files)), additions, deletions, hunks, added_lines, removed_lines)


def primary_areas(files: list[str]) -> list[str]:
    areas: list[str] = []
    for path in files:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] in {"src", "app", "packages", "services", "agents"}:
            area = "/".join(parts[:2])
        else:
            area = parts[0]
        if area not in areas:
            areas.append(area)
    return areas[:5]


def touched(pattern: str, files: list[str]) -> bool:
    compiled = RISK_PATTERNS[pattern]
    return any(compiled.search(path) for path in files)


def code_files(files: list[str]) -> list[str]:
    return [path for path in files if Path(path).suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".rb", ".java", ".cs"}]


def contains_any(lines: list[str], pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(line) for line in lines)


def identify_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    total = stats.additions + stats.deletions
    if total > 800 or len(stats.files) > 20:
        risks.append(f"Large review surface: {len(stats.files)} files and {total} changed lines may hide regressions.")
    if touched("database", stats.files):
        risks.append("Database or migration files changed; verify migration ordering, rollback story, and data safety before merge.")
    if touched("auth", stats.files):
        risks.append("Auth or permission-adjacent files changed; check tenant/user boundaries and denied-by-default behavior.")
    if touched("deploy", stats.files):
        risks.append("CI, deployment, or infrastructure files changed; confirm secrets, environment names, and trigger conditions.")
    if touched("dependencies", stats.files):
        risks.append("Dependency or lockfile changes are present; review transitive updates and supply-chain impact.")
    if code_files(stats.files) and not touched("tests", stats.files):
        risks.append("Application code changed without obvious test files in the diff.")
    if contains_any(stats.added_lines, re.compile(r"\brm\s+-[^\n]*[rR][^\n]*f|\brm\s+-[^\n]*f[^\n]*[rR]", re.I)):
        risks.append("A recursive force delete command appears in added lines.")
    if contains_any(stats.added_lines, re.compile(r"\bdrop\s+table\b|\btruncate\b", re.I)) or contains_any(
        stats.added_lines, DELETE_WITHOUT_WHERE
    ):
        risks.append("Potentially destructive SQL appears in added lines.")
    if contains_any(stats.added_lines, re.compile(r"\bTODO\b|\bFIXME\b", re.I)):
        risks.append("New TODO/FIXME markers may represent unfinished work.")
    return risks or ["No major risks were detected from the diff alone."]


def suggestions(stats: DiffStats, risks: list[str]) -> list[str]:
    items: list[str] = []
    if any("test" in risk.lower() for risk in risks):
        items.append("Add or update focused tests for the changed behavior before merge.")
    if touched("database", stats.files):
        items.append("Run migrations against a disposable database and document any data-loss or backfill assumptions.")
    if touched("auth", stats.files):
        items.append("Add a denied-access regression case for at least one unauthorized user or tenant.")
    if touched("deploy", stats.files):
        items.append("Dry-run the workflow or deployment path and confirm required secrets are documented.")
    if stats.additions + stats.deletions > 800:
        items.append("Consider splitting unrelated changes so reviewers can reason about risk independently.")
    if not items:
        items.append("Run the project test suite and smoke-test the changed user flow.")
    items.append("Ask the author to confirm any generated files, lockfiles, or external side effects are intentional.")
    return items


def confidence(stats: DiffStats, risks: list[str], diff_text: str) -> tuple[str, str]:
    if not diff_text.strip() or not stats.files:
        return "Low", "No parseable diff was available."
    total = stats.additions + stats.deletions
    if total > 1200 or len(stats.files) > 30:
        return "Low", "The diff is large enough that heuristic review may miss interactions."
    if any("without obvious test" in risk.lower() for risk in risks):
        return "Medium", "The diff is readable, but missing obvious tests lowers confidence."
    if total <= 300 and touched("tests", stats.files):
        return "High", "The diff is small to medium-sized and includes test coverage."
    return "Medium", "The diff is parseable, but repository-specific runtime context was not executed."


def render_review(pr: PullRequest, stats: DiffStats, diff_text: str) -> str:
    areas = primary_areas(stats.files)
    risks = identify_risks(stats)
    improvements = suggestions(stats, risks)
    score, reason = confidence(stats, risks, diff_text)
    title = f" for `{pr.title}`" if pr.title else ""
    repo = f"{pr.owner}/{pr.repo}" if pr.owner and pr.repo else "the repository"
    pr_ref = f"#{pr.number}" if pr.number else "the pull request"
    area_text = ", ".join(f"`{area}`" for area in areas) if areas else "no file areas"

    lines = [
        "## Summary",
        "",
        f"This review covers {pr_ref}{title} in `{repo}`. The diff changes {len(stats.files)} files with {stats.additions} additions and {stats.deletions} deletions across {stats.hunks} hunks.",
        f"The main touched areas are {area_text}. This comment is based on static diff analysis and should be paired with project tests before merge.",
        "",
        "## Identified Risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.extend(["", "## Improvement Suggestions", ""])
    lines.extend(f"- {item}" for item in improvements)
    lines.extend(["", "## Confidence", "", f"**{score}** - {reason}", ""])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Path to a saved PR diff")
    parser.add_argument("--repo", default="", help="Repository slug for --diff-file mode, e.g. owner/repo")
    parser.add_argument("--number", type=int, default=0, help="PR number for --diff-file mode")
    parser.add_argument("--title", default="", help="PR title for --diff-file mode")
    parser.add_argument("--output", help="Write review Markdown to this file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.pr:
        pr, diff_text = load_pr(args.pr)
    else:
        owner, _, repo = args.repo.partition("/")
        pr = PullRequest(owner=owner, repo=repo, number=args.number, title=args.title)
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")

    review = render_review(pr, parse_diff(diff_text), diff_text)
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
