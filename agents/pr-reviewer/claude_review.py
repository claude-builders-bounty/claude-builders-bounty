#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub PR diff."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PR_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)")


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0


@dataclass
class ReviewFacts:
    files: dict[str, FileChange] = field(default_factory=dict)
    additions: int = 0
    deletions: int = 0
    has_tests: bool = False
    has_docs: bool = False
    touches_dependencies: bool = False
    touches_ci: bool = False
    touches_config: bool = False
    touches_security_sensitive: bool = False

    @property
    def total_lines(self) -> int:
        return self.additions + self.deletions


def pr_diff_url(pr_url: str) -> str:
    match = PR_RE.fullmatch(pr_url.rstrip("/"))
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_url(url: str) -> str:
    request = Request(url, headers={"User-Agent": "claude-review/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def normalize_path(path: str) -> str:
    path = path.strip()
    if path.startswith("b/"):
        return path[2:]
    return path


def parse_diff(diff: str) -> ReviewFacts:
    facts = ReviewFacts()
    current: FileChange | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            path = normalize_path(parts[-1]) if parts else "unknown"
            current = facts.files.setdefault(path, FileChange(path=path))
            mark_file_flags(path, facts)
            continue

        if current is None:
            continue

        if line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            facts.additions += 1
            mark_line_flags(line[1:], facts)
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            facts.deletions += 1
            mark_line_flags(line[1:], facts)

    return facts


def mark_file_flags(path: str, facts: ReviewFacts) -> None:
    lower = path.lower()
    name = Path(lower).name

    if any(token in lower for token in ("test", "spec", "__tests__", "fixtures")):
        facts.has_tests = True
    if lower.endswith((".md", ".mdx", ".rst")) or "docs/" in lower:
        facts.has_docs = True
    if name in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "requirements.txt"}:
        facts.touches_dependencies = True
    if lower.startswith(".github/") or "ci" in lower or name in {"dockerfile", "compose.yaml", "docker-compose.yml"}:
        facts.touches_ci = True
    if name.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".env.example")):
        facts.touches_config = True


def mark_line_flags(line: str, facts: ReviewFacts) -> None:
    lower = line.lower()
    sensitive_tokens = (
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "auth",
        "permission",
        "role",
        "sql",
        "exec(",
        "subprocess",
        "eval(",
    )
    if any(token in lower for token in sensitive_tokens):
        facts.touches_security_sensitive = True


def main_areas(facts: ReviewFacts) -> str:
    paths = sorted(facts.files)
    if not paths:
        return "no files"

    roots: list[str] = []
    for path in paths:
        part = path.split("/", 1)[0]
        if part not in roots:
            roots.append(part)
    return ", ".join(roots[:4]) + ("..." if len(roots) > 4 else "")


def build_summary(facts: ReviewFacts) -> str:
    file_count = len(facts.files)
    area_text = main_areas(facts)
    first = (
        f"This PR changes {file_count} file{'s' if file_count != 1 else ''} "
        f"with {facts.additions} additions and {facts.deletions} deletions."
    )
    second = f"The touched areas are primarily `{area_text}`, so review should focus on behavior in those paths."
    if facts.has_tests:
        third = "The diff includes test-related files, which improves confidence that the change has executable coverage."
    else:
        third = "I do not see test files in the diff, so runtime coverage should be checked before merge."
    return "\n".join((first, second, third))


def identified_risks(facts: ReviewFacts) -> list[str]:
    risks: list[str] = []
    if facts.total_lines > 800 or len(facts.files) > 20:
        risks.append("Large diff size increases the chance of missed regressions during review.")
    if not facts.has_tests:
        risks.append("No test files were detected in the diff, so behavioral changes may be under-covered.")
    if facts.touches_dependencies:
        risks.append("Dependency or lockfile changes can alter transitive runtime behavior.")
    if facts.touches_ci:
        risks.append("CI, build, or container changes may affect deployment and developer workflows.")
    if facts.touches_config:
        risks.append("Configuration changes can behave differently across environments.")
    if facts.touches_security_sensitive:
        risks.append("Security-sensitive terms such as auth, tokens, SQL, subprocess, or permissions appear in changed lines.")
    if not risks:
        risks.append("No obvious high-risk patterns were detected from the diff metadata alone.")
    return risks


def suggestions(facts: ReviewFacts) -> list[str]:
    items = ["Run the project-specific test command and include the result before merge."]
    if not facts.has_tests:
        items.append("Add or update focused tests for the changed behavior, especially edge cases.")
    if facts.touches_dependencies:
        items.append("Confirm dependency changes are intentional and review lockfile updates for unexpected packages.")
    if facts.touches_security_sensitive:
        items.append("Manually inspect changed auth, token, SQL, subprocess, or permission paths for abuse cases.")
    if facts.touches_ci:
        items.append("Verify the CI workflow still runs on the expected triggers and platforms.")
    if facts.has_docs:
        items.append("Check that documentation examples still match the implemented behavior.")
    return items


def confidence(facts: ReviewFacts) -> str:
    if facts.total_lines > 1200 or len(facts.files) > 30:
        return "Low"
    if facts.has_tests and facts.total_lines < 400 and not facts.touches_security_sensitive:
        return "High"
    return "Medium"


def markdown_review(diff: str) -> str:
    facts = parse_diff(diff)
    risks = "\n".join(f"- {item}" for item in identified_risks(facts))
    improvements = "\n".join(f"- {item}" for item in suggestions(facts))
    changed_files = "\n".join(
        f"- `{change.path}` (+{change.additions}/-{change.deletions}, {change.hunks} hunks)"
        for change in sorted(facts.files.values(), key=lambda item: item.path)[:12]
    )
    if len(facts.files) > 12:
        changed_files += f"\n- ...and {len(facts.files) - 12} more files"

    return f"""## Summary of Changes

{build_summary(facts)}

## Identified Risks

{risks}

## Improvement Suggestions

{improvements}

## Confidence Score

{confidence(facts)}

<details>
<summary>Changed files analyzed</summary>

{changed_files or "- No file changes detected."}

</details>
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    source.add_argument("--diff", help="Path to a local unified diff file")
    parser.add_argument("-o", "--output", help="Write Markdown review to this path instead of stdout")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.pr:
        diff = fetch_url(pr_diff_url(args.pr))
    else:
        diff = Path(args.diff).read_text(encoding="utf-8")

    output = markdown_review(diff)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        raise SystemExit(1)
