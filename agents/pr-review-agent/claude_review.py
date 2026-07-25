#!/usr/bin/env python3
"""
claude_review.py — PR Review Sub-Agent for Claude Code.

Fetches a GitHub PR diff via the API, analyzes it, and outputs a
structured Markdown review with Summary, Risks, Improvements, and
Confidence score.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr owner/repo/123
    python claude_review.py --pr 123 --repo owner/repo
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime


# ── API helpers ──────────────────────────────────────────────────────────────

def _get_github_token():
    """Return a GitHub token from env, or None."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


def api_get(url, accept="application/vnd.github+json"):
    """Fetch a URL with the given Accept header and return parsed JSON or raw text.

    Uses GITHUB_TOKEN or GH_TOKEN env var for authentication when available
    (avoids rate limits in CI / GitHub Actions).
    """
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "claude-review-agent/1.0")
    token = _get_github_token()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if "json" in accept:
                return json.loads(raw)
            return raw
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {e.code} fetching {url}", file=sys.stderr)
        print(f"   {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error fetching {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def parse_pr_arg(pr_arg, repo_arg=None):
    """Parse --pr and --repo into (owner, repo, number)."""
    # Full URL form: https://github.com/owner/repo/pull/123
    m = re.match(
        r"(?:https?://github\.com/)?([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$", pr_arg
    )
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # Short form: owner/repo/number
    m = re.match(r"^([^/]+)/([^/]+)/(\d+)$", pr_arg)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # Bare number with --repo
    m = re.match(r"^(\d+)$", pr_arg)
    if m and repo_arg:
        parts = repo_arg.split("/")
        if len(parts) == 2:
            return parts[0], parts[1], int(m.group(1))

    print(
        "❌ Could not parse PR argument. Use one of:\n"
        "   --pr https://github.com/owner/repo/pull/123\n"
        "   --pr owner/repo/123\n"
        "   --pr 123 --repo owner/repo",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Diff analysis ────────────────────────────────────────────────────────────

RISK_PATTERNS = {
    "hardcoded_secret": [
        r"(?i)(?:api[_-]?key|secret|password|token|credential)\s*[=:]\s*['\"][^'\"]+['\"]",
    ],
    "sql_injection": [
        r"(?i)(?:execute|raw|query)\s*\(\s*f['\"]",
        r"(?i)\.format\(.*\)\s*\)\s*#\s*SQL",
    ],
    "command_injection": [
        r"(?i)os\.system\(",
        r"(?i)subprocess\.(?:call|Popen|run)\(.*shell\s*=\s*True",
    ],
    "eval_exec": [
        r"(?i)\beval\s*\(",
        r"(?i)\bexec\s*\(",
        r"(?i)__import__\(",
    ],
    "debug_code": [
        r"(?i)\bprint\s*\(.*(?:debug|test|temp|here|xxx)",
        r"(?i)#\s*TODO|#\s*FIXME|#\s*HACK|\bpass\s*#\s*(?:TODO|FIXME)",
        r"\bpdb\.set_trace\b",
        r"\bipdb\.set_trace\b",
        r"\bbreakpoint\s*\(\s*\)",
    ],
    "large_binary": [
        r"diff --git a/.+\.(?:png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|exe|dmg|class)",
    ],
    "permission_change": [
        r"^old mode \d+$",
        r"^new mode \d+$",
    ],
    "exception_swallowing": [
        r"except\s+\w+\s*:\s*\n\s*pass",
        r"except\s*:\s*\n\s*pass",
    ],
    "unsafe_yaml_load": [
        r"yaml\.load\s*\(",
    ],
    "pickle_load": [
        r"pickle\.loads?\s*\(",
    ],
}

IMPROVEMENT_PATTERNS = {
    "no_error_handling": [
        r"^\+.*(?:open|read|write)\s*\(",
    ],
    "no_input_validation": [
        r"^\+.*input\s*\(",
        r"^\+.*request\.(?:GET|POST|data|params)",
    ],
    "hardcoded_config": [
        r"^\+.*(?:localhost|127\.0\.0\.1|0\.0\.0\.0)[:]\d+",
        r"^\+.*(?:password|secret)\s*=\s*['\"][^'\"]+['\"]",
    ],
    "missing_docstring": [
        r"^def \w+",
    ],
    "bare_except": [
        r"^\+.*except\s*:",
    ],
}


def analyze_diff(diff_text, pr_data):
    """Analyze a PR diff and return a dict of findings."""
    files = []
    current_file = None
    added_lines = 0
    removed_lines = 0
    total_hunks = 0
    risk_findings = []
    improvement_findings = []
    file_extensions = Counter()
    languages = Counter()
    test_file_count = 0
    config_file_count = 0
    doc_file_count = 0
    source_file_count = 0
    largest_additions = []
    largest_deletions = []

    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".jsx": "JavaScript (React)",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".java": "Java",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".cs": "C#",
        ".php": "PHP",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".toml": "TOML",
        ".md": "Markdown",
        ".rst": "reStructuredText",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sql": "SQL",
        ".dockerfile": "Dockerfile",
        "Dockerfile": "Dockerfile",
        ".tf": "Terraform",
    }

    test_indicators = ["test_", "_test.", ".spec.", "__tests__", "test-"]

    for line in diff_text.splitlines():
        # File header
        fm = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
        if fm:
            if current_file is not None:
                files.append(current_file)
            old_path = fm.group(1)
            new_path = fm.group(2)
            _, ext = os.path.splitext(new_path)
            file_extensions[ext] += 1

            # Detect language
            lang = "Unknown"
            for key, val in lang_map.items():
                if new_path.endswith(key) or new_path.upper() == key.upper():
                    lang = val
                    break
            languages[lang] += 1

            is_test = any(ind in new_path.lower() for ind in test_indicators)
            is_config = ext in (".yaml", ".yml", ".json", ".toml", ".ini", ".cfg")
            is_doc = ext in (".md", ".rst", ".txt")

            current_file = {
                "old_path": old_path,
                "new_path": new_path,
                "extension": ext,
                "language": lang,
                "is_test": is_test,
                "is_config": is_config,
                "is_doc": is_doc,
                "additions": 0,
                "deletions": 0,
                "hunks": 0,
                "added_lines": [],
                "deleted_lines": [],
                "chunks": [],
            }

            if is_test:
                test_file_count += 1
            if is_config:
                config_file_count += 1
            if is_doc:
                doc_file_count += 1
            if not is_test and not is_config and not is_doc:
                source_file_count += 1

            continue

        if current_file is None:
            continue

        # Hunk header
        hm = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hm:
            current_file["hunks"] += 1
            total_hunks += 1
            current_file["chunks"].append({"start": int(hm.group(1)), "lines": []})
            continue

        # Added line
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            current_file["additions"] += 1
            added_lines += 1
            current_file["added_lines"].append(content)
            if current_file["chunks"]:
                current_file["chunks"][-1]["lines"].append(("+", content))

            # Check risk patterns
            for risk_type, patterns in RISK_PATTERNS.items():
                for pat in patterns:
                    m2 = re.search(pat, content)
                    if m2:
                        risk_findings.append({
                            "type": risk_type,
                            "file": current_file["new_path"],
                            "line": current_file["additions"],
                            "match": content.strip()[:100],
                        })

            # Check improvement patterns
            for impr_type, patterns in IMPROVEMENT_PATTERNS.items():
                for pat in patterns:
                    if re.match(pat, content):
                        improvement_findings.append({
                            "type": impr_type,
                            "file": current_file["new_path"],
                            "line": current_file["additions"],
                            "match": content.strip()[:100],
                        })

        # Removed line
        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:]
            current_file["deletions"] += 1
            removed_lines += 1
            current_file["deleted_lines"].append(content)
            if current_file["chunks"]:
                current_file["chunks"][-1]["lines"].append(("-", content))

    if current_file is not None:
        files.append(current_file)

    # Find largest files
    sorted_additions = sorted(files, key=lambda f: f["additions"], reverse=True)
    sorted_deletions = sorted(files, key=lambda f: f["deletions"], reverse=True)

    largest_additions = [
        (f["new_path"], f["additions"]) for f in sorted_additions[:5] if f["additions"] > 0
    ]
    largest_deletions = [
        (f["new_path"], f["deletions"]) for f in sorted_deletions[:5] if f["deletions"] > 0
    ]

    # Deduplicate findings
    risk_findings_dedup = []
    seen_risk = set()
    for f in risk_findings:
        key = (f["type"], f["file"])
        if key not in seen_risk:
            seen_risk.add(key)
            risk_findings_dedup.append(f)

    impr_findings_dedup = []
    seen_impr = set()
    for f in improvement_findings:
        key = (f["type"], f["file"])
        if key not in seen_impr:
            seen_impr.add(key)
            impr_findings_dedup.append(f)

    # Compute complexity score (rough heuristic)
    total_changes = added_lines + removed_lines
    complexity_score = min(10, total_changes / 20 + total_hunks / 2 + len(files) * 1.5)

    return {
        "files": files,
        "total_files": len(files),
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "total_hunks": total_hunks,
        "file_extensions": file_extensions,
        "languages": languages,
        "test_file_count": test_file_count,
        "config_file_count": config_file_count,
        "doc_file_count": doc_file_count,
        "source_file_count": source_file_count,
        "risk_findings": risk_findings_dedup,
        "improvement_findings": impr_findings_dedup,
        "largest_additions": largest_additions,
        "largest_deletions": largest_deletions,
        "complexity_score": complexity_score,
    }


