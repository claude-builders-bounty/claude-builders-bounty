#!/usr/bin/env python3
"""Standalone PR diff analyzer — produces structured review without requiring Claude Code.

Uses regex-based heuristics to detect common issues:
- SQL injection patterns
- Missing error handling
- Hardcoded secrets
- Debug artifacts (console.log, print, etc.)
- Type safety issues
- Missing input validation
- Unsafe deserialization
- Race condition patterns

Produces the same structured Markdown output format expected by the bounty.
"""

import re
import sys
import json
import subprocess
from pathlib import Path
from collections import Counter
from typing import NamedTuple


class Finding(NamedTuple):
    severity: str  # "high", "medium", "low"
    category: str
    message: str
    location: str  # file:line or just file


# ── Pattern definitions ─────────────────────────────────────────────────────

CHECKS = [
    # (regex, severity, category, message_template)
    # message_template uses {location} for file/line context

    # SQL Injection
    (r'(?:execute|query|run)\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*\$',
     "high", "SQL Injection",
     "Potential SQL injection: string interpolation in SQL query. Use parameterized queries."),

    (r'(?:execute|query|run)\s*\(\s*["\'].*\%[sdx]',
     "high", "SQL Injection",
     "Potential SQL injection: %-style formatting in SQL query."),

    (r'(?:execute|query|run)\s*\(\s*f["\']',
     "high", "SQL Injection",
     "Potential SQL injection: f-string in SQL query."),

    # Hardcoded secrets
    (r'(?:password|secret|token|api_key|apikey|API_KEY)\s*[:=]\s*["\'][^\'"]{8,}["\']',
     "high", "Hardcoded Secret",
     "Hardcoded secret/token found. Use environment variables instead."),

    (r'(?:-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----)',
     "critical", "Hardcoded Secret",
     "CRITICAL: Private key found in source code!"),

    # Debug artifacts
    (r'\bconsole\.(?:log|warn|error|debug|info)\s*\([^)]',
     "low", "Debug Artifact",
     "console.log/warn/error left in code. Remove or use a proper logger."),

    (r'\bprint\s*\([^)]',
     "low", "Debug Artifact",
     "print() statement found. Replace with proper logging."),

    (r'\bdebugger\b',
     "medium", "Debug Artifact",
     "debugger statement found. Remove before merging."),

    (r'\.only\s*\(',
     "medium", "Test Artifact",
     ".only() on test left in. Remove to run full test suite."),

    # Missing error handling
    (r'\bJSON\.parse\s*\([^)]*\)(?!.*\b(?:try|catch)\b)',
     "medium", "Missing Error Handling",
     "JSON.parse without try-catch. Malformed JSON will crash."),

    (r'(?:fetch|axios|got|request)(?!.*\b(?:\.catch|try\b|await.*catch))',
     "medium", "Missing Error Handling",
     "HTTP request without error handling."),

    # Type safety
    (r':\s*any\b',
     "medium", "Type Safety",
     "Use of 'any' type. Replace with a specific type or 'unknown'."),

    (r'@ts-ignore',
     "medium", "Type Safety",
     "@ts-ignore found. Add a comment explaining why the type is wrong, or fix it."),

    (r'@ts-expect-error(?!.*//)',
     "low", "Type Safety",
     "@ts-expect-error without a comment explaining why."),

    # XSS
    (r'dangerouslySetInnerHTML',
     "high", "XSS Risk",
     "dangerouslySetInnerHTML used. Ensure content is sanitized (DOMPurify)."),

    (r'\.innerHTML\s*=',
     "high", "XSS Risk",
     "Direct innerHTML assignment. Use textContent or DOM manipulation instead."),

    # Unsafe deserialization
    (r'\beval\s*\(',
     "critical", "Unsafe Deserialization",
     "CRITICAL: eval() used. Never evaluate arbitrary strings."),

    (r'\bFunction\s*\(',
     "high", "Unsafe Deserialization",
     "new Function() used. This is eval by another name."),

    # Race conditions
    (r'(?:setTimeout|setInterval)\s*\([^,]*,\s*0\s*\)',
     "medium", "Race Condition",
     "setTimeout with 0ms delay — potential race condition. Use proper async primitives."),

    # Missing validation
    (r'\.body\b(?!.*\b(?:validate|zod|joi|yup|check|assert)\b)',
     "medium", "Missing Validation",
     "Request body used without validation. Add input validation (zod, joi, etc.)."),

    # Security: unsafe regex
    (r'new\s+RegExp\s*\(\s*(?![\'\"])',
     "medium", "ReDoS Risk",
     "Dynamic RegExp from unvalidated input — potential ReDoS. Validate/reject long inputs first."),
]


