#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request."""

from __future__ import annotations

import argparse
import dataclasses
import os
import re
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
from collections import Counter
from typing import Iterable


PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)(?:[/?#].*)?$"
)
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@")
SENSITIVE_RE = re.compile(
    r"(secret|token|password|credential|private[_-]?key|\.env|\.pem|\.key)",
    re.IGNORECASE,
)
TEST_RE = re.compile(r"(^|/)(test|tests|spec|specs|__tests__)(/|$)|(\.test\.|_test\.)", re.IGNORECASE)
DOC_RE = re.compile(r"(^|/)(readme|docs?)(/|$)|\.(md|mdx|rst)$", re.IGNORECASE)
WORKFLOW_RE = re.compile(r"(^|/)\.github/(workflows|actions)/|action\.ya?ml$", re.IGNORECASE)
DEPENDENCY_RE = re.compile(
    r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|requirements\.txt|poetry\.lock|Cargo\.lock|go\.sum|Gemfile\.lock)$",
    re.IGNORECASE,
)
CA_BUNDLE_CANDIDATES = (
    "/etc/ssl/cert.pem",
    "/private/etc/ssl/cert.pem",
    "/opt/homebrew/etc/ca-certificates/cert.pem",
    "/usr/local/etc/ca-certificates/cert.pem",
)


@dataclasses.dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def diff_url(self) -> str:
        return f"{self.url}.diff"


@dataclasses.dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    file_types: Counter


@dataclasses.dataclass
class Review:
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> PullRequest:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return PullRequest(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
    )


def fetch_text(url: str, token: str | None = None) -> str:
    headers = {
        "Accept": "text/plain",
        "User-Agent": "claude-pr-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_certificate_error: urllib.error.URLError | None = None
    for context in certificate_contexts():
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30, context=context) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub returned HTTP {exc.code} for {url}") from exc
        except urllib.error.URLError as exc:
            if is_certificate_error(exc):
                last_certificate_error = exc
                continue
            raise RuntimeError(f"could not fetch {url}: {exc.reason}") from exc

    if last_certificate_error:
        raise RuntimeError(
            f"could not verify GitHub TLS certificate for {url}; set SSL_CERT_FILE to a CA bundle "
            "or provide --diff-file"
        ) from last_certificate_error
    raise RuntimeError(f"could not fetch {url}")


def certificate_contexts() -> Iterable[ssl.SSLContext | None]:
    yield None
    try:
        import certifi  # type: ignore

        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    for candidate in CA_BUNDLE_CANDIDATES:
        if os.path.exists(candidate):
            yield ssl.create_default_context(cafile=candidate)


def is_certificate_error(exc: urllib.error.URLError) -> bool:
    reason = getattr(exc, "reason", None)
    if isinstance(reason, ssl.SSLError):
        return True
    return "CERTIFICATE_VERIFY_FAILED" in str(reason)


def load_diff(pr: PullRequest, diff_file: str | None = None) -> str:
    if diff_file:
        with open(diff_file, "r", encoding="utf-8") as handle:
            return handle.read()
    return fetch_text(pr.diff_url, os.environ.get("GITHUB_TOKEN"))


def diff_stats(diff_text: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0
    file_types: Counter = Counter()

    for line in diff_text.splitlines():
        match = FILE_RE.match(line)
        if match and match.group(1) != "/dev/null":
            path = match.group(1)
            files.append(path)
            file_types[classify_file(path)] += 1
        elif HUNK_RE.match(line):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        hunks=hunks,
        file_types=file_types,
    )


def classify_file(path: str) -> str:
    if TEST_RE.search(path):
        return "tests"
    if DOC_RE.search(path):
        return "docs"
    if WORKFLOW_RE.search(path):
        return "workflow"
    if DEPENDENCY_RE.search(path):
        return "dependencies"
    return "code"


