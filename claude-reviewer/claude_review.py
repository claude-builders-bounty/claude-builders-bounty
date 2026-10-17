#!/usr/bin/env python3
"""
claude-review: Claude Code Sub-Agent & CLI for Automated Pull Request Reviews.

Analyzes a GitHub Pull Request URL or unified git diff and produces a
structured Markdown review comment containing:
  1. Summary of changes (2-3 sentences)
  2. Identified risks (bulleted list)
  3. Improvement suggestions (bulleted list)
  4. Confidence score: Low / Medium / High

Zero third-party dependencies required (uses Python 3 standard library).
Supports Anthropic Claude API (via ANTHROPIC_API_KEY) with an automatic
deterministic static-analysis engine fallback for offline/CI reliability.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class FileDiff:
    """Represents parsed changes for a single file in a unified diff."""
    old_path: str
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    added_lines: List[Tuple[int, str]] = field(default_factory=list)
    removed_lines: List[Tuple[int, str]] = field(default_factory=list)

    @property
    def display_path(self) -> str:
        if self.new_path and self.new_path != "/dev/null":
            return self.new_path
        return self.old_path


@dataclass
class RiskFinding:
    """Represents a concrete risk identified in the diff."""
    severity: str  # "High", "Medium", "Low"
    file_path: str
    line_number: Optional[int]
    category: str
    description: str
    suggestion: str


@dataclass
class ReviewResult:
    """Structured PR review output matching the bounty acceptance criteria."""
    summary_sentences: List[str]
    risks: List[str]
    suggestions: List[str]
    confidence: str  # "Low", "Medium", "High"
    confidence_reason: str
    pr_title: Optional[str] = None
    pr_url: Optional[str] = None
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    engine: str = "static"

    def to_markdown(self) -> str:
        """Render the structured review in the exact required Markdown format."""
        sentences = [s.strip() for s in self.summary_sentences if s.strip()]
        if len(sentences) < 2:
            sentences.append(
                f"The patch touches {self.files_changed} file(s) with "
                f"+{self.insertions}/-{self.deletions} line changes."
            )
        elif len(sentences) > 3:
            sentences = sentences[:3]

        summary_text = " ".join(sentences)
        header = "## Pull Request Review\n\n"
        if self.pr_title or self.pr_url:
            meta_parts = []
            if self.pr_title:
                meta_parts.append(f"**PR:** {self.pr_title}")
            if self.pr_url:
                meta_parts.append(f"**URL:** {self.pr_url}")
            header += " | ".join(meta_parts) + "\n\n"

        risk_lines = (
            "\n".join(f"- {r}" for r in self.risks)
            if self.risks
            else "- **Low Risk:** No critical security, data-loss, or breaking API issues detected in the diff."
        )
        suggestion_lines = (
            "\n".join(f"- {s}" for s in self.suggestions)
            if self.suggestions
            else "- Add targeted unit tests covering edge cases introduced by these changes."
        )

        valid_scores = {"Low", "Medium", "High"}
        score = self.confidence.capitalize() if self.confidence else "High"
        if score not in valid_scores:
            score = "Medium"

        return (
            f"{header}"
            f"### Summary of Changes\n"
            f"{summary_text}\n\n"
            f"### Identified Risks\n"
            f"{risk_lines}\n\n"
            f"### Improvement Suggestions\n"
            f"{suggestion_lines}\n\n"
            f"### Confidence Score\n"
            f"**Confidence Score: {score}** — {self.confidence_reason}\n"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the review result to a JSON-compatible dictionary."""
        return {
            "pr_title": self.pr_title,
            "pr_url": self.pr_url,
            "summary": " ".join(self.summary_sentences[:3]),
            "identified_risks": self.risks,
            "improvement_suggestions": self.suggestions,
            "confidence_score": self.confidence,
            "confidence_reason": self.confidence_reason,
            "metrics": {
                "files_changed": self.files_changed,
                "insertions": self.insertions,
                "deletions": self.deletions,
                "engine": self.engine,
            },
        }


# ---------------------------------------------------------------------------
# GitHub PR URL Parser & Fetcher
# ---------------------------------------------------------------------------

