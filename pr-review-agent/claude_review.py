#!/usr/bin/env python3
"""Deterministic GitHub PR review draft generator.

The tool intentionally avoids paid APIs. It uses the GitHub CLI to fetch a PR
diff and then applies local rules to produce a concise Markdown review draft.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:\?.*)?$")

TEST_RE = re.compile(
    r"(^|/)(__tests__|tests?|spec|fixtures?)/|(^|/)(test_.*|.*(_test|_spec))\.(sh|js|jsx|ts|tsx|py|rb|go|rs)$|(\.|_)(test|spec)\.(js|jsx|ts|tsx|py|rb|go|rs)$",
    re.IGNORECASE,
)

RISK_RULES = [
    (
        "auth/session/security surface changed",
        re.compile(r"(auth|session|login|oauth|jwt|token|permission|security|policy)", re.IGNORECASE),
        "Changes touch authentication, session, permission, or security-related paths; these usually need focused regression tests.",
    ),
    (
        "database or migration changed",
        re.compile(r"(migration|migrations|schema|database|db/|\.sql$)", re.IGNORECASE),
        "Database changes can affect persisted data and rollback behavior; verify migration order and compatibility.",
    ),
    (
        "dependency manifest changed",
        re.compile(
            r"(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|requirements.*\.txt|pyproject\.toml|poetry\.lock|go\.mod|go\.sum|Cargo\.toml|Cargo\.lock|Gemfile(\.lock)?|pom\.xml)$",
            re.IGNORECASE,
        ),
        "Dependency changes may alter build output or security posture; confirm lockfiles and compatibility.",
    ),
    (
        "shell or automation script changed",
        re.compile(r"(\.sh$|(^|/)(Dockerfile|Makefile)|(^|/)(scripts?|bin)/)", re.IGNORECASE),
        "Shell and automation changes can fail differently across environments; check quoting, exit codes, and dry-run behavior.",
    ),
    (
        "generated or bundled file changed",
        re.compile(r"(^|/)(dist|build|coverage|vendor|generated)/|(\.min\.js$|lock$)", re.IGNORECASE),
        "Generated or bundled files are hard to review manually; confirm they are reproducible and intentionally committed.",
    ),
]

ADDED_LINE_RULES = [
    (
        "possible secret or credential literal",
        re.compile(r"(api[_-]?key|secret|password|private[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}", re.IGNORECASE),
        "Added lines look like they may contain credential literals; ensure no secrets are committed.",
    ),
    (
        "destructive shell command",
        re.compile(r"\brm\s+-[^\n]*r[^\n]*f|\bgit\s+push\s+(-f|--force)", re.IGNORECASE),
        "Destructive shell commands or force-push behavior should be guarded or documented.",
    ),
    (
        "dynamic code execution",
        re.compile(r"\b(eval|exec)\s*\(|shell\s*=\s*True|new Function\s*\(", re.IGNORECASE),
        "Dynamic execution increases injection risk; prefer structured APIs or strict input validation.",
    ),
    (
        "broad exception swallowing",
        re.compile(r"except\s+Exception\s*:\s*(pass)?$|catch\s*\([^)]*\)\s*\{\s*\}", re.IGNORECASE),
        "Broad empty error handling can hide production failures; log or surface actionable errors.",
    ),
]


@dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def repo_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] = field(default_factory=list)


@dataclass
class Analysis:
    pr: PullRequestRef
    url: str
    title: str
    files: list[FileChange]
    total_additions: int
    total_deletions: int
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number))


def run_gh(args: list[str]) -> str:
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI is required. Install and authenticate gh, then retry.")
    completed = subprocess.run(
        ["gh", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"gh command failed: gh {' '.join(args)}\n{detail}")
    return completed.stdout


def fetch_pr_metadata(pr: PullRequestRef) -> dict:
    raw = run_gh(
        [
            "pr",
            "view",
            str(pr.number),
            "--repo",
            pr.repo_name,
            "--json",
            "title,url,additions,deletions,files",
        ]
    )
    return json.loads(raw)


def fetch_pr_diff(pr: PullRequestRef) -> str:
    return run_gh(["pr", "diff", str(pr.number), "--repo", pr.repo_name])


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            path = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith("b/") else "unknown"
            current = FileChange(path=path)
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-"):
            current.deletions += 1

    return files


def merge_metadata_counts(files: list[FileChange], metadata: dict) -> list[FileChange]:
    by_path = {item.path: item for item in files}
    for file_meta in metadata.get("files", []):
        path = file_meta.get("path") or file_meta.get("filename")
        if not path or path in by_path:
            continue
        by_path[path] = FileChange(
            path=path,
            additions=int(file_meta.get("additions") or 0),
            deletions=int(file_meta.get("deletions") or 0),
        )
    return sorted(by_path.values(), key=lambda item: item.path)


def has_tests(files: Iterable[FileChange]) -> bool:
    return any(TEST_RE.search(item.path) for item in files)


def classify_risks(files: list[FileChange], total_delta: int) -> list[str]:
    risks: list[str] = []
    paths = [item.path for item in files]
    paths_text = "\n".join(paths)

    for name, pattern, reason in RISK_RULES:
        matched = [path for path in paths if pattern.search(path)]
        if matched:
            example = ", ".join(matched[:3])
            risks.append(f"- **{name}**: {reason} Example path(s): `{example}`.")

    for name, pattern, reason in ADDED_LINE_RULES:
        for item in files:
            if any(pattern.search(line) for line in item.added_lines):
                risks.append(f"- **{name}**: {reason} First matched file: `{item.path}`.")
                break

    if total_delta > 800:
        risks.append(
            f"- **large diff**: The PR changes {total_delta} added/deleted lines; split-review or extra test evidence may be needed."
        )

    if len(files) > 20:
        risks.append(f"- **broad file surface**: The PR touches {len(files)} files, which raises review and regression risk.")

    if not has_tests(files) and not re.search(r"(^|/)(README|docs?)/|\.md$", paths_text, re.IGNORECASE):
        risks.append(
            "- **no obvious tests**: No test files were detected while non-documentation files changed; add or explain verification."
        )

    if not risks:
        risks.append("- No obvious high-risk patterns were detected by the local rules.")
    return risks


def build_suggestions(files: list[FileChange], risks: list[str]) -> list[str]:
    suggestions: list[str] = []
    paths_text = "\n".join(item.path for item in files)

    if any("no obvious tests" in risk for risk in risks):
        suggestions.append("- Add focused tests or include manual verification steps that exercise the changed behavior.")
    if re.search(r"(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|requirements.*\.txt|pyproject\.toml|go\.mod|Cargo\.toml)", paths_text, re.IGNORECASE):
        suggestions.append("- Confirm dependency changes are locked, minimal, and compatible with the supported runtime versions.")
    if re.search(r"(auth|session|security|permission|token)", paths_text, re.IGNORECASE):
        suggestions.append("- Include at least one negative-path test for auth/session/security behavior.")
    if re.search(r"(\.sh$|(^|/)(Dockerfile|Makefile)|(^|/)(scripts?|bin)/)", paths_text, re.IGNORECASE):
        suggestions.append("- Run shell syntax checks or dry-run commands and document expected failure behavior.")
    if not suggestions:
        suggestions.append("- Keep the PR scope tight and mention the exact test or manual verification command in the PR description.")
    suggestions.append("- Ask the author to clarify any generated files or broad refactors before approving.")
    return suggestions


def confidence_score(files: list[FileChange], risks: list[str], total_delta: int) -> str:
    high_signal_risks = [risk for risk in risks if "No obvious high-risk" not in risk]
    tests = has_tests(files)

    if total_delta > 1500 or len(files) > 30 or len(high_signal_risks) >= 5:
        return "Low"
    if not tests and len(high_signal_risks) >= 2:
        return "Low"
    if total_delta > 500 or len(files) > 12 or len(high_signal_risks) >= 2 or not tests:
        return "Medium"
    return "High"


def summarize(analysis: Analysis) -> list[str]:
    file_count = len(analysis.files)
    paths = [item.path for item in analysis.files]
    test_phrase = "with test files detected" if has_tests(analysis.files) else "with no obvious test files detected"
    surface = summarize_surface(paths)
    return [
        (
            f"This PR changes {file_count} file(s) with {analysis.total_additions} additions and "
            f"{analysis.total_deletions} deletions, {test_phrase}."
        ),
        f"The main review surface appears to be {surface}.",
        "The comments below are generated by deterministic local rules and should be treated as a maintainer review draft.",
    ]


def summarize_surface(paths: list[str]) -> str:
    if not paths:
        return "empty or unavailable diff data"
    categories: list[str] = []
    joined = "\n".join(paths)
    if re.search(r"(auth|session|security|permission)", joined, re.IGNORECASE):
        categories.append("auth/security behavior")
    if re.search(r"(migration|schema|database|db/|\.sql$)", joined, re.IGNORECASE):
        categories.append("database behavior")
    if re.search(r"(\.md$|README|docs?/)", joined, re.IGNORECASE):
        categories.append("documentation")
    if re.search(r"(test|spec|__tests__)", joined, re.IGNORECASE):
        categories.append("tests")
    if re.search(r"(\.sh$|Dockerfile|Makefile|scripts?/|bin/)", joined, re.IGNORECASE):
        categories.append("automation/scripts")
    if not categories:
        categories.append("application code")
    return ", ".join(categories)


def analyze(pr_url: str) -> Analysis:
    pr = parse_pr_url(pr_url)
    metadata = fetch_pr_metadata(pr)
    diff_text = fetch_pr_diff(pr)
    files = merge_metadata_counts(parse_diff(diff_text), metadata)
    total_additions = sum(item.additions for item in files) or int(metadata.get("additions") or 0)
    total_deletions = sum(item.deletions for item in files) or int(metadata.get("deletions") or 0)
    total_delta = total_additions + total_deletions
    risks = classify_risks(files, total_delta)
    suggestions = build_suggestions(files, risks)
    confidence = confidence_score(files, risks, total_delta)
    return Analysis(
        pr=pr,
        url=metadata.get("url") or pr_url,
        title=metadata.get("title") or f"PR #{pr.number}",
        files=files,
        total_additions=total_additions,
        total_deletions=total_deletions,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
    )


def render_markdown(analysis: Analysis) -> str:
    changed_files = "\n".join(
        f"- `{item.path}` (+{item.additions}/-{item.deletions})" for item in analysis.files[:20]
    )
    if len(analysis.files) > 20:
        changed_files += f"\n- ... {len(analysis.files) - 20} more file(s)"

    summary = "\n".join(f"- {line}" for line in summarize(analysis))
    risks = "\n".join(analysis.risks)
    suggestions = "\n".join(analysis.suggestions)

    return f"""# PR Review Draft

PR: {analysis.url}
Title: {analysis.title}

## Summary of Changes

{summary}

## Identified Risks

{risks}

## Improvement Suggestions

{suggestions}

## Confidence Score

**{analysis.confidence}**

Confidence is based on changed file count, diff size, detected risk surfaces, and whether test files are present.

## Changed Files

{changed_files if changed_files else "- No changed files were detected."}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Generate a deterministic Markdown review draft for a GitHub PR.",
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--output", help="Optional file path to write the Markdown review.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        markdown = render_markdown(analyze(args.pr))
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review: error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
