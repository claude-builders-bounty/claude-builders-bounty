#!/usr/bin/env python3
"""Claude Code PR review agent.

The tool fetches a GitHub pull request diff and returns a structured Markdown
review. It prefers Claude Code for the final analysis, then falls back to a
deterministic local analyzer so the CLI remains testable in offline CI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


USER_AGENT = "cookupsunny-claude-review-agent/1.0"
REQUIRED_SECTIONS = (
    "summary",
    "identified risks",
    "improvement suggestions",
    "confidence score",
)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str

    @property
    def diff_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}.diff"

    @property
    def api_comments_url(self) -> str:
        return (
            f"https://api.github.com/repos/{self.owner}/{self.repo}"
            f"/issues/{self.number}/comments"
        )


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    signals: set[str] = field(default_factory=set)


@dataclass
class DiffAnalysis:
    files: list[FileChange]
    additions: int
    deletions: int
    truncated: bool = False

    @property
    def changed_paths(self) -> list[str]:
        return [item.path for item in self.files]


def parse_pr_url(url: str) -> PullRequestRef:
    match = re.match(
        r"^https?://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$",
        url.strip(),
    )
    if not match:
        raise ValueError(
            "Expected a GitHub PR URL like "
            "https://github.com/owner/repo/pull/123"
        )
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number), url=url.strip())


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fetch_url(url: str, *, token: str | None = None, accept: str = "*/*") -> str:
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        fallback = fetch_url_with_curl(url, token=token, accept=accept)
        if fallback is not None:
            return fallback
        raise RuntimeError(f"GitHub request failed: {exc.reason}") from exc


def fetch_url_with_curl(url: str, *, token: str | None = None, accept: str = "*/*") -> str | None:
    """Fallback for Python installs with a broken local certificate store."""
    curl_path = shutil.which("curl")
    if not curl_path:
        return None
    command = [
        curl_path,
        "-fsSL",
        "-H",
        f"Accept: {accept}",
        "-H",
        f"User-Agent: {USER_AGENT}",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
    ]
    if token:
        command.extend(["-H", f"Authorization: Bearer {token}"])
    command.append(url)
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return result.stdout
    return None


def truncate_diff(diff: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0 or len(diff) <= max_chars:
        return diff, False
    head = diff[: max_chars // 2]
    tail = diff[-(max_chars // 2) :]
    notice = (
        "\n\n"
        f"... diff truncated to {max_chars} characters for review context ...\n\n"
    )
    return head + notice + tail, True


def analyze_diff(diff: str, *, truncated: bool = False) -> DiffAnalysis:
    files: list[FileChange] = []
    current: FileChange | None = None

    for raw_line in diff.splitlines():
        if raw_line.startswith("diff --git "):
            current = parse_diff_header(raw_line)
            files.append(current)
            continue
        if current is None:
            continue
        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue
        if raw_line.startswith("+"):
            current.additions += 1
            collect_line_signals(raw_line[1:], current.signals)
        elif raw_line.startswith("-"):
            current.deletions += 1
        collect_path_signals(current.path, current.signals)

    additions = sum(item.additions for item in files)
    deletions = sum(item.deletions for item in files)
    return DiffAnalysis(
        files=files,
        additions=additions,
        deletions=deletions,
        truncated=truncated,
    )


def parse_diff_header(line: str) -> FileChange:
    match = re.match(r"diff --git a/(.*?) b/(.*)$", line)
    if not match:
        return FileChange(path="unknown")
    _, new_path = match.groups()
    return FileChange(path=new_path)


def collect_path_signals(path: str, signals: set[str]) -> None:
    lowered = path.lower()
    if re.search(r"(^|/)(test|tests|spec|specs|__tests__)(/|$)", lowered):
        signals.add("tests")
    if lowered.endswith((".test.js", ".spec.js", "_test.py", "_spec.py")):
        signals.add("tests")
    if any(part in lowered for part in ("auth", "session", "jwt", "oauth")):
        signals.add("auth")
    if any(part in lowered for part in ("migration", "schema", "database", "db/")):
        signals.add("database")
    if lowered.endswith((".yml", ".yaml", ".toml", ".json", ".lock")):
        signals.add("configuration")
    if any(part in lowered for part in ("package-lock", "yarn.lock", "pnpm-lock")):
        signals.add("lockfile")


def collect_line_signals(line: str, signals: set[str]) -> None:
    lowered = line.lower()
    secret_assignment = re.search(
        r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]([^'\"]{8,})",
        line,
        re.IGNORECASE,
    )
    placeholder_secret = any(
        marker in lowered
        for marker in (
            "${{ secrets.",
            "ghp_xxx",
            "sk-xxx",
            "your_",
            "example",
            "placeholder",
            "redacted",
        )
    )
    if secret_assignment:
        assigned_value = secret_assignment.group(2).strip()
        placeholder_secret = placeholder_secret or bool(
            re.fullmatch(r"[A-Z0-9_]+", assigned_value)
            or "..." in assigned_value
        )
    if secret_assignment and not placeholder_secret:
        signals.add("possible-secret")
    if re.search(r"\b(eval|exec)\s*\(", line):
        signals.add("dynamic-code")
    if "shell=true" in lowered or re.search(r"subprocess\.(run|popen|call)\(", lowered):
        signals.add("shell-command")
    if re.search(r"(select|insert|update|delete).*\+.*(request|input|param|args)", lowered):
        signals.add("sql-construction")
    if "dangerouslysetinnerhtml" in lowered or "innerhtml" in lowered:
        signals.add("html-injection")
    if "todo" in lowered or "fixme" in lowered:
        signals.add("unfinished-work")


def classify_paths(paths: Iterable[str]) -> str:
    buckets: dict[str, int] = {
        "application code": 0,
        "tests": 0,
        "configuration": 0,
        "documentation": 0,
    }
    for path in paths:
        lowered = path.lower()
        if lowered.endswith((".md", ".rst", ".txt")):
            buckets["documentation"] += 1
        elif re.search(r"(^|/)(test|tests|spec|specs|__tests__)(/|$)", lowered):
            buckets["tests"] += 1
        elif lowered.endswith((".yml", ".yaml", ".toml", ".json", ".lock")):
            buckets["configuration"] += 1
        else:
            buckets["application code"] += 1
    dominant = [name for name, count in buckets.items() if count]
    if not dominant:
        return "no changed files"
    if len(dominant) == 1:
        return dominant[0]
    return ", ".join(dominant[:-1]) + f", and {dominant[-1]}"


def static_review(pr: PullRequestRef, analysis: DiffAnalysis) -> str:
    paths = analysis.changed_paths
    file_count = len(paths)
    scope = classify_paths(paths)
    summary = [
        (
            f"This PR changes {file_count} file{'s' if file_count != 1 else ''} "
            f"with about {analysis.additions} added and {analysis.deletions} removed lines."
        ),
        (
            f"The touched paths are primarily {scope}, based on the diff from "
            f"{pr.owner}/{pr.repo}#{pr.number}."
        ),
        (
            "The review below focuses on correctness, security, test coverage, "
            "and maintainability signals visible in the patch."
        ),
    ]
    risks = identify_risks(analysis)
    suggestions = identify_suggestions(analysis, risks)
    confidence = confidence_for(analysis, risks)

    return "\n".join(
        [
            "## Summary",
            " ".join(summary),
            "",
            "## Identified Risks",
            format_bullets(risks),
            "",
            "## Improvement Suggestions",
            format_bullets(suggestions),
            "",
            "## Confidence Score",
            confidence,
            "",
        ]
    )


def identify_risks(analysis: DiffAnalysis) -> list[str]:
    if not analysis.files:
        return ["No diff content was available, so behavioral risk could not be assessed."]

    all_signals = set().union(*(item.signals for item in analysis.files))
    risks: list[str] = []
    if "possible-secret" in all_signals:
        risks.append("Possible hardcoded secret or token-like value appears in added lines.")
    if "dynamic-code" in all_signals:
        risks.append("Dynamic code execution appears in the patch and should be tightly scoped.")
    if "shell-command" in all_signals:
        risks.append("Shell or subprocess execution appears in the patch and may need input validation.")
    if "sql-construction" in all_signals:
        risks.append("SQL construction appears to use string concatenation or user-controlled input.")
    if "html-injection" in all_signals:
        risks.append("HTML injection-sensitive rendering appears in added lines.")
    if "auth" in all_signals:
        risks.append("Authentication or session-related code changed, increasing regression impact.")
    if "database" in all_signals:
        risks.append("Database or migration code changed and may need rollback/compatibility checks.")
    if "lockfile" in all_signals:
        risks.append("Lockfile changes can obscure dependency updates; verify the intended package delta.")
    if "unfinished-work" in all_signals:
        risks.append("TODO/FIXME markers were added and may indicate unfinished behavior.")
    if analysis.additions + analysis.deletions > 800:
        risks.append("The diff is large enough that manual review may miss cross-file behavior changes.")
    if analysis.truncated:
        risks.append("The diff was truncated before review, so some changed lines were not analyzed.")
    if "tests" not in all_signals and analysis.additions > 20:
        risks.append("No obvious test file changes were found for a non-trivial patch.")
    if not risks:
        risks.append("No high-risk patterns were detected from the diff alone.")
    return risks


def identify_suggestions(analysis: DiffAnalysis, risks: list[str]) -> list[str]:
    all_signals = set().union(*(item.signals for item in analysis.files)) if analysis.files else set()
    suggestions: list[str] = []
    if "possible-secret" in all_signals:
        suggestions.append("Remove any committed secrets and rotate exposed credentials if they are real.")
    if "shell-command" in all_signals or "dynamic-code" in all_signals:
        suggestions.append("Add tests covering untrusted input paths before merging execution-sensitive code.")
    if "sql-construction" in all_signals:
        suggestions.append("Use parameterized queries or query builder bindings for user-controlled values.")
    if "auth" in all_signals:
        suggestions.append("Add regression tests for authenticated, unauthenticated, and expired-session flows.")
    if "database" in all_signals:
        suggestions.append("Document migration rollback expectations and verify old/new schema compatibility.")
    if "tests" not in all_signals and analysis.additions > 20:
        suggestions.append("Add or update tests that exercise the changed behavior before merge.")
    if analysis.truncated:
        suggestions.append("Re-run the review with a higher --max-diff-chars value for complete coverage.")
    if not suggestions:
        suggestions.append("Keep the PR small, confirm the test suite covers the main changed path, and merge normally.")
    if risks == ["No high-risk patterns were detected from the diff alone."]:
        suggestions.append("Have a maintainer still check product intent, since diff-only review cannot infer requirements.")
    return suggestions


def confidence_for(analysis: DiffAnalysis, risks: list[str]) -> str:
    if not analysis.files or analysis.truncated:
        return "Low"
    if analysis.additions + analysis.deletions > 800:
        return "Low"
    high_risk = {
        "Possible hardcoded secret or token-like value appears in added lines.",
        "Dynamic code execution appears in the patch and should be tightly scoped.",
        "Shell or subprocess execution appears in the patch and may need input validation.",
        "SQL construction appears to use string concatenation or user-controlled input.",
        "HTML injection-sensitive rendering appears in added lines.",
    }
    if any(risk in high_risk for risk in risks):
        return "Medium"
    if analysis.additions + analysis.deletions < 120 and any(
        "tests" in item.signals for item in analysis.files
    ):
        return "High"
    return "Medium"


def format_bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_prompt(pr: PullRequestRef, diff: str) -> str:
    return textwrap.dedent(
        f"""
        Review this GitHub pull request diff as a senior code reviewer.

        PR: {pr.url}

        Return Markdown only with exactly these sections:

        ## Summary
        2-3 concise sentences summarizing the change.

        ## Identified Risks
        Bullet list of concrete correctness, security, testing, performance,
        compatibility, or maintainability risks. Use "- None found from the diff"
        if appropriate.

        ## Improvement Suggestions
        Bullet list of actionable suggestions. Keep them specific to this diff.

        ## Confidence Score
        One of: Low, Medium, High.

        Diff:
        ```diff
        {diff}
        ```
        """
    ).strip()


def run_claude(pr: PullRequestRef, diff: str, *, timeout: int, max_budget_usd: str) -> str | None:
    claude_path = shutil.which("claude")
    if not claude_path:
        return None

    agents = {
        "pr-reviewer": {
            "description": "Reviews GitHub PR diffs and returns structured Markdown.",
            "prompt": (
                "You are a concise senior code reviewer. Focus on concrete "
                "behavioral risks visible in the diff. Do not invent files or "
                "facts not shown in the patch."
            ),
        }
    }
    command = [
        claude_path,
        "--bare",
        "--print",
        "--no-session-persistence",
        "--max-budget-usd",
        max_budget_usd,
        "--agents",
        json.dumps(agents),
        "--agent",
        "pr-reviewer",
    ]
    try:
        result = subprocess.run(
            command,
            input=build_prompt(pr, diff),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if has_required_sections(output):
        return output + "\n"
    return None


def has_required_sections(markdown: str) -> bool:
    lowered = markdown.lower()
    return all(section in lowered for section in REQUIRED_SECTIONS)


def post_comment(pr: PullRequestRef, body: str, *, token: str) -> None:
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        pr.api_comments_url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"GitHub comment returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub comment failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub comment failed: {exc.reason}") from exc


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub pull request diff and emit structured Markdown.",
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL to review.")
    parser.add_argument(
        "--diff-file",
        type=Path,
        help="Read diff content from a local file instead of fetching from GitHub.",
    )
    parser.add_argument("--output", type=Path, help="Write review Markdown to this file.")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the generated review to the PR using GITHUB_TOKEN.",
    )
    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="Skip Claude Code and use the deterministic local analyzer.",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=60_000,
        help="Maximum diff characters to send/analyze before truncating.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Claude Code subprocess timeout.",
    )
    parser.add_argument(
        "--max-budget-usd",
        default="0.25",
        help="Claude Code max budget when using --print.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        pr = parse_pr_url(args.pr)
        raw_diff = (
            read_text_file(args.diff_file)
            if args.diff_file
            else fetch_url(pr.diff_url, token=os.getenv("GITHUB_TOKEN"))
        )
        diff, truncated = truncate_diff(raw_diff, args.max_diff_chars)
        analysis = analyze_diff(diff, truncated=truncated)
        review = None
        if not args.no_claude:
            review = run_claude(
                pr,
                diff,
                timeout=args.timeout_seconds,
                max_budget_usd=args.max_budget_usd,
            )
        if review is None:
            review = static_review(pr, analysis)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(review, encoding="utf-8")
        else:
            sys.stdout.write(review)
        if args.post_comment:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                raise RuntimeError("--post-comment requires GITHUB_TOKEN")
            post_comment(pr, review, token=token)
    except Exception as exc:  # noqa: BLE001 - CLI should convert all failures.
        parser.exit(1, f"claude-review: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