PR_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)(?:/.*)?$"
)


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pull_number)."""
    match = PR_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(
            f"Invalid GitHub Pull Request URL: '{url}'. "
            "Expected format: https://github.com/<owner>/<repo>/pull/<number>"
        )
    return (
        match.group("owner"),
        match.group("repo"),
        int(match.group("number")),
    )


def fetch_github_pr(
    pr_url: str, github_token: Optional[str] = None, timeout: int = 20
) -> Tuple[Dict[str, Any], str]:
    """Fetch PR metadata and unified diff from the GitHub REST API."""
    owner, repo, number = parse_pr_url(pr_url)
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    headers_common = {
        "User-Agent": "claude-review-agent/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if github_token:
        headers_common["Authorization"] = f"Bearer {github_token}"

    # 1. Fetch PR JSON metadata
    meta_req = urllib.request.Request(
        api_base,
        headers={**headers_common, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(meta_req, timeout=timeout) as resp:
            metadata = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f"GitHub API error ({exc.code}) fetching PR metadata for {pr_url}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error fetching PR metadata for {pr_url}: {exc.reason}"
        ) from exc

    # 2. Fetch PR unified diff
    diff_req = urllib.request.Request(
        api_base,
        headers={**headers_common, "Accept": "application/vnd.github.v3.diff"},
    )
    try:
        with urllib.request.urlopen(diff_req, timeout=timeout) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f"GitHub API error ({exc.code}) fetching PR diff for {pr_url}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error fetching PR diff for {pr_url}: {exc.reason}"
        ) from exc

    return metadata, diff_text


def post_github_pr_comment(
    pr_url: str, markdown_body: str, github_token: str, timeout: int = 20
) -> Dict[str, Any]:
    """Post the structured review comment to the GitHub Pull Request."""
    owner, repo, number = parse_pr_url(pr_url)
    comments_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    )
    payload = json.dumps({"body": markdown_body}).encode("utf-8")
    req = urllib.request.Request(
        comments_url,
        data=payload,
        method="POST",
        headers={
            "User-Agent": "claude-review-agent/1.0",
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Unified Diff Parser
# ---------------------------------------------------------------------------

HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,\d+)? \+(?P<new_start>\d+)(?:,\d+)? @@"
)


def parse_unified_diff(diff_text: str) -> List[FileDiff]:
    """Parse a unified git diff into a list of FileDiff objects."""
    files: List[FileDiff] = []
    current_file: Optional[FileDiff] = None
    old_line_no = 0
    new_line_no = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            old_p = parts[2][2:] if len(parts) >= 4 and parts[2].startswith("a/") else ""
            new_p = parts[3][2:] if len(parts) >= 4 and parts[3].startswith("b/") else ""
            current_file = FileDiff(old_path=old_p, new_path=new_p)
            files.append(current_file)
            continue

        if raw_line.startswith("--- "):
            path_val = raw_line[4:].strip()
            if path_val.startswith("a/"):
                path_val = path_val[2:]
            if current_file is None:
                current_file = FileDiff(old_path=path_val, new_path=path_val)
                files.append(current_file)
            else:
                current_file.old_path = path_val
            if path_val == "/dev/null":
                current_file.is_new = True
            continue

        if raw_line.startswith("+++ "):
            path_val = raw_line[4:].strip()
            if path_val.startswith("b/"):
                path_val = path_val[2:]
            if current_file is None:
                current_file = FileDiff(old_path=path_val, new_path=path_val)
                files.append(current_file)
            else:
                current_file.new_path = path_val
            if path_val == "/dev/null":
                current_file.is_deleted = True
            continue

        if current_file is None:
            continue

        if raw_line.startswith("new file mode"):
            current_file.is_new = True
            continue
        if raw_line.startswith("deleted file mode"):
            current_file.is_deleted = True
            continue

        hunk_match = HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            old_line_no = int(hunk_match.group("old_start"))
            new_line_no = int(hunk_match.group("new_start"))
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            current_file.added_lines.append((new_line_no, raw_line[1:]))
            new_line_no += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            current_file.removed_lines.append((old_line_no, raw_line[1:]))
            old_line_no += 1
        elif raw_line.startswith(" "):
            old_line_no += 1
            new_line_no += 1

    return files


# ---------------------------------------------------------------------------
# Static Heuristic Analyzer (Deterministic Engine & Fallback)
# ---------------------------------------------------------------------------

RISK_PATTERNS: List[Tuple[str, str, re.Pattern[str], str, str]] = [
    (
        "High",
        "Hardcoded Secret / Credential",
        re.compile(
            r"(?i)(?:api[_-]?key|secret[_-]?key|password|passwd|private[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-./+=]{8,}['\"]|"
            r"(?:sk-[A-Za-z0-9\-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"
        ),
        "Potential hardcoded credential, API key, or secret token detected in source code.",
        "Move sensitive credentials to environment variables (`os.environ` / `process.env`) and rotate any exposed keys immediately.",
    ),
    (
        "High",
        "Command Injection / Unsafe Shell Execution",
        re.compile(
            r"(?:subprocess\.(?:run|Popen|call|check_output)\([^)]*shell\s*=\s*True)|"
            r"(?:os\.system\s*\()|(?:child_process\.exec\s*\()"
        ),
        "Shell command execution with `shell=True` or unvalidated command string increases command injection risk.",
        "Pass command arguments as an explicit list (`shell=False` or `execFile`) and validate/sanitize all external inputs.",
    ),
    (
        "High",
        "Dynamic Code Execution",
        re.compile(r"\b(?:eval|exec)\s*\("),
        "Use of dynamic code evaluation (`eval`/`exec`) can allow arbitrary code execution if untrusted input reaches this path.",
        "Replace `eval`/`exec` with safe parsers such as `json.loads`, `ast.literal_eval`, or explicit dispatch tables.",
    ),
    (
        "High",
        "Potential SQL Injection",
        re.compile(
            r"(?i)(?:\bf(['\"]).*\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b.*\{[^}]+\}.*\1)|"
            r"(?:(['\"]).*\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b.*\2\s*(?:\+|%\s*\w+|\.format\())"
        ),
        "SQL statement appears to be constructed via string interpolation or concatenation rather than parameterized queries.",
        "Use parameterized query placeholders (`?` or `$1`) provided by the database driver instead of f-strings or string concatenation.",
    ),
    (
        "Medium",
        "Broad / Bare Exception Handler",
        re.compile(r"^\s*except(?:\s+(?:Exception|BaseException))?\s*:\s*$"),
        "Broad or bare `except:` block may silently swallow unexpected runtime errors or system interrupts.",
        "Catch specific exception classes (e.g., `ValueError`, `KeyError`, `HTTPError`) and log or propagate unexpected failures.",
    ),
    (
        "Medium",
        "Insecure TLS / SSL Verification Disabled",
        re.compile(r"(?:verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?)"),
        "TLS certificate verification appears disabled, exposing network calls to man-in-the-middle (MITM) attacks.",
        "Keep TLS verification enabled (`verify=True`) and configure a custom CA bundle if connecting to internal endpoints.",
    ),
    (
        "Low",
        "Leftover Debug / Console Output",
        re.compile(r"\b(?:console\.log|debugger|pdb\.set_trace|breakpoint\(\))\b"),
        "Debug statement or interactive breakpoint left in modified code.",
        "Remove leftover debug statements or replace them with structured logger calls before merging.",
    ),
    (
        "Low",
        "Unresolved TODO / FIXME Marker",
        re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b"),
        "Unresolved `TODO`/`FIXME` marker introduced in the diff.",
        "Resolve the deferred work item or link it to a tracked GitHub issue number.",
    ),
]


def is_test_file(path: str) -> bool:
    """Return True if the file path looks like a unit or integration test file."""
    lower = path.lower()
    base = os.path.basename(lower)
    return (
        "test" in lower
        or "spec" in lower
        or base.startswith("test_")
        or base.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"))
    )


def is_code_file(path: str) -> bool:
    """Return True if the file path is an executable source code file."""
    _, ext = os.path.splitext(path.lower())
    return ext in {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".php", ".sh", ".c", ".cpp"
    }


def analyze_diff_statically(
    diff_text: str,
    pr_title: Optional[str] = None,
    pr_url: Optional[str] = None,
) -> ReviewResult:
    """Perform deterministic static analysis on a unified diff."""
    parsed_files = parse_unified_diff(diff_text)
    files_changed = len(parsed_files)
    total_insertions = sum(len(f.added_lines) for f in parsed_files)
    total_deletions = sum(len(f.removed_lines) for f in parsed_files)

    if files_changed == 0:
        return ReviewResult(
            summary_sentences=[
                "No file modifications were detected in the provided diff input.",
                "The patch contains 0 changed files, 0 insertions, and 0 deletions.",
            ],
            risks=["**Low Risk:** Empty diff provided; verify that the target branch or commit range contains changes."],
            suggestions=["Ensure the PR or diff source includes committed changes before running the review agent."],
            confidence="High",
            confidence_reason="Diff input was empty and required no heuristic ambiguity resolution.",
            pr_title=pr_title,
            pr_url=pr_url,
            files_changed=0,
            insertions=0,
            deletions=0,
            engine="static",
        )

    findings: List[RiskFinding] = []
    seen_keys = set()

    for fdiff in parsed_files:
        for line_no, content in fdiff.added_lines:
            for severity, category, pattern, desc, sugg in RISK_PATTERNS:
                if pattern.search(content):
                    dedup_key = (fdiff.display_path, category, line_no)
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        findings.append(
                            RiskFinding(
                                severity=severity,
                                file_path=fdiff.display_path,
                                line_number=line_no,
                                category=category,
                                description=desc,
                                suggestion=sugg,
                            )
                        )

    # Check if production code changed without test updates
    prod_code_files = [
        f.display_path for f in parsed_files if is_code_file(f.display_path) and not is_test_file(f.display_path)
    ]
    test_files = [f.display_path for f in parsed_files if is_test_file(f.display_path)]

    if prod_code_files and not test_files:
        findings.append(
            RiskFinding(
                severity="Medium",
                file_path=prod_code_files[0],
                line_number=None,
                category="Missing Test Coverage",
                description=(
                    f"Production source files ({', '.join(prod_code_files[:3])}) were modified "
                    "without corresponding unit or integration test updates."
                ),
                suggestion=(
                    f"Add unit tests covering the new logic and edge cases in `{prod_code_files[0]}` "
                    "to prevent regressions."
                ),
            )
        )

    # Check for large diff size risk
    if total_insertions + total_deletions > 500:
        findings.append(
            RiskFinding(
                severity="Medium",
                file_path=parsed_files[0].display_path,
                line_number=None,
                category="Large Patch Surface",
                description=(
                    f"Large change set (+{total_insertions}/-{total_deletions} lines across "
                    f"{files_changed} files) increases review complexity and merge conflict risk."
                ),
                suggestion="Consider splitting independent refactors and feature additions into smaller, focused PRs.",
            )
        )

    # Sort findings by severity (High -> Medium -> Low)
    severity_rank = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda x: severity_rank.get(x.severity, 3))

    # Build 2-3 sentence summary
    file_names = [f.display_path for f in parsed_files[:3]]
    more_suffix = f" and {files_changed - 3} other file(s)" if files_changed > 3 else ""
    new_count = sum(1 for f in parsed_files if f.is_new)
    del_count = sum(1 for f in parsed_files if f.is_deleted)

    sentence_1 = (
        f"This pull request ({pr_title}) updates {files_changed} file(s) "
        f"(`{'`, `'.join(file_names)}`{more_suffix}) with +{total_insertions} additions and -{total_deletions} deletions."
        if pr_title
        else f"This change set modifies {files_changed} file(s) "
        f"(`{'`, `'.join(file_names)}`{more_suffix}) with +{total_insertions} additions and -{total_deletions} deletions."
    )

    change_types = []
    if new_count:
        change_types.append(f"{new_count} newly added file(s)")
    if del_count:
        change_types.append(f"{del_count} deleted file(s)")
    if prod_code_files:
        change_types.append(f"{len(prod_code_files)} implementation module(s)")
    if test_files:
        change_types.append(f"{len(test_files)} test file(s)")

    sentence_2 = (
        f"The patch encompasses {', '.join(change_types)}."
        if change_types
        else "The patch primarily updates documentation and configuration files."
    )

    high_count = sum(1 for item in findings if item.severity == "High")
    med_count = sum(1 for item in findings if item.severity == "Medium")
    if high_count > 0:
        sentence_3 = (
            f"Automated review flagged {high_count} high-severity and {med_count} medium-severity "
            "risk(s) that should be addressed before merging."
        )
    elif findings:
        sentence_3 = (
            f"Automated review identified {len(findings)} minor/medium finding(s) with no critical blockers."
        )
    else:
        sentence_3 = "Automated analysis found clean code changes with accompanying test coverage and no high-severity risks."

    risks_formatted: List[str] = []
    suggestions_formatted: List[str] = []
    seen_suggestions = set()

    for item in findings[:8]:
        loc = f"`{item.file_path}:{item.line_number}`" if item.line_number else f"`{item.file_path}`"
        risks_formatted.append(
            f"**[{item.severity}] {item.category}** ({loc}): {item.description}"
        )
        if item.suggestion not in seen_suggestions:
            seen_suggestions.add(item.suggestion)
            suggestions_formatted.append(item.suggestion)

    if not suggestions_formatted:
        suggestions_formatted.append(
            "Verify all CI checks pass and consider adding edge-case assertions for boundary inputs."
        )

    # Compute Confidence Score
    if total_insertions + total_deletions > 800:
        confidence = "Medium"
        confidence_reason = (
            "Large diff surface area may involve cross-module side effects outside the immediate diff context."
        )
    elif high_count > 0:
        confidence = "High"
        confidence_reason = (
            "High-severity security/reliability patterns were deterministically matched with exact line numbers."
        )
    else:
        confidence = "High"
        confidence_reason = (
            f"All {files_changed} changed file(s) (+{total_insertions}/-{total_deletions} lines) "
            "were completely parsed and analyzed against security and quality rules."
        )

    return ReviewResult(
        summary_sentences=[sentence_1, sentence_2, sentence_3],
        risks=risks_formatted,
        suggestions=suggestions_formatted,
        confidence=confidence,
        confidence_reason=confidence_reason,
        pr_title=pr_title,
        pr_url=pr_url,
        files_changed=files_changed,
        insertions=total_insertions,
        deletions=total_deletions,
        engine="static",
    )


# ---------------------------------------------------------------------------
# Anthropic Claude API Engine
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Staff Software Engineer and Security Reviewer operating as a Claude Code PR Review Sub-Agent.
Given a Pull Request unified diff and static analysis pre-check notes, return a JSON object with EXACTLY these keys:
{
  "summary_sentences": ["Sentence 1.", "Sentence 2.", "Sentence 3 (optional)."],
  "risks": ["**[High|Medium|Low] Category** (`file:line`): description", ...],
  "suggestions": ["Actionable improvement suggestion 1", ...],
  "confidence": "Low" | "Medium" | "High",
  "confidence_reason": "One concise sentence explaining the confidence level."
}
Constraints:
- `summary_sentences` MUST contain 2 or 3 sentences.
- `confidence` MUST be one of: "Low", "Medium", "High".
- Return ONLY valid JSON without markdown code fences."""


