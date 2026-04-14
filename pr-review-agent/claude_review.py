#!/usr/bin/env python3
"""
claude-review — PR Review Agent

Analyzes a GitHub PR diff and produces a structured Markdown review.
Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo
    claude-review --diff /path/to/file.diff
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Risk Pattern Rules ──────────────────────────────────────────────
RISK_PATTERNS = [
    {
        "pattern": re.compile(r"(?im)(DROP\s+TABLE|DROP\s+DATABASE|TRUNCATE|DELETE\s+FROM\s+\w+\s*;)"),
        "category": "Destructive SQL",
        "severity": "Critical",
        "description": "Destructive database operation detected",
    },
    {
        "pattern": re.compile(r"(?im)(eval\(|exec\(|os\.system|subprocess.*shell=True)"),
        "category": "Code Injection",
        "severity": "Critical",
        "description": "Dynamic code execution with unvalidated input",
    },
    {
        "pattern": re.compile(r"(?im)(hardcoded|hardcode|password\s*=\s*['\"][^'\"]+['\"]|secret\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"])"),
        "category": "Security",
        "severity": "High",
        "description": "Potential hardcoded secret or credential",
    },
    {
        "pattern": re.compile(r"(?im)(rm\s+-rf|rm\s+-fr|\.\./|\.\.\\\\)"),
        "category": "Path Traversal",
        "severity": "High",
        "description": "Path traversal or force-delete pattern",
    },
    {
        "pattern": re.compile(r"(?im)(console\.(log|debug|warn|error)|print\([^)]*\))"),
        "category": "Debug Code",
        "severity": "Low",
        "description": "Debug logging statement that may not belong in production",
    },
    {
        "pattern": re.compile(r"(?im)(TODO|FIXME|HACK|XXX|TEMP)"),
        "category": "Technical Debt",
        "severity": "Medium",
        "description": "Outstanding TODO/FIXME marker in code",
    },
    {
        "pattern": re.compile(r"(?im)(except\s*:|except\s+Exception\s*:)\s*$"),
        "category": "Error Handling",
        "severity": "Medium",
        "description": "Bare except clause swallows all errors",
    },
    {
        "pattern": re.compile(r"(?im)(random|secrets|token|password).*(seed|generate|rand)"),
        "category": "Cryptography",
        "severity": "Critical",
        "description": "Weak random number generator or insecure token generation",
    },
    {
        "pattern": re.compile(r"(?im)(innerHTML|dangerouslySetInnerHTML|document\.write)"),
        "category": "XSS",
        "severity": "High",
        "description": "Direct DOM injection — potential XSS vector",
    },
    {
        "pattern": re.compile(r"(?im)(npm\s+install|--no-audit|--no-verify)"),
        "category": "Supply Chain",
        "severity": "Medium",
        "description": "Package install without integrity verification",
    },
]


def fetch_pr_diff(pr_url: str, repo: str | None = None) -> str:
    """Fetch PR diff using gh CLI."""
    if pr_url.startswith("http"):
        result = subprocess.run(
            ["gh", "pr", "diff", pr_url],
            capture_output=True, text=True, timeout=30,
        )
    else:
        pr_num = pr_url
        repo_arg = ["--repo", repo] if repo else []
        result = subprocess.run(
            ["gh", "pr", "diff", pr_num] + repo_arg,
            capture_output=True, text=True, timeout=30,
        )

    if result.returncode != 0:
        print(f"Error fetching PR diff: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    return result.stdout


def get_pr_metadata(pr_url: str, repo: str | None = None) -> dict:
    """Get PR metadata (title, author, files changed, etc.)."""
    if pr_url.startswith("http"):
        cmd = ["gh", "pr", "view", pr_url, "--json", "title,author,additions,deletions,changedFiles,state,baseRefName,headRefName"]
    else:
        repo_arg = ["--repo", repo] if repo else []
        cmd = ["gh", "pr", "view", pr_url, "--json", "title,author,additions,deletions,changedFiles,state,baseRefName,headRefName"] + repo_arg

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return {}
    return json.loads(result.stdout)


def analyze_diff(diff_text: str) -> dict:
    """Analyze a git diff and extract risks, stats, and suggestions."""
    added_lines = []
    removed_lines = []
    file_changes = set()
    languages_seen = set()

    for line in diff_text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(line[1:])
        elif line.startswith("+++ b/") or line.startswith("--- a/"):
            filepath = line.split("/", 1)[1] if "/" in line else ""
            if filepath:
                file_changes.add(filepath)
                ext = Path(filepath).suffix.lower()
                lang_map = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                           ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
                           ".php": "PHP", ".cs": "C#", ".jsx": "JSX", ".tsx": "TSX",
                           ".vue": "Vue", ".svelte": "Svelte", ".sql": "SQL",
                           ".sh": "Shell", ".yaml": "YAML", ".yml": "YAML",
                           ".json": "JSON", ".html": "HTML", ".css": "CSS"}
                if ext in lang_map:
                    languages_seen.add(lang_map[ext])

    # Detect risks from added lines
    risks_found = []
    seen_categories = set()
    for i, line in enumerate(added_lines):
        for rule in RISK_PATTERNS:
            if rule["pattern"].search(line):
                cat = rule["category"]
                key = f"{cat}:{rule['description']}"
                if key not in seen_categories:
                    seen_categories.add(key)
                    risks_found.append({
                        "category": cat,
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "snippet": line.strip()[:200],
                    })

    # Generate suggestions based on analysis
    suggestions = generate_suggestions(added_lines, file_changes, languages_seen, risks_found)

    # Calculate confidence score
    confidence = calculate_confidence(risks_found, len(added_lines), len(file_changes))

    return {
        "added_lines": len(added_lines),
        "removed_lines": len(removed_lines),
        "files_changed": list(file_changes),
        "languages": list(languages_seen),
        "risks": risks_found,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def generate_suggestions(added_lines, file_changes, languages, risks) -> list:
    """Generate improvement suggestions based on the analysis."""
    suggestions = []

    # Check for missing tests
    has_test_file = any("test" in f.lower() or "spec" in f.lower() for f in file_changes)
    src_files = [f for f in file_changes if not any(x in f.lower() for x in ["test", "spec", "mock", "fixture"])]
    if src_files and not has_test_file:
        suggestions.append({
            "priority": "Consider",
            "text": "No test files detected in this PR. Consider adding unit tests for new or modified logic.",
        })

    # Check for large diffs
    if len(added_lines) > 500:
        suggestions.append({
            "priority": "Consider",
            "text": f"Large diff ({len(added_lines)} lines added). Consider splitting into smaller, focused PRs for easier review.",
        })

    # Check for config changes mixed with source
    config_files = [f for f in file_changes if any(f.endswith(x) for x in [".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"])]
    src_only = [f for f in file_changes if not any(f.endswith(x) for x in [".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".md", ".lock"])]

    # Security-specific suggestions
    critical_risks = [r for r in risks if r["severity"] == "Critical"]
    if critical_risks:
        suggestions.append({
            "priority": "Recommended",
            "text": f"{len(critical_risks)} critical risk(s) found. Please review each item carefully before merging.",
        })

    # Language-specific suggestions
    if "Python" in languages:
        has_type_hints = any(":" in line and ("def " in line or " -> ") in line for line in added_lines[:50])
        if not has_type_hints and any("def " in line for line in added_lines[:50]):
            suggestions.append({
                "priority": "Suggestion",
                "text": "Python functions detected without type hints. Adding type hints improves readability and enables static analysis.",
            })

    if "JavaScript" in languages or "TypeScript" in languages:
        has_jsdoc = any("/**" in line for line in added_lines[:50])
        if not has_jsdoc and any("function" in line or "=>" in line or "const " in line for line in added_lines[:50]):
            suggestions.append({
                "priority": "Suggestion",
                "text": "Consider adding JSDoc/TSDoc comments for public functions and complex logic.",
            })

    return suggestions


def calculate_confidence(risks, added_count, files_count) -> str:
    """Calculate overall confidence in the review."""
    if added_count == 0:
        return "High"

    critical_count = sum(1 for r in risks if r["severity"] == "Critical")
    high_count = sum(1 for r in risks if r["severity"] == "High")

    # More lines + more files + more risks = lower confidence
    risk_score = critical_count * 3 + high_count * 2 + len(risks)
    size_factor = min(added_count / 200, 2.0) + min(files_count / 5, 1.0)

    if risk_score == 0 and size_factor < 1.5:
        return "High"
    elif risk_score <= 2 and size_factor < 2.5:
        return "Medium"
    else:
        return "Low"


def format_review(pr_meta: dict, analysis: dict, pr_url: str) -> str:
    """Format the analysis as structured Markdown."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = pr_meta.get("title", "Unknown PR")
    author = pr_meta.get("author", {}).get("login", "unknown") if isinstance(pr_meta.get("author"), dict) else "unknown"
    additions = pr_meta.get("additions", "?")
    deletions = pr_meta.get("deletions", "?")
    files_count = pr_meta.get("changedFiles", len(analysis["files_changed"]))
    state = pr_meta.get("state", "")

    lines = []
    lines.append("## 📋 PR Review Summary\n")

    # Header info
    lines.append(f"**PR:** [{title}]({pr_url})")
    lines.append(f"**Author:** @{author} | **State:** {state}")
    lines.append(f"**Stats:** +{additions} / -{deletions} | **Files:** {files_count}")
    lines.append(f"**Languages:** {', '.join(analysis['languages']) if analysis['languages'] else 'Unknown'}")
    lines.append(f"**Reviewed:** {now}\n")

    # ── Summary ──
    lines.append("### 📝 Summary")
    risk_summary = {}
    for r in analysis["risks"]:
        risk_summary[r["severity"]] = risk_summary.get(r["severity"], 0) + 1

    parts = []
    if analysis["risks"]:
        sev_parts = [f"{v} {k}(s)" for k, v in sorted(risk_summary.items())]
        parts.append(f"Identified {', '.join(sev_parts)} across {analysis['added_lines']} lines of new code.")
    else:
        parts.append(f"No significant risks detected in {analysis['added_lines']} lines of new code.")

    parts.append(f"Affects {files_count} file(s) spanning {', '.join(analysis['languages']) if analysis['languages'] else 'multiple'}.")
    confidence = analysis["confidence"]
    emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(confidence, "⚪")
    parts.append(f"Overall confidence: {emoji} **{confidence}**")

    lines.append(" ".join(parts) + "\n")

    # ── Risks ──
    lines.append("### ⚠️ Identified Risks")
    if analysis["risks"]:
        for i, risk in enumerate(analysis["risks"], 1):
            sev_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵"}.get(risk["severity"], "⚪")
            lines.append(f"{i}. **[{risk['severity']}]** {sev_emoji} `{risk['category']}` — {risk['description']}")
            if risk.get("snippet"):
                lines.append(f"   ```")
                lines.append(f"   {risk['snippet']}")
                lines.append(f"   ```")
    else:
        lines.append("✅ No significant risks found in this diff.\n")

    # ── Suggestions ──
    lines.append("### 💡 Improvement Suggestions")
    if analysis["suggestions"]:
        for i, sug in enumerate(analysis["suggestions"], 1):
            pri_emoji = {"Recommended": "⚡", "Consider": "💭", "Suggestion": "💡"}.get(sug["priority"], "•")
            lines.append(f"{i}. {pri_emoji} **{sug['priority']}:** {sug['text']}")
    else:
        lines.append("No specific suggestions at this time.\n")

    # ── Confidence Breakdown ──
    lines.append("### 📊 Confidence Score")
    conf_detail = {
        "High": "The PR appears well-structured with minimal risk indicators. Standard review should suffice.",
        "Medium": "Some risk patterns were found. Recommend thorough review of flagged areas before merge.",
        "Low": "Multiple high-severity risks or large scope detected. Detailed security and architecture review recommended.",
    }
    lines.append(f"**{confidence}** — {conf_detail.get(confidence, '')}")

    lines.append("\n---")
    lines.append("*Generated by `claude-review` — PR Review Agent*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — Analyze PRs and produce structured reviews.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr 123 --repo owner/repo
  claude-review --diff changes.diff
  claude-review --pr 456 --repo owner/repo --output review.md
""",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="PR URL or number to review")
    group.add_argument("--diff", help="Path to a .diff file to analyze")
    parser.add_argument("--repo", help="Repo slug (owner/repo), required when --pr is a number")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Fetch or read diff
    if args.pr:
        diff_text = fetch_pr_diff(args.pr, args.repo)
        pr_url = args.pr if args.pr.startswith("http") else f"https://github.com/{args.repo}/pull/{args.pr}" if args.repo else args.pr
        pr_meta = get_pr_metadata(args.pr, args.repo)
    else:
        with open(args.diff, "r") as f:
            diff_text = f.read()
        pr_url = f"file://{Path(args.diff).resolve()}"
        pr_meta = {}

    # Analyze
    analysis = analyze_diff(diff_text)

    # Format output
    if args.json_output:
        output = json.dumps({"meta": pr_meta, "analysis": analysis}, indent=2, default=str)
    else:
        output = format_review(pr_meta, analysis, pr_url)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