def analyze_diff(diff_text: str, pr_info: dict | None = None) -> str:
    """Analyze a git diff and produce a structured Markdown review."""

    lines = diff_text.split('\n')
    changed_files: list[str] = []
    additions = 0
    deletions = 0
    current_file = ""

    for line in lines:
        if line.startswith('diff --git'):
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file = parts[3].lstrip('b/')
                changed_files.append(current_file)
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1

    # Deduplicate files
    changed_files = list(dict.fromkeys(changed_files))

    # Run pattern checks on added lines only
    added_lines = [(i, line[1:]) for i, line in enumerate(lines)
                   if line.startswith('+') and not line.startswith('+++')]

    findings: list[Finding] = []
    current_file = ""

    for line_num, line in enumerate(lines):
        # Track current file
        if line.startswith('diff --git'):
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file = parts[3].lstrip('b/')

        if not line.startswith('+') or line.startswith('+++'):
            continue

        content = line[1:]  # Strip leading '+'

        for pattern, severity, category, message in CHECKS:
            if re.search(pattern, content, re.IGNORECASE):
                location = f"{current_file}:{line_num + 1}" if current_file else f"line {line_num + 1}"
                findings.append(Finding(severity, category, f"{message} ({location})", location))

    # ── Build the report ────────────────────────────────────────────────────

    pr_desc = ""
    if pr_info:
        pr_desc = f"**PR:** {pr_info.get('title', 'Unknown')}\n"
        pr_desc += f"**Author:** {pr_info.get('author', 'Unknown')}\n"
        pr_desc += f"**Files:** {len(changed_files)} | **+{additions}** **-{deletions}**\n\n"

    report = "## Review Summary\n\n"
    report += f"Automated analysis of {len(changed_files)} file(s) "
    report += f"({additions} additions, {deletions} deletions).\n\n"

    if not findings:
        report += "No issues detected by automated analysis. "
        report += "Manual review still recommended for logic correctness.\n\n"
    else:
        severity_counts = Counter(f.severity for f in findings)
        high_critical = severity_counts.get('critical', 0) + severity_counts.get('high', 0)
        if high_critical > 0:
            report += f"⚠️ **{high_critical} high/critical issue(s)** found. "
        report += f"{len(findings)} total finding(s) across {len(set(f.location for f in findings))} locations.\n\n"

    # Pros
    report += "## ✅ Pros\n\n"
    pros = []
    if additions > 0:
        pros.append(f"Adds {additions} lines across {len(changed_files)} file(s)")
    if len(changed_files) <= 5:
        pros.append(f"Focused change: only {len(changed_files)} file(s) modified")
    if any(f.endswith('.test.ts') or f.endswith('.test.tsx') or f.endswith('_test.py') or f.endswith('_test.go') or '.test.' in f for f in changed_files):
        pros.append("Includes test files — tests were added or updated")
    if any(f.endswith('.md') or 'docs' in f.lower() for f in changed_files):
        pros.append("Includes documentation updates")

    if pros:
        for p in pros:
            report += f"- {p}\n"
    else:
        report += "- _(automated analysis cannot determine human-intent positives — manual review needed)_\n"
    report += "\n"

    # Cons
    report += "## ⚠️ Cons\n\n"
    if findings:
        reported = set()
        for f in sorted(findings, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.severity, 4)):
            key = (f.severity, f.message)
            if key not in reported:
                severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(f.severity, '⚪')
                report += f"- {severity_icon} [{f.severity.upper()}] [{f.category}] {f.message}\n"
                reported.add(key)
    else:
        report += "- No automated issues detected. Manual review still recommended.\n"
    report += "\n"

    # Suggestions
    report += "## 💡 Suggestions\n\n"
    suggestions = []
    if not any(f.endswith('.test.ts') or f.endswith('.test.tsx') or '.test.' in f for f in changed_files):
        suggestions.append("Consider adding tests for the changed functionality")
    if additions > 200:
        suggestions.append(f"Large change ({additions} additions). Consider splitting into smaller PRs for easier review")
    if any(f.category == "Debug Artifact" for f in findings):
        suggestions.append("Set up a pre-commit hook to catch debug artifacts (console.log, print, debugger)")

    if suggestions:
        for s in suggestions:
            report += f"- {s}\n"
    else:
        report += "- _(no automated suggestions — manual review may yield improvements)_\n"
    report += "\n"

    # Confidence
    report += "## 📊 Confidence\n\n"
    if not findings:
        confidence = "Medium"
        reason = "No issues detected by automated patterns, but static analysis cannot verify logic correctness."
    elif any(f.severity == 'critical' for f in findings):
        confidence = "High"
        reason = f"Critical issues found ({severity_counts.get('critical', 0)}) that should be addressed before merge."
    elif any(f.severity == 'high' for f in findings):
        confidence = "High"
        reason = f"High-severity issues found ({severity_counts.get('high', 0)}) — review findings carefully."
    else:
        confidence = "Medium"
        reason = f"{len(findings)} low/medium finding(s) — most are lintable issues."

    report += f"**{confidence}** — {reason}\n\n"

    # Footer
    report += "---\n"
    report += f"_Automated review by claude-review agent. "
    report += f"Analyzed {len(changed_files)} file(s), {len(lines)} line(s)._"

    return report