def analyze_with_claude_api(
    diff_text: str,
    static_baseline: ReviewResult,
    api_key: str,
    model: str = "claude-3-7-sonnet-latest",
    timeout: int = 45,
) -> ReviewResult:
    """Call Anthropic Messages API to enrich the PR review, falling back cleanly on error."""
    truncated_diff = diff_text[:60000]
    user_message = (
        f"PR Title: {static_baseline.pr_title or 'N/A'}\n"
        f"PR URL: {static_baseline.pr_url or 'N/A'}\n"
        f"Static Pre-Check Findings: {json.dumps(static_baseline.to_dict())}\n\n"
        f"Unified Diff:\n{truncated_diff}"
    )

    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 1500,
            "temperature": 0.1,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "claude-review-agent/1.0",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="replace"))

    content_blocks = body.get("content", [])
    text_out = "".join(
        block.get("text", "") for block in content_blocks if block.get("type") == "text"
    ).strip()

    # Strip optional markdown code fences if present
    if text_out.startswith("```"):
        text_out = re.sub(r"^```(?:json)?\s*", "", text_out)
        text_out = re.sub(r"\s*```$", "", text_out)

    parsed = json.loads(text_out)
    sentences = parsed.get("summary_sentences") or static_baseline.summary_sentences
    if isinstance(sentences, str):
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sentences) if s.strip()]

    return ReviewResult(
        summary_sentences=sentences[:3],
        risks=parsed.get("risks") or static_baseline.risks,
        suggestions=parsed.get("suggestions") or static_baseline.suggestions,
        confidence=parsed.get("confidence", static_baseline.confidence),
        confidence_reason=parsed.get("confidence_reason", static_baseline.confidence_reason),
        pr_title=static_baseline.pr_title,
        pr_url=static_baseline.pr_url,
        files_changed=static_baseline.files_changed,
        insertions=static_baseline.insertions,
        deletions=static_baseline.deletions,
        engine=f"claude ({model})",
    )


