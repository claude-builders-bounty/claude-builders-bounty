#!/usr/bin/env python3
"""
pr-review-agent: Automated PR code review with structured Markdown output.

Fetches a GitHub PR diff via `gh` CLI, performs static analysis,
and outputs a structured review comment.

Usage:
    python review.py --pr https://github.com/owner/repo/pull/123
    python review.py --pr owner/repo/123
    python review.py --diff path/to/changes.diff
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    category: str
    severity: Severity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ReviewResult:
    pr_url: str
    title: str
    summary: str
    findings: list[Finding] = field(default_factory=list)
    confidence: str = "Medium"
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


# ─── PR Fetching ──────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, PR number from URL or shorthand."""
    url = url.strip().rstrip("/")
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Shorthand: owner/repo/123
    m = re.match(r"([^/]+)/([^/]+)/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Invalid PR URL or shorthand: {url}")


def fetch_pr_metadata(owner: str, repo: str, number: int) -> dict:
    """Fetch PR metadata via gh CLI."""
    cmd = [
        "gh", "api", f"repos/{owner}/{repo}/pulls/{number}",
        "--jq", '{"title": .title, "body": .body, "user": .user.login, '
                '"changed_files": .changed_files, "additions": .additions, '
                '"deletions": .deletions, "state": .state, '
                '"base": .base.ref, "head": .head.ref}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR metadata: {result.stderr}")
    return json.loads(result.stdout)


def fetch_pr_diff(owner: str, repo: str, number: int) -> str:
    """Fetch PR diff via gh CLI."""
    cmd = [
        "gh", "api", f"repos/{owner}/{repo}/pulls/{number}",
        "--header", "Accept: application/vnd.github.v3.diff"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR diff: {result.stderr}")
    return result.stdout


def fetch_pr_files(owner: str, repo: str, number: int) -> list[dict]:
    """Fetch list of changed files in a PR."""
    cmd = [
        "gh", "api", f"repos/{owner}/{repo}/pulls/{number}/files",
        "--paginate",
        "--jq", '.[] | {"filename": .filename, "status": .status, '
                '"additions": .additions, "deletions": .deletions, "patch": .patch}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR files: {result.stderr}")
    files = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            files.append(json.loads(line))
    return files


# ─── Diff Analysis ────────────────────────────────────────────────────────────

# Patterns that indicate potential issues
RISK_PATTERNS: list[tuple[str, str, Severity, str]] = [
    # Security
    (r"(?i)(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]+['\"]",
     "security", Severity.CRITICAL, "Hardcoded credential or secret detected"),
    (r"(?i)eval\s*\(",
     "security", Severity.HIGH, "Use of eval() — potential code injection risk"),
    (r"(?i)exec\s*\(",
     "security", Severity.MEDIUM, "Use of exec() — review for injection vectors"),
    (r"(?i)subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True",
     "security", Severity.HIGH, "Shell=True in subprocess — command injection risk"),
    (r"(?i)pickle\.load",
     "security", Severity.HIGH, "Pickle deserialization — can execute arbitrary code"),
    (r"(?i)__import__\s*\(",
     "security", Severity.MEDIUM, "Dynamic import — review for untrusted input"),
    (r"(?i)verify\s*=\s*False",
     "security", Severity.HIGH, "SSL verification disabled"),
    (r"(?i)SELECT\s+\*\s+FROM.*WHERE.*\+|f['\"].*SELECT",
     "security", Severity.CRITICAL, "Potential SQL injection — use parameterized queries"),

    # Error handling
    (r"except\s*:", "quality", Severity.MEDIUM, "Bare except clause — catches all exceptions including KeyboardInterrupt"),
    (r"except\s+Exception\s*:", "quality", Severity.LOW, "Catching base Exception — consider more specific exceptions"),
    (r"pass\s*$", "quality", Severity.LOW, "Empty except block — swallowed error with no logging"),

    # Code quality
    (r"(?i)TODO|FIXME|HACK|XXX", "quality", Severity.LOW, "Unresolved TODO/FIXME comment"),
    (r"(?i)print\s*\(", "quality", Severity.LOW, "Debug print statement — remove before production"),
    (r"console\.log\s*\(", "quality", Severity.LOW, "Debug console.log — remove before production"),
    (r"(?i)@deprecated", "quality", Severity.MEDIUM, "Use of deprecated API"),

    # Performance
    (r"SELECT\s+\*\s+FROM", "performance", Severity.MEDIUM, "SELECT * — specify needed columns"),
    (r"(?i)sleep\s*\(\s*\d{2,}", "performance", Severity.MEDIUM, "Long sleep() call — potential performance issue"),
    (r"for .+ in .+:\s*\n\s+.+\.append\(", "performance", Severity.LOW, "Consider list comprehension for better performance"),

    # Type safety
    (r":\s*Any\b", "quality", Severity.LOW, "Type annotation uses Any — consider more specific type"),
    (r"# type:\s*ignore", "quality", Severity.LOW, "Type checking suppressed — verify this is intentional"),

    # Configuration
    (r"(?i)debug\s*=\s*True", "config", Severity.MEDIUM, "Debug mode enabled — disable before production"),
    (r"(?i)localhost|127\.0\.0\.1", "config", Severity.LOW, "Hardcoded localhost — verify this is intentional"),
]


def analyze_diff(diff_text: str) -> list[Finding]:
    """Analyze a diff for potential issues."""
    findings: list[Finding] = []
    current_file = None
    line_num = 0

    for line in diff_text.split("\n"):
        # Track which file we're in
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("--- a/"):
            continue
        if line.startswith("@@"):
            # Extract line number from hunk header
            m = re.search(r"\+(\d+)", line)
            if m:
                line_num = int(m.group(1))
            continue

        # Only analyze added lines
        if not line.startswith("+"):
            if line.strip():
                line_num += 1
            continue

        code_line = line[1:]  # Remove the leading +

        # Check all risk patterns
        for pattern, category, severity, message in RISK_PATTERNS:
            if re.search(pattern, code_line):
                findings.append(Finding(
                    category=category,
                    severity=severity,
                    message=message,
                    file=current_file,
                    line=line_num
                ))

        line_num += 1

    return findings


def compute_diff_stats(diff_text: str) -> dict:
    """Compute basic stats from the diff."""
    files = set()
    additions = 0
    deletions = 0

    for line in diff_text.split("\n"):
        if line.startswith("+++ b/"):
            files.add(line[6:])
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return {
        "files_changed": len(files),
        "additions": additions,
        "deletions": deletions
    }


# ─── Risk Assessment ──────────────────────────────────────────────────────────

def assess_risks(findings: list[Finding]) -> list[str]:
    """Summarize identified risks from findings."""
    risks: list[str] = []
    critical = [f for f in findings if f.severity == Severity.CRITICAL]
    high = [f for f in findings if f.severity == Severity.HIGH]
    medium = [f for f in findings if f.severity == Severity.MEDIUM]

    if critical:
        risks.append(f"**Critical**: {len(critical)} critical issue(s) found — "
                     f"must be addressed before merge")
        for f in critical:
            loc = f"{f.file}:{f.line}" if f.file else "unknown"
            risks.append(f"  - [{loc}] {f.message}")

    if high:
        risks.append(f"**High**: {len(high)} high-severity issue(s) — "
                     f"should be reviewed carefully")
        for f in high:
            loc = f"{f.file}:{f.line}" if f.file else "unknown"
            risks.append(f"  - [{loc}] {f.message}")

    if medium:
        risks.append(f"**Medium**: {len(medium)} medium-severity issue(s) — "
                     f"consider addressing")
        for f in medium:
            loc = f"{f.file}:{f.line}" if f.file else "unknown"
            risks.append(f"  - [{loc}] {f.message}")

    if not risks:
        risks.append("No significant risks identified.")

    return risks


def suggest_improvements(findings: list[Finding], stats: dict) -> list[str]:
    """Generate improvement suggestions based on findings and stats."""
    suggestions: list[str] = []

    categories = set(f.category for f in findings)

    if "security" in categories:
        suggestions.append(
            "Address all security findings before merge — "
            "hardcoded credentials and injection risks are blockers."
        )

    if "quality" in categories:
        quality_count = sum(1 for f in findings if f.category == "quality")
        if quality_count > 3:
            suggestions.append(
                f"Found {quality_count} code quality issues — "
                f"consider a cleanup pass before submitting."
            )

    if stats["additions"] > 500:
        suggestions.append(
            f"Large diff ({stats['additions']} additions) — "
            f"consider splitting into smaller, focused PRs for easier review."
        )

    if stats["files_changed"] > 20:
        suggestions.append(
            f"Touching {stats['files_changed']} files — "
            f"ensure all changes are related to the PR purpose."
        )

    # Check for missing tests
    all_files = set()
    for f in findings:
        if f.file:
            all_files.add(f.file)

    test_files = [f for f in all_files if "test" in f.lower() or "spec" in f.lower()]
    code_files = [f for f in all_files if f.endswith((".py", ".js", ".ts", ".go", ".rs"))
                  and "test" not in f.lower() and "spec" not in f.lower()]

    if code_files and not test_files:
        suggestions.append(
            "No test files changed — consider adding tests for the modified code."
        )

    if not suggestions:
        suggestions.append("No specific improvements suggested — code looks clean.")

    return suggestions


def compute_confidence(findings: list[Finding], stats: dict) -> str:
    """Compute confidence level for the review."""
    critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    high = sum(1 for f in findings if f.severity == Severity.HIGH)

    if critical > 0:
        return "High"
    if high > 0:
        return "High"
    if stats["additions"] > 1000:
        return "Low"
    if stats["additions"] > 300:
        return "Medium"
    return "High"


# ─── Output Formatting ────────────────────────────────────────────────────────

def format_review(result: ReviewResult) -> str:
    """Format the review result as structured Markdown."""
    lines: list[str] = []

    lines.append("## PR Review")
    lines.append("")

    # Summary
    lines.append("### Summary")
    lines.append("")
    lines.append(result.summary)
    lines.append("")

    # Stats
    lines.append(f"**Files changed:** {result.files_changed} | "
                 f"**Additions:** +{result.additions} | "
                 f"**Deletions:** -{result.deletions}")
    lines.append("")

    # Risks
    lines.append("### Identified Risks")
    lines.append("")
    risks = assess_risks(result.findings)
    for risk in risks:
        lines.append(f"- {risk}")
    lines.append("")

    # Suggestions
    lines.append("### Improvement Suggestions")
    lines.append("")
    suggestions = suggest_improvements(result.findings, {
        "files_changed": result.files_changed,
        "additions": result.additions,
        "deletions": result.deletions
    })
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")

    # Confidence
    lines.append(f"### Confidence: {result.confidence}")
    lines.append("")

    # Detailed findings
    if result.findings:
        lines.append("<details>")
        lines.append("<summary>All Findings</summary>")
        lines.append("")
        lines.append("| Severity | Category | File | Line | Issue |")
        lines.append("|----------|----------|------|------|-------|")
        for f in sorted(result.findings, key=lambda x: list(Severity).index(x.severity)):
            sev = f.severity.value.upper()
            loc = f.file or "-"
            ln = str(f.line) if f.line else "-"
            lines.append(f"| {sev} | {f.category} | {loc} | {ln} | {f.message} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by pr-review-agent*")

    return "\n".join(lines)


def generate_summary(title: str, stats: dict, findings: list[Finding]) -> str:
    """Generate a 2-3 sentence summary of the PR."""
    parts: list[str] = []

    parts.append(
        f"This PR modifies {stats['files_changed']} file(s) with "
        f"+{stats['additions']}/-{stats['deletions']} lines changed."
    )

    severity_counts = {}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    if severity_counts.get(Severity.CRITICAL, 0) > 0:
        parts.append(
            f"Found {severity_counts[Severity.CRITICAL]} critical issue(s) "
            f"that require immediate attention."
        )
    elif severity_counts.get(Severity.HIGH, 0) > 0:
        parts.append(
            f"Identified {severity_counts[Severity.HIGH]} high-severity concern(s) "
            f"for review."
        )
    elif findings:
        parts.append(
            f"Found {len(findings)} minor issue(s) — overall low risk."
        )
    else:
        parts.append("No significant issues found — looks good to merge.")

    return " ".join(parts)


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Automated PR code review with structured Markdown output"
    )
    parser.add_argument(
        "--pr",
        help="PR URL (https://github.com/owner/repo/pull/123) or shorthand (owner/repo/123)"
    )
    parser.add_argument(
        "--diff",
        help="Path to a diff file (alternative to --pr)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write output to file instead of stdout"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON instead of Markdown"
    )
    args = parser.parse_args()

    if not args.pr and not args.diff:
        parser.error("Provide either --pr or --diff")

    # Fetch or read diff
    if args.diff:
        with open(args.diff) as f:
            diff_text = f.read()
        pr_url = f"local:{args.diff}"
        title = f"Local diff: {args.diff}"
        metadata = {"changed_files": 0, "additions": 0, "deletions": 0}
    else:
        owner, repo, number = parse_pr_url(args.pr)
        pr_url = f"https://github.com/{owner}/{repo}/pull/{number}"
        print(f"Fetching PR #{number} from {owner}/{repo}...", file=sys.stderr)
        metadata = fetch_pr_metadata(owner, repo, number)
        title = metadata["title"]
        diff_text = fetch_pr_diff(owner, repo, number)

    # Analyze
    print("Analyzing diff...", file=sys.stderr)
    stats = compute_diff_stats(diff_text)
    if args.diff:
        stats["files_changed"] = metadata.get("changed_files", stats["files_changed"])
        stats["additions"] = metadata.get("additions", stats["additions"])
        stats["deletions"] = metadata.get("deletions", stats["deletions"])
    else:
        stats["files_changed"] = metadata.get("changed_files", stats["files_changed"])
        stats["additions"] = metadata.get("additions", stats["additions"])
        stats["deletions"] = metadata.get("deletions", stats["deletions"])

    findings = analyze_diff(diff_text)
    confidence = compute_confidence(findings, stats)
    summary = generate_summary(title, stats, findings)

    result = ReviewResult(
        pr_url=pr_url,
        title=title,
        summary=summary,
        findings=findings,
        confidence=confidence,
        files_changed=stats["files_changed"],
        additions=stats["additions"],
        deletions=stats["deletions"]
    )

    # Output
    if args.json_output:
        output = json.dumps({
            "pr_url": result.pr_url,
            "title": result.title,
            "summary": result.summary,
            "confidence": result.confidence,
            "files_changed": result.files_changed,
            "additions": result.additions,
            "deletions": result.deletions,
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity.value,
                    "message": f.message,
                    "file": f.file,
                    "line": f.line
                }
                for f in result.findings
            ],
            "risk_count": {
                "critical": sum(1 for f in findings if f.severity == Severity.CRITICAL),
                "high": sum(1 for f in findings if f.severity == Severity.HIGH),
                "medium": sum(1 for f in findings if f.severity == Severity.MEDIUM),
                "low": sum(1 for f in findings if f.severity == Severity.LOW),
            }
        }, indent=2)
    else:
        output = format_review(result)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
