#!/usr/bin/env python3
"""claude-review: AI-powered PR review agent.

Zero-dependency Python tool for automated pull request review.
Detects security vulnerabilities, performance issues, and code quality problems
from a PR diff.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --diff-file /tmp/pr.diff
    python claude_review.py --pr 123 --repo owner/repo --output review.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI-powered PR review agent (zero deps)")
    p.add_argument("--pr", help="PR URL or number")
    p.add_argument("--repo", help="Repository (owner/repo)")
    p.add_argument("--diff-file", help="Path to diff file")
    p.add_argument("--github-token", help="GitHub token", default=os.getenv("GITHUB_TOKEN", ""))
    p.add_argument("--output", "-o", help="Output file (default: stdout)")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--severity", choices=["all", "critical", "high"], default="all", help="Minimum severity level")
    return p.parse_args()


def http_get(url: str, token: str, accept: str = "application/json") -> Any:
    """HTTP GET with auth, returns parsed JSON or raw text."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}", "Accept": accept, "User-Agent": "claude-review"
    })
    resp = urllib.request.urlopen(req, timeout=30)
    data = resp.read().decode("utf-8")
    if "application/json" in accept or url.endswith(".json"):
        return json.loads(data)
    return data


def fetch_pr_diff(repo: str, pr_num: str, token: str) -> str:
    """Fetch PR diff from GitHub API."""
    return http_get(
        f"https://api.github.com/repos/{repo}/pulls/{pr_num}",
        token, "application/vnd.github.v3.diff"
    )


def fetch_pr_meta(repo: str, pr_num: str, token: str) -> dict:
    """Fetch PR metadata."""
    try:
        return http_get(f"https://api.github.com/repos/{repo}/pulls/{pr_num}", token)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Security vulnerability patterns (CWE-referenced)
# ---------------------------------------------------------------------------
SECURITY_PATTERNS = [
    # (pattern, severity, cwe, message)
    (r"shell\s*=\s*True", "critical", "CWE-78", "OS Command Injection: shell=True allows arbitrary command execution. Use subprocess.run with argument list."),
    (r"os\.system\(|os\.popen\(|subprocess\.Popen.*shell=True", "critical", "CWE-78", "OS Command Injection: direct shell execution detected."),
    (r"eval\(|exec\(|compile\(", "critical", "CWE-95", "Code Injection: eval/exec/compile can execute arbitrary code. Never use on user input."),
    (r"\.innerHTML\s*=|\.outerHTML\s*=|dangerouslySetInnerHTML|v-html=", "high", "CWE-79", "XSS: Direct HTML injection. Use safe rendering methods like textContent or React's JSX."),
    (r"document\.write\(|document\.writeln\(", "high", "CWE-79", "XSS: document.write can inject arbitrary HTML. Use DOM manipulation APIs instead."),
    (r"SELECT\s+.*\s+FROM|INSERT\s+INTO|DROP\s+TABLE", "high", "CWE-89", "SQL statement detected. Verify queries use parameterized statements, not string interpolation."),
    (r"['\"]\s*\+\s*(request|params|query|body|input|req\.)", "high", "CWE-89", "SQL Injection Risk: String concatenation with user input in query. Use parameterized queries."),
    (r"yaml\.load\(|pickle\.loads\(|xml\.etree\.ElementTree\.fromstring", "critical", "CWE-502", "Insecure Deserialization: can lead to RCE. Use yaml.safe_load / defusedxml."),
    (r"api.?key\s*=\s*['\"][^'\"]{16,}|secret\s*=\s*['\"][^'\"]{8,}|token\s*=\s*['\"][^'\"]{16,}|password\s*=\s*['\"][^'\"]{4,}", "critical", "CWE-798", "Hardcoded credential detected. Use environment variables or a secrets manager."),
    (r"urllib\.request\.urlopen\(|requests\.get\(|requests\.post\(|httpx\.get\(", "medium", "CWE-918", "SSRF Risk: Server-side request. If URL comes from user input, validate against allowlist."),
    (r"os\.path\.join\(.*request|os\.path\.join\(.*input|os\.path\.join\(.*params|\.\.\/", "high", "CWE-22", "Path Traversal: user-controlled input in file path. Validate and sanitize."),
    (r"json\.loads\(.*request|json\.loads\(.*input|json\.loads\(.*body", "medium", "CWE-20", "JSON input validation: wrap in try/except to prevent unhandled parse errors."),
    (r"redirect\(|redirect_to\(|Redirect\(|Location:", "medium", "CWE-601", "Open Redirect: if URL comes from user input, validate against allowlist."),
    (r"@csrf_exempt|csrf_exempt|csrf_protect\s*=\s*False", "high", "CWE-352", "CSRF protection disabled. Ensure this endpoint has alternative protection."),
    (r"algorithm.*none|'none'.*algorithms", "high", "CWE-347", "JWT None Algorithm: using 'none' algorithm bypasses signature verification."),
    (r"allow_redirects\s*=\s*True|follow_redirects\s*=\s*True", "low", "CWE-601", "Unvalidated redirect following could be chained in SSRF attacks."),
]

