#!/usr/bin/env python3
"""Claude Code PR review helper.

Fetches a GitHub pull request diff and renders a structured Markdown review.
The implementation is dependency-free so it can run in GitHub Actions and
fresh clones without a package install step.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


GITHUB_API = "https://api.github.com"
USER_AGENT = "claude-builders-bounty-pr-reviewer"

SECRET_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|private[_-]?key)")
ASSIGNMENT_RE = re.compile(r"(?i)(=|:)\s*['\"][^'\"]{8,}['\"]")
SQL_RE = re.compile(r"(?i)\b(select|insert|update|delete)\b.+(\+|f['\"]|%|\.format\()")
SHELL_RE = re.compile(r"(?i)(shell\s*=\s*True|os\.system\(|subprocess\.(call|run|Popen)\()")
EVAL_RE = re.compile(r"\b(eval|exec)\s*\(")
SUPPRESSION_RE = re.compile(r"(?i)(noqa|eslint-disable|ts-ignore|type:\s*ignore|pylint:\s*disable)")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def repo_full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class Finding:
    severity: str
    title: str
    detail: str
    path: str | None = None

    def to_markdown(self) -> str:
        location = f" in `{self.path}`" if self.path else ""
        return f"- **{self.severity}: {self.title}**{location} - {self.detail}"


@dataclass
class Review:
    pr_title: str
    pr_url: str
    files_changed: list[str]
    additions: int
    deletions: int
    summary: list[str]
    risks: list[Finding]
    suggestions: list[str]
    confidence: str
    notes: list[str]

    def to_markdown(self) -> str:
        risk_lines = (
            [risk.to_markdown() for risk in self.risks]
            if self.risks
            else ["- No high-confidence risks were detected by the local analyzer."]
        )
        suggestion_lines = [f"- {suggestion}" for suggestion in self.suggestions]

        changed = ", ".join(f"`{path}`" for path in self.files_changed[:8])
        if len(self.files_changed) > 8:
            changed += f", and {len(self.files_changed) - 8} more"
        if not changed:
            changed = "No changed files detected"

        lines = [
            "## Claude Code PR Review",
            "",
            f"**PR:** [{self.pr_title}]({self.pr_url})",
            f"**Changed files:** {changed}",
            f"**Diff size:** +{self.additions} / -{self.deletions}",
            "",
            "### Summary of Changes",
            *[f"- {sentence}" for sentence in self.summary],
            "",
            "### Identified Risks",
            *risk_lines,
            "",
            "### Improvement Suggestions",
            *suggestion_lines,
            "",
            f"### Confidence Score: {self.confidence}",
            confidence_explanation(self.confidence),
        ]
        if self.notes:
            lines.extend(["", "### Analyzer Notes", *[f"- {note}" for note in self.notes]])
        return "\n".join(lines).rstrip() + "\n"


def confidence_explanation(confidence: str) -> str:
    if confidence == "High":
        return "The diff is small enough for focused review and the analyzer found clear structural signals."
    if confidence == "Medium":
        return "The review is useful, but the diff size, missing tests, or heuristic-only findings leave some uncertainty."
    return "The diff is large, sparse, or difficult to evaluate without deeper project-specific context."


def parse_pr_reference(pr: str | None, repo: str | None, pr_number: int | None = None) -> PullRequestRef:
    if pr:
        url_match = re.match(
            r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$",
            pr.strip(),
        )
        if url_match:
            owner, repo_name, number = url_match.groups()
            return PullRequestRef(owner=owner, repo=repo_name, number=int(number))
        if pr.isdigit() and repo:
            owner, repo_name = parse_repo(repo)
            return PullRequestRef(owner=owner, repo=repo_name, number=int(pr))
        raise ValueError("Expected --pr to be a GitHub PR URL or a number used with --repo.")

    if repo and pr_number is not None:
        owner, repo_name = parse_repo(repo)
        return PullRequestRef(owner=owner, repo=repo_name, number=pr_number)

    raise ValueError("Provide --pr https://github.com/owner/repo/pull/123 or --repo owner/repo --pr-number 123.")


def parse_repo(repo: str) -> tuple[str, str]:
    parts = repo.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Expected repository in owner/repo form.")
    return parts[0], parts[1]


def github_request(
    url: str,
    *,
    token: str | None,
    accept: str = "application/vnd.github+json",
    method: str = "GET",
    body: bytes | None = None,
) -> bytes:
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed ({exc.code}) for {url}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub request failed for {url}: {exc.reason}") from exc


def fetch_pr(ref: PullRequestRef, token: str | None) -> dict:
    url = f"{GITHUB_API}/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    return json.loads(github_request(url, token=token).decode("utf-8"))


def fetch_diff(ref: PullRequestRef, token: str | None) -> str:
    url = f"{GITHUB_API}/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    data = github_request(url, token=token, accept="application/vnd.github.v3.diff")
    return data.decode("utf-8", errors="replace")


def post_comment(ref: PullRequestRef, token: str, body: str) -> str:
    url = f"{GITHUB_API}/repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    data = github_request(url, token=token, method="POST", body=payload)
    return json.loads(data.decode("utf-8")).get("html_url", "")


def analyze_diff(
    diff: str,
    *,
    pr_title: str,
    pr_url: str,
    max_diff_chars: int = 120_000,
) -> Review:
    truncated = len(diff) > max_diff_chars
    if truncated:
        diff = diff[:max_diff_chars]

    files_changed: list[str] = []
    additions = 0
    deletions = 0
    tests_touched = False
    docs_only = True
    current_file: str | None = None
    findings: list[Finding] = []

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current_file = extract_path_from_diff_header(line)
            if current_file and current_file not in files_changed:
                files_changed.append(current_file)
                if not is_docs_path(current_file):
                    docs_only = False
                if is_test_path(current_file):
                    tests_touched = True
            continue

        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
            inspect_added_line(line[1:], current_file, findings)
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    code_files = [path for path in files_changed if not is_docs_path(path)]
    if code_files and not tests_touched and additions >= 40:
        findings.append(
            Finding(
                "Medium",
                "No tests changed with code",
                "The PR changes implementation files but does not add or update tests in the diff.",
            )
        )
    if additions + deletions > 900:
        findings.append(
            Finding(
                "Medium",
                "Large review surface",
                "The diff is large enough that a single reviewer may miss behavior changes; consider smaller PRs.",
            )
        )

    risks = dedupe_findings(findings)
    suggestions = build_suggestions(code_files, tests_touched, risks, docs_only)
    summary = build_summary(files_changed, additions, deletions, tests_touched, docs_only, risks)
    confidence = choose_confidence(additions, deletions, tests_touched, truncated, risks)
    notes = []
    if truncated:
        notes.append(f"Diff was truncated to {max_diff_chars} characters before analysis.")

    return Review(
        pr_title=pr_title or "Pull request",
        pr_url=pr_url,
        files_changed=files_changed,
        additions=additions,
        deletions=deletions,
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        notes=notes,
    )


def extract_path_from_diff_header(line: str) -> str | None:
    # Format: diff --git a/path b/path
    parts = line.split()
    if len(parts) >= 4 and parts[3].startswith("b/"):
        return parts[3][2:]
    return None


def inspect_added_line(content: str, path: str | None, findings: list[Finding]) -> None:
    stripped = content.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("//"):
        return

    if SECRET_RE.search(stripped) and ASSIGNMENT_RE.search(stripped) and "os.environ" not in stripped:
        findings.append(
            Finding(
                "High",
                "Possible hardcoded secret",
                "A credential-like value appears to be assigned directly in added code.",
                path,
            )
        )
    if EVAL_RE.search(stripped):
        findings.append(
            Finding(
                "High",
                "Dynamic code execution",
                "`eval` or `exec` appears in added code and should be replaced or tightly sandboxed.",
                path,
            )
        )
    if SHELL_RE.search(stripped):
        severity = "High" if "shell=True" in stripped.replace(" ", "") else "Medium"
        findings.append(
            Finding(
                severity,
                "Shell execution added",
                "Added shell execution needs input validation, argument arrays, and timeout handling.",
                path,
            )
        )
    if SQL_RE.search(stripped):
        findings.append(
            Finding(
                "High",
                "Interpolated SQL",
                "SQL appears to be built with string interpolation or concatenation; prefer parameterized queries.",
                path,
            )
        )
    if stripped.startswith("except:") or stripped.startswith("except Exception"):
        findings.append(
            Finding(
                "Medium",
                "Broad exception handling",
                "Broad catches can hide production failures; catch specific exceptions or re-raise with context.",
                path,
            )
        )
    if SUPPRESSION_RE.search(stripped):
        findings.append(
            Finding(
                "Low",
                "Static analysis suppression",
                "A lint/type-check suppression was added; make sure the PR explains why it is needed.",
                path,
            )
        )


def dedupe_findings(findings: Iterable[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str | None]] = set()
    result: list[Finding] = []
    for finding in findings:
        key = (finding.severity, finding.title, finding.path)
        if key in seen:
            continue
        seen.add(key)
        result.append(finding)
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(result, key=lambda item: (severity_order.get(item.severity, 9), item.title, item.path or ""))


def is_docs_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".md", ".txt", ".rst", ".adoc")) or lowered.startswith("docs/")


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    return (
        "/test/" in lowered
        or "/tests/" in lowered
        or lowered.startswith("test/")
        or lowered.startswith("tests/")
        or lowered.endswith(("_test.py", "test.py", ".test.js", ".spec.js", ".test.ts", ".spec.ts"))
    )


def build_summary(
    files_changed: list[str],
    additions: int,
    deletions: int,
    tests_touched: bool,
    docs_only: bool,
    risks: list[Finding],
) -> list[str]:
    if not files_changed:
        return ["The diff did not expose any changed files, so there is no substantive change to review."]

    areas = summarize_areas(files_changed)
    first = f"This PR changes {len(files_changed)} file(s) with +{additions}/-{deletions}, mostly in {areas}."
    if docs_only:
        second = "The change appears documentation-only, so the main review focus is clarity and completeness rather than runtime behavior."
    elif tests_touched:
        second = "The diff includes test coverage alongside implementation changes, which improves reviewer confidence."
    else:
        second = "The diff changes executable code without an obvious matching test update."

    high_count = sum(1 for risk in risks if risk.severity == "High")
    if high_count:
        third = f"The analyzer found {high_count} high-severity signal(s) that should be resolved or explained before merge."
    elif risks:
        third = "The analyzer found review follow-ups, but no high-severity signal in the changed lines."
    else:
        third = "The analyzer did not find a high-confidence risk pattern in the changed lines."
    return [first, second, third]


def summarize_areas(files_changed: list[str]) -> str:
    buckets: dict[str, int] = {}
    for path in files_changed:
        bucket = path.split("/", 1)[0] if "/" in path else path
        buckets[bucket] = buckets.get(bucket, 0) + 1
    top = sorted(buckets.items(), key=lambda item: (-item[1], item[0]))[:3]
    return ", ".join(f"`{name}`" for name, _count in top)


def build_suggestions(
    code_files: list[str],
    tests_touched: bool,
    risks: list[Finding],
    docs_only: bool,
) -> list[str]:
    suggestions: list[str] = []
    if code_files and not tests_touched:
        suggestions.append("Add or update focused tests that exercise the changed behavior.")
    if any(risk.severity == "High" for risk in risks):
        suggestions.append("Resolve the high-severity findings or document why the flagged code is safe.")
    if any(risk.title == "Shell execution added" for risk in risks):
        suggestions.append("Prefer argument-list subprocess calls, explicit timeouts, and allow-listed inputs.")
    if docs_only:
        suggestions.append("Confirm the documentation matches the current CLI/API behavior before merge.")
    suggestions.append("Run the repository's native test or lint command and include the result in the PR.")
    suggestions.append("Keep the review comment updated if follow-up commits materially change the risk profile.")
    return suggestions


def choose_confidence(
    additions: int,
    deletions: int,
    tests_touched: bool,
    truncated: bool,
    risks: list[Finding],
) -> str:
    size = additions + deletions
    if truncated or size > 1200:
        return "Low"
    if size <= 350 and (tests_touched or not risks):
        return "High"
    return "Medium"


def review_as_json(review: Review) -> str:
    return json.dumps(asdict(review), indent=2)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_or_print(content: str, output: str | None) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a GitHub PR diff and print a structured Claude Code review.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --repo owner/repo --pr-number 123 --comment
              claude-review --diff-file change.diff --title "Local patch"
            """
        ),
    )
    parser.add_argument("--pr", help="GitHub PR URL, or a PR number when --repo is also provided.")
    parser.add_argument("--repo", help="Repository in owner/repo form, used with --pr-number or numeric --pr.")
    parser.add_argument("--pr-number", type=int, help="Pull request number used with --repo.")
    parser.add_argument("--diff-file", type=Path, help="Analyze a local diff file instead of fetching GitHub.")
    parser.add_argument("--title", default="Pull request", help="Title for --diff-file output.")
    parser.add_argument("--output", help="Write the review to a file instead of stdout.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--comment", action="store_true", help="Post the Markdown review back to the PR.")
    parser.add_argument("--max-diff-chars", type=int, default=120_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")

    try:
        if args.diff_file:
            diff = read_text(args.diff_file)
            pr_title = args.title
            pr_url = "local diff"
            ref = None
        else:
            ref = parse_pr_reference(args.pr, args.repo, args.pr_number)
            pr_info = fetch_pr(ref, token)
            diff = fetch_diff(ref, token)
            pr_title = pr_info.get("title") or f"PR #{ref.number}"
            pr_url = pr_info.get("html_url") or ref.html_url

        review = analyze_diff(
            diff,
            pr_title=pr_title,
            pr_url=pr_url,
            max_diff_chars=args.max_diff_chars,
        )
        content = review.to_markdown() if args.format == "markdown" else review_as_json(review)

        if args.comment:
            if args.format != "markdown":
                raise ValueError("--comment requires --format markdown.")
            if ref is None:
                raise ValueError("--comment requires a GitHub PR, not --diff-file.")
            if not token:
                raise ValueError("--comment requires GITHUB_TOKEN with permission to write PR comments.")
            comment_url = post_comment(ref, token, content)
            review.notes.append(f"Posted review comment: {comment_url}")
            content = review.to_markdown()

        write_or_print(content, args.output)
        return 0
    except Exception as exc:  # noqa: BLE001 - command-line tool needs concise errors.
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