# ---------------------------------------------------------------------------
# Main Orchestrator & CLI Entrypoint
# ---------------------------------------------------------------------------

def run_review(
    pr_url: Optional[str] = None,
    diff_source: Optional[str] = None,
    pr_title: Optional[str] = None,
    api_key: Optional[str] = None,
    github_token: Optional[str] = None,
    model: str = "claude-3-7-sonnet-latest",
) -> ReviewResult:
    """Run the end-to-end PR review pipeline on a PR URL or diff input."""
    if not pr_url and diff_source is None:
        raise ValueError("Either --pr <github_pr_url> or --diff <path_or_stdin> must be provided.")

    resolved_title = pr_title
    if pr_url and diff_source is None:
        metadata, diff_text = fetch_github_pr(pr_url, github_token=github_token)
        resolved_title = resolved_title or metadata.get("title")
    else:
        diff_text = diff_source or ""

    baseline = analyze_diff_statically(diff_text, pr_title=resolved_title, pr_url=pr_url)

    effective_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if effective_key:
        try:
            return analyze_with_claude_api(
                diff_text=diff_text,
                static_baseline=baseline,
                api_key=effective_key,
                model=model,
            )
        except Exception as exc:
            sys.stderr.write(
                f"[claude-review] Warning: Claude API call failed ({exc}); using deterministic static analysis.\n"
            )

    return baseline


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code Sub-Agent that reviews a PR diff and outputs a structured Markdown comment.",
    )
    parser.add_argument(
        "--pr",
        dest="pr_url",
        help="GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--diff",
        dest="diff_path",
        help="Path to a unified .diff/.patch file, or '-' to read from stdin",
    )
    parser.add_argument(
        "--title",
        dest="pr_title",
        help="Optional Pull Request title when reviewing a local diff",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format: 'markdown' (default) or 'json'",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        help="Optional file path to write the review output",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review comment directly to the GitHub PR (requires GITHUB_TOKEN and --pr)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL", "claude-3-7-sonnet-latest"),
        help="Anthropic Claude model identifier (default: claude-3-7-sonnet-latest)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    diff_content: Optional[str] = None
    if args.diff_path:
        if args.diff_path == "-":
            diff_content = sys.stdin.read()
        else:
            with open(args.diff_path, "r", encoding="utf-8") as fh:
                diff_content = fh.read()
    elif not args.pr_url and not sys.stdin.isatty():
        diff_content = sys.stdin.read()

    if not args.pr_url and diff_content is None:
        parser.print_help(sys.stderr)
        return 2

    github_token = os.environ.get("GITHUB_TOKEN")
    try:
        result = run_review(
            pr_url=args.pr_url,
            diff_source=diff_content,
            pr_title=args.pr_title,
            github_token=github_token,
            model=args.model,
        )
    except Exception as exc:
        sys.stderr.write(f"[claude-review] Error: {exc}\n")
        return 1

    rendered = (
        json.dumps(result.to_dict(), indent=2)
        if args.format == "json"
        else result.to_markdown()
    )

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as out_fh:
            out_fh.write(rendered)
    else:
        sys.stdout.write(rendered)

    if args.post_comment:
        if not args.pr_url or not github_token:
            sys.stderr.write(
                "[claude-review] Error: --post-comment requires both --pr <url> and GITHUB_TOKEN.\n"
            )
            return 1
        post_github_pr_comment(args.pr_url, result.to_markdown(), github_token=github_token)

    return 0


if __name__ == "__main__":
    sys.exit(main())