PERFORMANCE_PATTERNS = [
    (r"for\s+.*\bquery\b|for\s+.*\.all\(\)|for\s+.*\.find\(", "medium", "N+1 Query: database query inside a loop. Consider batch loading or eager loading."),
    (r"import\s+\*\s*$", "medium", "Wildcard import wastes memory. Import only what you need."),
    (r"print\(|console\.log\(|debugger|pdb\.set_trace\(\)", "low", "Debug code left in. Remove before production deployment."),
    (r"except\s*:\s*pass|except\s+Exception\s*:\s*pass", "high", "Bare except with pass silently swallows all errors. Log or handle specific exceptions."),
    (r"sleep\(|time\.sleep\(", "medium", "time.sleep() blocks the thread. Use async/schedule patterns for production."),
    (r"range\(\d{5,}\)|range\(\d{6,}", "medium", "Very large range detected. Consider lazy evaluation or batching."),
    (r"(\d{4,})\s*\*\s*\1|O\(n\^2\)", "low", "Potential O(n^2) complexity. Consider optimizing the algorithm."),
]

CODE_QUALITY_PATTERNS = [
    (r"\bTODO\b|\bFIXME\b|\bHACK\b|\bXXX\b", "low", "Unresolved TODO/FIXME/HACK in code. Address before merging."),
    (r"#\s*type:\s*ignore|@ts-ignore|@ts-expect-error", "medium", "Type checker suppression. Fix underlying type issue instead of silencing."),
    (r"except\s*:|\bexcept\s", "low", "Broad exception handling. Catch specific exceptions where possible."),
    (r"if\s+(\w+)\s*!=\s*None|if\s+(\w+)\s*is\s+not\s+None", "info", "Explicit None check. Consider using `if x is not None` consistently."),
    (r"(\w+)\s*=\s*\[\]\s*(\n|;)\s*for.*\1\.append", "low", "Consider list comprehension instead of loop + append pattern."),
]

FINDING_TEMPLATE = {
    "critical": "🔴 CRITICAL",
    "high": "🟠 HIGH",
    "medium": "🟡 MEDIUM",
    "low": "🔵 LOW",
    "info": "ℹ️ INFO",
}


def analyze_diff(diff_text: str, min_severity: str = "all") -> tuple:
    """Analyze a PR diff for security, performance, and code quality issues."""
    files_raw = re.split(r"^diff --git ", diff_text, flags=re.MULTILINE)
    files_raw = [f for f in files_raw if f.strip()]

    stats = {"files_changed": 0, "additions": 0, "deletions": 0, "file_types": Counter()}
    findings = []
    all_lines = diff_text.splitlines()

    for i, f in enumerate(files_raw):
        if not f.strip():
            continue
        stats["files_changed"] += 1

        hm = re.search(r"a/(.+?) b/(.+?)$", f, re.MULTILINE)
        filename = hm.group(2) if hm else f"file_{i}"
        ext = os.path.splitext(filename)[1].lower() or "no_ext"
        stats["file_types"][ext] += 1

        added = len(re.findall(r"^\+(?!\+)", f, re.MULTILINE))
        removed = len(re.findall(r"^-(?!-)", f, re.MULTILINE))
        stats["additions"] += added
        stats["deletions"] += removed

        file_findings = []
        file_body_lines = f.splitlines()
        for line_idx, line in enumerate(file_body_lines):
            if not line.startswith("+"):
                continue

            for pattern, severity, msg in SECURITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    cwe = msg.split(":")[0] if ":" in msg else ""
                    file_findings.append({
                        "severity": severity, "type": "security",
                        "pattern": pattern, "message": msg, "line": line_idx,
                        "code": line.strip()[:120],
                        "cwe": cwe
                    })

            for pattern, severity, msg in PERFORMANCE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    file_findings.append({
                        "severity": severity, "type": "performance",
                        "pattern": pattern, "message": msg, "line": line_idx,
                        "code": line.strip()[:120]
                    })

            for pattern, severity, msg in CODE_QUALITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    file_findings.append({
                        "severity": severity, "type": "quality",
                        "pattern": pattern, "message": msg, "line": line_idx,
                        "code": line.strip()[:120]
                    })

        if file_findings:
            findings.append({"file": filename, "additions": added, "deletions": removed, "issues": file_findings})

    return stats, findings


