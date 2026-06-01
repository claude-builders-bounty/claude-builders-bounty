#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request diff."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@")


@dataclasses.dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    added_lines: list[tuple[str, str]]
    deleted_lines: list[tuple[str, str]]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub pull request diff and print structured Markdown.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Local unified diff file to review")
    parser.add_argument("--repo", help="Repository name to show when using --diff-file")
    parser.add_argument("--title", help="Optional PR title to include in the report")
    return parser.parse_args(argv)


def fetch_pr_diff(pr_url: str) -> tuple[str, str]:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")

    owner, repo, number = match.groups()
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    request = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace"), f"{owner}/{repo}#{number}"
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching {diff_url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch {diff_url}: {exc.reason}") from exc


def parse_diff(diff_text: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0
    current_file = "unknown"
    added_lines: list[tuple[str, str]] = []
    deleted_lines: list[tuple[str, str]] = []

    for line in diff_text.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            current_file = file_match.group(1)
            if current_file != "/dev/null":
                files.append(current_file)
            continue
        if HUNK_RE.match(line):
            hunks += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
            added_lines.append((current_file, line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            deleted_lines.append((current_file, line[1:]))

    return DiffStats(files, additions, deletions, hunks, added_lines, deleted_lines)


def classify_files(files: list[str]) -> Counter[str]:
    groups: Counter[str] = Counter()
    for filename in files:
        suffix = Path(filename).suffix.lower()
        if filename.startswith((".github/", "ci/", "scripts/")) or suffix in {".yml", ".yaml"}:
            groups["automation/config"] += 1
        elif suffix in {".md", ".rst", ".txt"}:
            groups["documentation"] += 1
        elif suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb"}:
            groups["application code"] += 1
        elif suffix in {".json", ".toml", ".lock", ".xml"}:
            groups["metadata/data"] += 1
        else:
            groups["other"] += 1
    return groups


def detect_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    added_text = "\n".join(line for _, line in stats.added_lines)
    touched = "\n".join(stats.files)

    if stats.additions + stats.deletions > 500:
        risks.append("Large diff size increases review surface and regression risk.")
    if re.search(r"\b(eval|exec|subprocess|shell=True|child_process|os\.system)\b", added_text):
        risks.append("New dynamic execution or shell-adjacent code should be checked for injection paths.")
    if re.search(r"\b(token|secret|password|private_key|api[_-]?key)\b", added_text, re.I):
        risks.append("Credential-like names appear in added lines; verify no secrets or sensitive values are committed.")
    if re.search(r"\b(delete|drop|truncate|rm -rf)\b", added_text, re.I):
        risks.append("Destructive operation wording appears in added lines; confirm guardrails and tests.")
    if re.search(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock)$", touched, re.M):
        risks.append("Lockfile changes should match intentional dependency updates.")
    if any(name.startswith(".github/workflows/") for name in stats.files):
        risks.append("Workflow changes can affect CI permissions, triggers, and secret exposure.")
    if not risks:
        risks.append("No high-signal risk patterns detected by the static diff scan.")
    return risks


def suggest_improvements(stats: DiffStats) -> list[str]:
    suggestions: list[str] = []
    file_groups = classify_files(stats.files)

    if file_groups["application code"] and not any("test" in name.lower() for name in stats.files):
        suggestions.append("Add or point to focused tests for the changed application behavior.")
    if file_groups["automation/config"]:
        suggestions.append("Include the exact local or CI command used to validate the workflow/config change.")
    if file_groups["documentation"] == len(stats.files) and stats.files:
        suggestions.append("Confirm links, commands, and paths in the docs still resolve from a fresh checkout.")
    if stats.hunks > len(stats.files) * 4 and stats.files:
        suggestions.append("Consider splitting unrelated edits so maintainers can review each concern independently.")
    suggestions.append("Link this review to the PR discussion and update it after maintainer feedback or test results.")
    return suggestions


def confidence(stats: DiffStats, risks: list[str]) -> str:
    if not stats.files or stats.additions + stats.deletions == 0:
        return "Low"
    if stats.additions + stats.deletions > 800 or len(risks) >= 4:
        return "Low"
    if stats.additions + stats.deletions > 250 or any("No high-signal" not in risk for risk in risks):
        return "Medium"
    return "High"


def summarize(stats: DiffStats, target: str) -> str:
    groups = classify_files(stats.files)
    dominant = ", ".join(f"{count} {name}" for name, count in groups.most_common(3)) or "no files"
    return (
        f"This review covers {target} with {len(stats.files)} changed file(s), "
        f"{stats.additions} addition(s), and {stats.deletions} deletion(s). "
        f"The diff mainly touches {dominant}, so the review focus is regression risk, validation coverage, "
        "and whether the handoff is clear for maintainers."
    )


def render_markdown(stats: DiffStats, target: str, title: str | None = None) -> str:
    risks = detect_risks(stats)
    suggestions = suggest_improvements(stats)
    conf = confidence(stats, risks)
    files_by_dir: dict[str, list[str]] = defaultdict(list)
    for filename in stats.files[:30]:
        top = filename.split("/", 1)[0] if "/" in filename else "."
        files_by_dir[top].append(filename)

    touched = []
    for top, names in sorted(files_by_dir.items()):
        sample = ", ".join(names[:3])
        suffix = "..." if len(names) > 3 else ""
        touched.append(f"- `{top}`: {sample}{suffix}")
    if not touched:
        touched.append("- No changed files detected.")

    title_line = f" for {title}" if title else ""
    risk_lines = "\n".join(f"- {item}" for item in risks)
    suggestion_lines = "\n".join(f"- {item}" for item in suggestions)
    touched_lines = "\n".join(touched)

    return "\n".join(
        [
            f"## Claude Review{title_line}",
            "",
            f"**Target:** {target}",
            "",
            "### Summary",
            summarize(stats, target),
            "",
            "### Identified Risks",
            risk_lines,
            "",
            "### Improvement Suggestions",
            suggestion_lines,
            "",
            "### Changed Surface",
            touched_lines,
            "",
            "### Confidence",
            f"**{conf}**",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.pr:
            diff_text, target = fetch_pr_diff(args.pr)
        else:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
            target = args.repo or Path(args.diff_file).name
        stats = parse_diff(diff_text)
        print(render_markdown(stats, target, args.title))
        return 0
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
