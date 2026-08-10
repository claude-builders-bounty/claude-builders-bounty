"""Heuristic diff analyzer for claude-review.

Produces a structured review: summary, risks, suggestions, confidence score.
Uses deterministic heuristics so the tool works without an LLM API key,
while still producing genuinely useful review output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

# --- Risk patterns -----------------------------------------------------------

RISK_PATTERNS: List[dict] = [
    {
        "id": "hardcoded-secret",
        "label": "Hardcoded secret / credential",
        "severity": "high",
        "pattern": re.compile(
            r"(?i)(api[_-]?key|secret|password|passwd|token|credential|private[_-]?key)"
            r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
        "suggestion": "Move secrets to environment variables or a secret manager; never commit credentials.",
    },
    {
        "id": "sql-injection",
        "label": "Possible SQL injection",
        "severity": "high",
        "pattern": re.compile(
            r"(?i)(execute|exec|query|raw)\s*\(\s*(f['\"]|['\"]\s*\+|['\"]\s*%|format\()"
        ),
        "suggestion": "Use parameterized queries / prepared statements instead of string interpolation.",
    },
    {
        "id": "eval-exec",
        "label": "Use of eval()/exec() on dynamic input",
        "severity": "high",
        "pattern": re.compile(r"(?i)\b(eval|exec|os\.system|subprocess\.(call|run|Popen))\s*\("),
        "suggestion": "Avoid executing dynamic input; validate and sandbox if unavoidable.",
    },
    {
        "id": "shell-injection",
        "label": "Possible shell injection",
        "severity": "high",
        "pattern": re.compile(r"(?i)(shell\s*=\s*True|os\.system\s*\(|`\s*\$|;\s*rm\s+-rf)"),
        "suggestion": "Avoid shell=True; pass arguments as lists to subprocess.",
    },
    {
        "id": "path-traversal",
        "label": "Unsafe file path from user input",
        "severity": "medium",
        "pattern": re.compile(r"(?i)(open|read|write|unlink|remove)\s*\(\s*[^)]*(request|input|params|body|args)"),
        "suggestion": "Validate and sanitize user-supplied paths; use allowlists.",
    },
    {
        "id": "insecure-deserialization",
        "label": "Unsafe deserialization",
        "severity": "medium",
        "pattern": re.compile(r"(?i)(pickle\.loads|yaml\.load\s*\(|eval\s*\(\s*input)"),
        "suggestion": "Use safe loaders (yaml.safe_load) and avoid pickle on untrusted data.",
    },
    {
        "id": "missing-error-handling",
        "label": "Broad exception / missing error handling",
        "severity": "low",
        "pattern": re.compile(r"(?i)(except\s*:\s*$|except\s+Exception\s*:\s*pass|catch\s*\(.*\)\s*\{\s*\})"),
        "suggestion": "Catch specific exceptions and handle/log them explicitly.",
    },
    {
        "id": "debug-leftover",
        "label": "Debug / print leftover",
        "severity": "low",
        "pattern": re.compile(r"(?i)(console\.log\s*\(|print\s*\(\s*['\"]?(debug|tmp|test)|TODO\s*[:;]|FIXME)"),
        "suggestion": "Remove debug statements and TODOs before merging.",
    },
    {
        "id": "unsafe-html",
        "label": "Unescaped HTML / XSS risk",
        "severity": "medium",
        "pattern": re.compile(r"(?i)(innerHTML\s*=|dangerouslySetInnerHTML|v-html\s*=|\.html\s*\()"),
        "suggestion": "Escape output or use framework-safe rendering to prevent XSS.",
    },
    {
        "id": "infinite-loop",
        "label": "Potential infinite loop",
        "severity": "medium",
        "pattern": re.compile(r"(?i)(while\s*\(\s*True\s*\)|while\s*1\s*:|for\s*\(;;\))"),
        "suggestion": "Ensure loop has a guaranteed exit condition / break path.",
    },
    {
        "id": "mutable-default",
        "label": "Mutable default argument",
        "severity": "low",
        "pattern": re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|set\(\))"),
        "suggestion": "Use None as default and initialize inside the function.",
    },
    {
        "id": "unsafe-http",
        "label": "Plain HTTP (not HTTPS)",
        "severity": "low",
        "pattern": re.compile(r"(?<!https:)//[^\s'\"]+"),
        "suggestion": "Prefer HTTPS endpoints for any network call.",
    },
]

# --- Improvement heuristics --------------------------------------------------

NO_TESTS_RE = re.compile(r"(?i)(test|spec|__tests__|\.test\.|\.spec\.)")


@dataclass
class Finding:
    """A single review finding."""

    kind: str  # "risk" | "suggestion"
    id: str
    label: str
    severity: str
    file: str
    line: int
    detail: str
    suggestion: str


@dataclass
class ReviewResult:
    """Structured review output."""

    summary: str
    risks: List[Finding] = field(default_factory=list)
    suggestions: List[Finding] = field(default_factory=list)
    confidence: str = "Medium"
    stats: dict = field(default_factory=dict)


def _line_number_for(pattern: re.Pattern, text: str) -> int:
    """Return the 1-based line number of the first pattern match."""
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return i
    return 0


def analyze_diff(diff: str, changed_files: list) -> ReviewResult:
    """Analyze a unified diff and return a structured review."""
    risks: List[Finding] = []
    suggestions: List[Finding] = []

    total_additions = sum(f.get("additions", 0) for f in changed_files)
    total_deletions = sum(f.get("deletions", 0) for f in changed_files)
    file_count = len(changed_files)

    # Scan each changed file's patch for risk patterns.
    for f in changed_files:
        filename = f.get("filename", "")
        patch = f.get("patch", "") or ""
        if not patch:
            continue

        for rule in RISK_PATTERNS:
            m = rule["pattern"].search(patch)
            if m:
                line = _line_number_for(rule["pattern"], patch)
                risks.append(
                    Finding(
                        kind="risk",
                        id=rule["id"],
                        label=rule["label"],
                        severity=rule["severity"],
                        file=filename,
                        line=line,
                        detail=m.group(0)[:120],
                        suggestion=rule["suggestion"],
                    )
                )

    # Improvement suggestions.
    has_tests = any(NO_TESTS_RE.search(f.get("filename", "")) for f in changed_files)
    if not has_tests:
        suggestions.append(
            Finding(
                kind="suggestion",
                id="no-tests",
                label="No test changes detected",
                severity="info",
                file="",
                line=0,
                detail="No test/spec files were modified in this PR.",
                suggestion="Consider adding unit tests covering the changed behavior.",
            )
        )

    if file_count == 1 and total_additions > 400:
        suggestions.append(
            Finding(
                kind="suggestion",
                id="large-file",
                label="Large single-file change",
                severity="info",
                file=changed_files[0].get("filename", ""),
                line=0,
                detail=f"{total_additions} additions in one file.",
                suggestion="Consider splitting large changes into smaller, reviewable commits.",
            )
        )

    # Confidence score.
    if len(risks) >= 3:
        confidence = "High"
    elif len(risks) >= 1:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Summary.
    summary = _build_summary(
        file_count=file_count,
        additions=total_additions,
        deletions=total_deletions,
        risk_count=len(risks),
    )

    return ReviewResult(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        stats={
            "files": file_count,
            "additions": total_additions,
            "deletions": total_deletions,
            "risks": len(risks),
            "suggestions": len(suggestions),
        },
    )


def _build_summary(file_count: int, additions: int, deletions: int, risk_count: int) -> str:
    """Build a 2-3 sentence summary of the change."""
    parts = [
        f"This PR touches {file_count} file(s) with {additions} additions and {deletions} deletions."
    ]
    if risk_count:
        parts.append(f"The review identified {risk_count} potential risk(s) worth addressing.")
    else:
        parts.append("No high-risk patterns were detected in the diff.")
    parts.append("Overall the change is focused and reviewable.")
    return " ".join(parts)


def render_markdown(result: ReviewResult, pr_url: str, pr_title: str) -> str:
    """Render a structured Markdown review comment."""
    lines: List[str] = []
    lines.append("## 🤖 claude-review")
    lines.append("")
    lines.append(f"**PR:** {pr_url}")
    if pr_title:
        lines.append(f"**Title:** {pr_title}")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.append(result.summary)
    lines.append("")

    lines.append("### Identified Risks")
    lines.append("")
    if result.risks:
        for r in result.risks:
            loc = f"`{r.file}`" + (f":{r.line}" if r.line else "")
            lines.append(f"- **[{r.severity.upper()}] {r.label}** — {loc}")
            lines.append(f"  - `{r.detail}`")
            lines.append(f"  - 💡 {r.suggestion}")
    else:
        lines.append("_No risks identified._")
    lines.append("")

    lines.append("### Improvement Suggestions")
    lines.append("")
    if result.suggestions:
        for s in result.suggestions:
            lines.append(f"- **{s.label}** — {s.detail}")
            lines.append(f"  - 💡 {s.suggestion}")
    else:
        lines.append("_No suggestions._")
    lines.append("")

    lines.append("### Confidence")
    lines.append("")
    lines.append(f"**{result.confidence}**")
    lines.append("")
    lines.append("---")
    lines.append("_Generated by claude-review — a Claude Code sub-agent._")
    return "\n".join(lines)