# ── Markdown output ─────────────────────────────────────────────────────────

def classify_change_type(analysis):
    """Determine the primary nature of the change."""
    l = analysis["languages"]
    most_common_lang = l.most_common(1)[0][0] if l else "Unknown"

    source_change = analysis["source_file_count"]
    test_change = analysis["test_file_count"]
    config_change = analysis["config_file_count"]
    doc_change = analysis["doc_file_count"]
    deletions_pct = (
        analysis["removed_lines"] / (analysis["added_lines"] + analysis["removed_lines"]) * 100
        if (analysis["added_lines"] + analysis["removed_lines"]) > 0
        else 0
    )

    if deletions_pct > 70 and analysis["added_lines"] < 20:
        return "cleanup", f"Code cleanup / removal in **{most_common_lang}**"
    if test_change > source_change and source_change > 0:
        return "tests", f"Test additions in **{most_common_lang}**"
    if config_change >= analysis["total_files"] * 0.5:
        return "configuration", "Configuration / metadata changes"
    if doc_change >= analysis["total_files"] * 0.5:
        return "documentation", "Documentation updates"
    return "feature", f"Feature / fix in **{most_common_lang}**"


def generate_summary(pr_data, analysis, change_type, change_desc):
    """Generate an executive summary paragraph."""
    author = pr_data.get("user", {}).get("login", "unknown")
    title = pr_data.get("title", "Untitled PR")
    state = pr_data.get("state", "unknown")

    parts = [
        f"This PR by **@{author}** ({title}) "
        f"modifies **{analysis['total_files']} files** "
        f"(**+{analysis['added_lines']}** / **−{analysis['removed_lines']}** lines)"
        f" across **{analysis['total_hunks']} hunks**.",
        f"",
        f"**Change type:** {change_desc}.",
    ]

    if analysis["test_file_count"] > 0:
        pct = analysis["test_file_count"] / analysis["total_files"] * 100
        parts.append(
            f" Includes **{analysis['test_file_count']} test file(s)** ({pct:.0f}% of changes)."
        )

    risk_count = len(analysis["risk_findings"])
    if risk_count > 0:
        parts.append(
            f" **{risk_count} potential risk(s)** flagged for review."
        )
    else:
        parts.append(" No high-severity risks detected.")

    impr_count = len(analysis["improvement_findings"])
    if impr_count > 0:
        parts.append(
            f" **{impr_count} improvement suggestion(s)** offered."
        )
    else:
        parts.append(" Code quality looks solid.")

    return "".join(parts)