def analyze(pr: PullRequest, diff_text: str) -> Review:
    stats = diff_stats(diff_text)
    files = stats.files
    changed = len(files)
    tests_changed = stats.file_types["tests"]
    code_changed = stats.file_types["code"]
    docs_changed = stats.file_types["docs"]
    workflow_changed = stats.file_types["workflow"]
    dependency_changed = stats.file_types["dependencies"]

    summary = [
        (
            f"This PR changes {changed} file{'s' if changed != 1 else ''} "
            f"with {stats.additions} additions and {stats.deletions} deletions across {stats.hunks} diff hunks."
        )
    ]
    emphasis = describe_emphasis(stats.file_types)
    summary.append(
        f"The change is primarily {emphasis}, based on the touched file paths in {pr.owner}/{pr.repo}#{pr.number}."
    )

    risks: list[str] = []
    suggestions: list[str] = []

    if changed == 0:
        risks.append("The diff is empty or could not be parsed, so there is no implementation evidence to review.")
        suggestions.append("Re-run the tool with an accessible public PR URL or provide a local diff file.")
    if code_changed and tests_changed == 0:
        risks.append("Code files changed without an obvious test file in the diff.")
        suggestions.append("Add or update focused tests that exercise the changed behavior, including at least one failure-path case.")
    if workflow_changed:
        risks.append("Workflow or action configuration changed, which can affect repository permissions, secrets, or CI behavior.")
        suggestions.append("Document the intended token permissions and add a dry-run or restricted-permission validation path.")
    if dependency_changed:
        risks.append("Dependency lock or manifest files changed, which can introduce supply-chain or runtime drift.")
        suggestions.append("Include dependency-diff evidence and explain why each new or upgraded dependency is required.")
    if any(SENSITIVE_RE.search(path) for path in files):
        risks.append("The PR touches paths whose names suggest credentials, secrets, or key material.")
        suggestions.append("Verify no secret values are committed and add redaction or fixture guidance if sample data is needed.")
    if stats.additions + stats.deletions > 600:
        risks.append("The patch is large enough that unrelated behavior may be mixed into the same review surface.")
        suggestions.append("Split unrelated concerns or provide a reviewer map that ties each file group to an acceptance criterion.")
    if docs_changed and changed == docs_changed:
        risks.append("This appears to be documentation-only, so any claimed runtime behavior depends on external implementation evidence.")
        suggestions.append("Link the implementation PR or include executable verification if the bounty expects working code.")
    if not risks:
        risks.append("No high-risk patterns were detected from the diff structure alone.")
    if not suggestions:
        suggestions.append("Keep the PR description aligned with the changed files and include exact commands used for validation.")

    confidence = confidence_level(stats, risks)
    return Review(summary=summary[:2], risks=risks, suggestions=suggestions, confidence=confidence)


def describe_emphasis(file_types: Counter) -> str:
    if not file_types:
        return "unclassified"
    ordered = file_types.most_common()
    if len(ordered) == 1:
        return ordered[0][0]
    top = ", ".join(f"{kind} ({count})" for kind, count in ordered[:3])
    return f"a mix of {top}"


def confidence_level(stats: DiffStats, risks: Iterable[str]) -> str:
    risk_count = sum(1 for _ in risks)
    if not stats.files or stats.additions + stats.deletions == 0:
        return "Low"
    if stats.file_types["code"] and stats.file_types["tests"] == 0:
        return "Medium"
    if risk_count >= 4 or stats.additions + stats.deletions > 900:
        return "Medium"
    return "High"


def render_markdown(pr: PullRequest, review: Review) -> str:
    summary_text = " ".join(review.summary)
    return "\n".join(
        [
            "## Claude PR Review",
            "",
            f"Target: {pr.url}",
            "",
            "### Summary of Changes",
            "",
            summary_text,
            "",
            "### Identified Risks",
            "",
            *[f"- {item}" for item in review.risks],
            "",
            "### Improvement Suggestions",
            "",
            *[f"- {item}" for item in review.suggestions],
            "",
            f"### Confidence Score: {review.confidence}",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Generate a structured Markdown review from a GitHub PR diff.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
            """
        ),
    )
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--diff-file", help="Use a local unified diff instead of fetching from GitHub")
    parser.add_argument("--output", help="Write Markdown review to this file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        pr = parse_pr_url(args.pr)
        diff_text = load_diff(pr, args.diff_file)
        markdown = render_markdown(pr, analyze(pr, diff_text))
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