def get_pr_diff(pr_identifier: str) -> tuple[str, dict]:
    """Get diff from a GitHub PR using gh CLI."""
    # Parse owner/repo#num or full URL
    owner = repo = num = ""
    url_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_identifier)
    short_match = re.match(r'([^/]+)/([^#]+)#(\d+)', pr_identifier)

    if url_match:
        owner, repo, num = url_match.group(1), url_match.group(2), url_match.group(3)
    elif short_match:
        owner, repo, num = short_match.group(1), short_match.group(2), short_match.group(3)
    else:
        raise ValueError(f"Cannot parse PR identifier: {pr_identifier}")

    # Get diff
    diff = subprocess.check_output(
        ['gh', 'pr', 'diff', num, '--repo', f'{owner}/{repo}'],
        text=True, stderr=subprocess.PIPE
    )

    # Get PR info
    title = author = "Unknown"
    try:
        info = json.loads(subprocess.check_output(
            ['gh', 'pr', 'view', num, '--repo', f'{owner}/{repo}',
             '--json', 'title,author'],
            text=True, stderr=subprocess.PIPE
        ))
        title = info.get('title', 'Unknown')
        author = info['author']['login'] if 'author' in info else 'Unknown'
    except Exception:
        pass

    return diff, {'title': title, 'author': author, 'owner': owner, 'repo': repo, 'number': num}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI-powered PR review agent')
    parser.add_argument('--pr', help='GitHub PR URL or owner/repo#num')
    parser.add_argument('--diff', help='Raw diff text (alternative to --pr)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--use-claude', action='store_true',
                        help='Use Claude Code for LLM-powered review (requires claude CLI)')
    args = parser.parse_args()

    if args.pr:
        print(f"Fetching PR: {args.pr}...")
        diff_text, pr_info = get_pr_diff(args.pr)
        print(f"Analyzing {pr_info['owner']}/{pr_info['repo']}#{pr_info['number']} by {pr_info['author']}...")
    elif args.diff:
        diff_text = args.diff
        pr_info = None
    elif not sys.stdin.isatty():
        diff_text = sys.stdin.read()
        pr_info = None
    else:
        parser.error("Provide --pr, --diff, or pipe diff via stdin")

    if args.use_claude:
        # Use Claude Code for LLM review
        try:
            import subprocess
            result = subprocess.run(
                ['claude', '-p', 'Review this PR diff and produce a structured markdown review with Summary, Pros, Cons, Suggestions, and Confidence score.'],
                input=diff_text, text=True, capture_output=True, timeout=300
            )
            review = result.stdout
        except Exception as e:
            review = analyze_diff(diff_text, pr_info)
            review += f"\n\n_(Claude Code unavailable: {e}. Fallback to heuristic analysis.)_\n"
    else:
        review = analyze_diff(diff_text, pr_info)

    if args.output:
        Path(args.output).write_text(review)
        print(f"Review saved to {args.output}")
    else:
        print(review)


if __name__ == '__main__':
    main()