def compute_confidence(analysis):
    """Compute a confidence score 0-100 based on analysis thoroughness."""
    score = 70  # baseline

    # More analysis is possible with more data
    if analysis["total_files"] > 0:
        score += 5
    if analysis["added_lines"] > 20:
        score += 5
    if analysis["risk_findings"]:
        score -= len(analysis["risk_findings"]) * 3  # uncertainty from risks
    if analysis["improvement_findings"]:
        score -= min(10, len(analysis["improvement_findings"]) * 2)
    if analysis["test_file_count"] > 0:
        score += 10  # tests increase confidence
    if analysis["total_hunks"] <= 3:
        score += 5  # small, focused changes
    if analysis["total_files"] > 10:
        score -= 10  # large PRs are harder to review

    return max(10, min(100, score))


def format_review(pr_data, diff_text, analysis):
    """Format the full structured Markdown review."""
    pr_url = pr_data.get("html_url", "")
    title = pr_data.get("title", "Untitled PR")
    author = pr_data.get("user", {}).get("login", "unknown")
    created = pr_data.get("created_at", "")[:10]
    state = pr_data.get("state", "unknown")
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)

    change_type, change_desc = classify_change_type(analysis)
    summary = generate_summary(pr_data, analysis, change_type, change_desc)
    confidence = compute_confidence(analysis)

    body = pr_data.get("body", "")
    body_preview = body.strip()[:300] if body else "*No description provided.*"

    lines = []
    lines.append(f"# 🔍 PR Review: {title}")
    lines.append("")
    lines.append(
        f"*Review generated by [claude_review.py] at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*"
        if False else
        f"*Review generated by `claude_review.py` at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Metadata ──
    lines.append("## 📋 PR Metadata")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| **PR** | [{pr_url}]({pr_url}) |")
    lines.append(f"| **Title** | {title} |")
    lines.append(f"| **Author** | @{author} |")
    lines.append(f"| **State** | {state} |")
    lines.append(f"| **Created** | {created} |")
    lines.append(f"| **Files Changed** | {changed_files} |")
    lines.append(f"| **Additions** | +{additions} |")
    lines.append(f"| **Deletions** | −{deletions} |")
    lines.append(f"| **Net Change** | {'+' if additions >= deletions else ''}{additions - deletions} |")
    lines.append("")
    lines.append("### Description")
    lines.append("")
    lines.append(f"> {body_preview}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Executive Summary ──
    lines.append("## 📝 Executive Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Files Changed ──
    lines.append("## 📂 Files Changed")
    lines.append("")
    lines.append("| # | File | Lang | Changes | Status |")
    lines.append("|---|---|---|---|---|")

    for i, f in enumerate(analysis["files"], 1):
        status = "✅" if f["additions"] > 0 else ("❌" if f["deletions"] > 0 else "➡️")
        changes = f"+{f['additions']} / −{f['deletions']}"
        lang_icon = {
            "Python": "🐍",
            "Shell": "🐚",
            "JavaScript": "📜",
            "TypeScript": "📘",
            "Markdown": "📝",
            "JSON": "📦",
            "YAML": "⚙️",
            "Dockerfile": "🐳",
            "Go": "🔷",
            "Rust": "🦀",
        }.get(f["language"], "📄")
        lines.append(f"| {i} | `{f['new_path']}` | {lang_icon} {f['language']} | {changes} | {status} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Risks ──
    lines.append("## ⚠️ Risks & Concerns")
    lines.append("")
    if not analysis["risk_findings"]:
        lines.append("✅ **No significant risks detected.**")
        lines.append("")
        lines.append("The changes look clean with no obvious security, stability, or correctness concerns "
                      "based on the static analysis performed.")
        lines.append("")
    else:
        risk_labels = {
            "hardcoded_secret": "🔑 Hardcoded Secret",
            "sql_injection": "🗄️ SQL Injection Risk",
            "command_injection": "💻 Command Injection",
            "eval_exec": "⚠️ Unsafe eval/exec",
            "debug_code": "🐛 Debug Code Left In",
            "large_binary": "📦 Large Binary File",
            "permission_change": "🔒 Permission Change",
            "exception_swallowing": "🙈 Exception Swallowing",
            "unsafe_yaml_load": "📄 Unsafe YAML Load",
            "pickle_load": "🥒 Unsafe Pickle Load",
        }
        lines.append(f"Found **{len(analysis['risk_findings'])}** potential issue(s):")
        lines.append("")
        for rf in analysis["risk_findings"]:
            label = risk_labels.get(rf["type"], rf["type"].replace("_", " ").title())
            lines.append(f"- **{label}** in `{rf['file']}` — `{rf['match']}`")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Improvements ──
    lines.append("## 💡 Suggestions for Improvement")
    lines.append("")
    if not analysis["improvement_findings"]:
        lines.append("✅ **No specific improvement suggestions.**")
        lines.append("")
        lines.append("The code follows good practices. Keep up the great work!")
        lines.append("")
    else:
        impr_labels = {
            "no_error_handling": "🛡️ Error Handling",
            "no_input_validation": "🔍 Input Validation",
            "hardcoded_config": "🔧 Hardcoded Configuration",
            "missing_docstring": "📚 Missing Docstring",
            "bare_except": "⚠️ Bare Except",
        }
        lines.append(f"Found **{len(analysis['improvement_findings'])}** suggestion(s):")
        lines.append("")
        for impr in analysis["improvement_findings"]:
            label = impr_labels.get(impr["type"], impr["type"].replace("_", " ").title())
            lines.append(f"- **{label}** in `{impr['file']}` — `{impr['match']}`")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Detailed Analysis ──
    lines.append("## 📊 Detailed Analysis")
    lines.append("")

    # Languages
    if analysis["languages"]:
        lines.append("### Languages")
        lines.append("")
        lines.append("| Language | Files |")
        lines.append("|---|---|")
        for lang, count in analysis["languages"].most_common():
            lines.append(f"| {lang} | {count} |")
        lines.append("")

    # Largest files
    if analysis["largest_additions"]:
        lines.append("### Most Added Lines")
        lines.append("")
        for path, count in analysis["largest_additions"]:
            lines.append(f"- `{path}` — +{count} lines")
        lines.append("")

    if analysis["largest_deletions"]:
        lines.append("### Most Removed Lines")
        lines.append("")
        for path, count in analysis["largest_deletions"]:
            lines.append(f"- `{path}` — −{count} lines")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Confidence ──
    lines.append("## 🎯 Review Confidence")
    lines.append("")
    bar_len = 20
    filled = round(confidence / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    lines.append(f"**{confidence:.0f}%** `{bar}`")
    lines.append("")
    if confidence >= 80:
        lines.append("*High confidence — the analysis is thorough and reliable.*")
    elif confidence >= 50:
        lines.append("*Moderate confidence — some areas could benefit from deeper review.*")
    else:
        lines.append("*Low confidence — this PR is large or complex; manual review strongly recommended.*")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*🤖 This review was generated automatically by `claude_review.py` "
        "using static analysis. It is not a substitute for human review.*"
    )
    lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Sub-Agent — fetch, analyze, and review GitHub PRs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pr https://github.com/owner/repo/pull/123
  %(prog)s --pr owner/repo/123
  %(prog)s --pr 123 --repo owner/repo
  %(prog)s --pr owner/repo/123 --output review.md
  %(prog)s --pr owner/repo/123 --json
        """,
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="PR URL (https://github.com/owner/repo/pull/123) or short form (owner/repo/123 or just number)",
    )
    parser.add_argument(
        "--repo",
        help="Repository in owner/repo format (required if --pr is just a number)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: print to stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw analysis as JSON instead of Markdown review",
    )

    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_arg(args.pr, args.repo)

    # ── Fetch PR metadata ──
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    pr_data = api_get(api_url)

    # ── Fetch diff ──
    diff_text = api_get(api_url, accept="application/vnd.github.v3.diff")

    if not diff_text.strip():
        print("⚠️ Empty diff — PR may have merge conflicts or no changes.", file=sys.stderr)
        diff_text = ""

    # ── Analyze ──
    print("📊 Analyzing diff...", file=sys.stderr)
    analysis = analyze_diff(diff_text, pr_data)

    # ── Output ──
    if args.json:
        output = json.dumps({
            "pr": {
                "number": pr_number,
                "owner": owner,
                "repo": repo,
                "title": pr_data.get("title"),
                "author": pr_data.get("user", {}).get("login"),
                "state": pr_data.get("state"),
                "url": pr_data.get("html_url"),
            },
            "analysis": {
                "total_files": analysis["total_files"],
                "added_lines": analysis["added_lines"],
                "removed_lines": analysis["removed_lines"],
                "total_hunks": analysis["total_hunks"],
                "languages": dict(analysis["languages"]),
                "risk_findings": analysis["risk_findings"],
                "improvement_findings": analysis["improvement_findings"],
                "confidence": compute_confidence(analysis),
            },
        }, indent=2)
    else:
        output = format_review(pr_data, diff_text, analysis)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
