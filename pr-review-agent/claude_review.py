#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request diff."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import sys
import urllib.error
import urllib.request
from collections import Counter


@dataclasses.dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    added_lines: list[str] = dataclasses.field(default_factory=list)
    removed_lines: list[str] = dataclasses.field(default_factory=list)


class ReviewError(RuntimeError):
    """Raised when the review agent cannot continue."""


def diff_url(pr_url: str) -> str:
    normalized = pr_url.strip().rstrip("/")
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/pull/\d+$", normalized):
        raise ReviewError("expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return f"{normalized}.diff"


def fetch_diff(pr_url: str) -> str:
    request = urllib.request.Request(
        diff_url(pr_url),
        headers={
            "Accept": "text/plain",
            "User-Agent": "claude-review-agent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise ReviewError(f"failed to fetch PR diff: {error}") from error


def parse_diff(diff: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"diff --git a/(.*?) b/(.*)", line)
            path = match.group(2) if match else line.rsplit(" ", 1)[-1]
            current = FileChange(path=path)
            files.append(current)
            continue

        if current is None:
            continue

        if line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            current.removed_lines.append(line[1:])

    return files


def language_for(path: str) -> str:
    suffix = pathlib.Path(path).suffix.lower()
    return {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".md": "Markdown",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".json": "JSON",
        ".sql": "SQL",
    }.get(suffix, suffix.lstrip(".").upper() or "Other")


def change_summary(files: list[FileChange]) -> str:
    if not files:
        return "No file changes were found in the supplied diff."

    languages = Counter(language_for(file.path) for file in files)
    total_additions = sum(file.additions for file in files)
    total_deletions = sum(file.deletions for file in files)
    top_languages = ", ".join(name for name, _ in languages.most_common(3))
    largest = max(files, key=lambda file: file.additions + file.deletions)

    return (
        f"This PR changes {len(files)} file(s), with {total_additions} additions and "
        f"{total_deletions} deletions across {top_languages}. The largest change is "
        f"`{largest.path}`, so that file deserves the closest review pass."
    )


def contains_any(lines: list[str], patterns: tuple[str, ...]) -> bool:
    joined = "\n".join(lines).lower()
    return any(pattern in joined for pattern in patterns)


def risk_signals(files: list[FileChange]) -> list[str]:
    risks: list[str] = []

    for file in files:
        path_lower = file.path.lower()
        added = file.added_lines

        if any(part in path_lower for part in ("auth", "login", "token", "password", "secret")):
            risks.append(f"`{file.path}` touches authentication or secret-handling paths; verify access control and redaction behavior.")
        if any(part in path_lower for part in ("payment", "billing", "stripe", "invoice")):
            risks.append(f"`{file.path}` touches money movement; verify idempotency, retries, and failure paths.")
        if "migration" in path_lower or path_lower.endswith(".sql"):
            risks.append(f"`{file.path}` changes database shape; verify rollback and data compatibility.")
        if contains_any(added, ("eval(", "exec(", "shell=true", "subprocess", "os.system")):
            risks.append(f"`{file.path}` introduces dynamic execution or shell access; verify input boundaries.")
        if contains_any(added, ("todo", "fixme", "console.log", "debugger")):
            risks.append(f"`{file.path}` includes debug or follow-up markers that may not be production ready.")
        if file.additions + file.deletions > 300:
            risks.append(f"`{file.path}` is a large change; consider splitting or adding focused tests around the main behavior.")

    return dedupe(risks) or ["No obvious high-risk patterns were detected from the diff alone."]


def suggestions(files: list[FileChange]) -> list[str]:
    tips: list[str] = []
    paths = [file.path.lower() for file in files]
    all_added = [line for file in files for line in file.added_lines]

    if any(path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")) for path in paths):
        tips.append("Add or update tests that exercise the changed behavior, including at least one failure path.")
    if any(path.endswith((".md", ".yml", ".yaml", ".json")) for path in paths):
        tips.append("Validate generated or configuration files with the repository's formatter or schema checks.")
    if contains_any(all_added, ("http", "fetch(", "axios", "request(")):
        tips.append("Mock network boundaries in tests so retry, timeout, and error handling remain deterministic.")
    if not tips:
        tips.append("Run the repository's normal lint and test commands before merge.")

    tips.append("Keep the PR description aligned with the final behavior so reviewers can verify intent quickly.")
    return dedupe(tips)


def confidence(files: list[FileChange], risks: list[str]) -> str:
    changed_lines = sum(file.additions + file.deletions for file in files)
    if changed_lines > 500 or len(risks) >= 4:
        return "Low"
    if changed_lines > 150 or len(risks) >= 2:
        return "Medium"
    return "High"


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def render_review(files: list[FileChange], source: str) -> str:
    risks = risk_signals(files)
    tips = suggestions(files)
    score = confidence(files, risks)
    changed_files = "\n".join(
        f"- `{file.path}` (+{file.additions}/-{file.deletions}, {file.hunks} hunk{'s' if file.hunks != 1 else ''})"
        for file in files[:12]
    )
    if len(files) > 12:
        changed_files += f"\n- ...and {len(files) - 12} more file(s)"

    return "\n".join(
        [
            "## PR Review",
            "",
            "### Summary of changes",
            change_summary(files),
            f"Source reviewed: `{source}`.",
            "",
            "### Changed files",
            changed_files or "- No changed files detected.",
            "",
            "### Identified risks",
            *[f"- {risk}" for risk in risks],
            "",
            "### Improvement suggestions",
            *[f"- {tip}" for tip in tips],
            "",
            f"### Confidence score: {score}",
            "",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured PR review comment.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub pull request URL.")
    source.add_argument("--diff", help="Path to a local .diff file.")
    parser.add_argument("--output", help="Write Markdown review to this file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        if args.pr:
            source = args.pr
            diff = fetch_diff(args.pr)
        else:
            source = args.diff
            diff = pathlib.Path(args.diff).read_text(encoding="utf-8")

        review = render_review(parse_diff(diff), source)
        if args.output:
            pathlib.Path(args.output).write_text(review, encoding="utf-8")
        else:
            print(review, end="")
        return 0
    except (OSError, ReviewError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