def generate_report(meta: dict, stats: dict, findings: list, fmt: str = "markdown", min_severity: str = "all") -> str:
    """Generate review report in markdown or JSON."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    title = meta.get("title", "PR Review")

    if fmt == "json":
        return json.dumps({
            "title": title,
            "author": meta.get("user", {}).get("login", "unknown"),
            "url": meta.get("html_url", ""),
            "generated_at": now,
            "stats": {k: dict(v) if isinstance(v, Counter) else v for k, v in stats.items()},
            "findings": findings,
            "summary": {"total_issues": sum(len(f["issues"]) for f in findings)}
        }, indent=2)

    # Markdown
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    total_issues = 0
    for f in findings:
        for issue in f["issues"]:
            if min_severity == "all" or severity_order.get(issue["severity"], 99) <= severity_order.get(min_severity, 0):
                total_issues += 1

    md = []
    md.append(f"# 🔍 PR Review: {title}")
    md.append("")
    md.append(f"**Generated:** {now}  ")
    if meta.get("user"):
        md.append(f"**Author:** @{meta['user']['login']}  ")
    if meta.get("html_url"):
        md.append(f"**PR:** [{meta['html_url']}]({meta['html_url']})  ")
    md.append("")

    # Summary table
    md.append("## 📊 Summary")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|---|---|")
    md.append(f"| Files changed | {stats['files_changed']} |")
    md.append(f"| Additions | {stats['additions']} |")
    md.append(f"| Deletions | {stats['deletions']} |")
    ft = ", ".join(f"{k}: {v}" for k, v in stats["file_types"].most_common())
    md.append(f"| File types | {ft} |")
    md.append(f"| Issues found | {total_issues} |")
    severity_counts = Counter(i["severity"] for f in findings for i in f["issues"])
    sev_str = ", ".join(f"{FINDING_TEMPLATE[s]} {c}" for s, c in severity_counts.most_common() if s in FINDING_TEMPLATE)
    md.append(f"| Issue breakdown | {sev_str} |")
    md.append("")

    # Issues by file
    if findings:
        md.append("## 🚨 Issues Found")
        md.append("")

        for fi in findings:
            file_issues = [
                i for i in fi["issues"]
                if min_severity == "all" or severity_order.get(i["severity"], 99) <= severity_order.get(min_severity, 0)
            ]
            if not file_issues:
                continue

            md.append(f"### 📁 `{fi['file']}` (+{fi['additions']}/-{fi['deletitions']})")
            md.append("")

            for issue in file_issues:
                sev_label = FINDING_TEMPLATE.get(issue["severity"], "⚪")
                issue_type = issue.get("type", "").upper()
                cwe = f" `{issue.get('cwe','')}`" if issue.get('cwe') else ""
                md.append(f"- {sev_label} [{issue_type}]{cwe} {issue['message']}")
                code = issue.get("code", "")
                if code and len(code) > 10:
                    md.append(f"  ```")
                    md.append(f"  {code[:100]}")
                    md.append(f"  ```")
            md.append("")

    # Recommendations
    md.append("## ✅ Recommendations")
    md.append("")
    if stats["additions"] > 400:
        md.append(f"- 📏 PR is large (+{stats['additions']} lines). Consider splitting into smaller changes.")
    if stats["files_changed"] > 10:
        md.append(f"- 📂 High file count ({stats['files_changed']}). Verify scope is focused.")
    vuln_count = sum(1 for f in findings for i in f["issues"] if i["type"] == "security")
    if vuln_count > 0:
        md.append(f"- 🔒 {vuln_count} security issues found. Address before merging.")
    md.append("- ✅ Ensure all new code has corresponding unit tests.")
    md.append("- 📖 Add or update documentation for any new public APIs.")
    md.append("- 🔄 Run the full test suite before merging.")
    md.append("")
    md.append("---")
    md.append(f"*Review generated by claude-review • {now}*")

    return "\n".join(md)


def main():
    args = parse_args()

    if args.diff_file:
        with open(args.diff_file) as f:
            diff_text = f.read()
        meta = {}
    elif args.pr:
        parts = args.pr.replace("https://github.com/", "").split("/pull/") if "/" in args.pr else [args.repo, args.pr]
        if len(parts) < 2 and not args.repo:
            print("Error: --repo required when --pr is a number", file=sys.stderr)
            sys.exit(1)
        repo, pr_num = parts[0] if "/" in args.pr else (args.repo, args.pr)
        diff_text = fetch_pr_diff(repo, pr_num, args.github_token)
        meta = fetch_pr_meta(repo, pr_num, args.github_token)
    else:
        print("Usage: provide --pr or --diff-file", file=sys.stderr)
        sys.exit(1)

    stats, findings = analyze_diff(diff_text, args.severity)
    output = generate_report(meta, stats, findings, args.format, args.severity)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
