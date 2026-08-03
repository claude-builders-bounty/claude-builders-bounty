#!/usr/bin/env python3
"""
claude_review.py — CLI tool that reviews a public GitHub PR and outputs a structured Markdown report.

Usage:
    python claude_review.py https://github.com/owner/repo/pull/123

Bounty: #4 ($150) — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
"""

import json, os, re, sys, urllib.request, urllib.error

VERSION = "1.0.0"
PR_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)$")


class ReviewResult:
    def __init__(self, summary, risks, suggestions, confidence):
        self.summary = summary
        self.risks = risks
        self.suggestions = suggestions
        self.confidence = confidence

    def to_markdown(self, pr_url):
        lines = [
            "## PR Review: " + pr_url,
            "",
            "**Confidence:** " + self.confidence,
            "",
            "### Summary",
            self.summary,
            "",
        ]
        if self.risks:
            lines.append("### Risks")
            for r in self.risks:
                lines.append("- " + r)
            lines.append("")
        if self.suggestions:
            lines.append("### Suggestions")
            for s in self.suggestions:
                lines.append("- " + s)
            lines.append("")
        return "\n".join(lines)


def fetch_json(url, token=None):
    headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_diff(pr_url, token=None):
    m = PR_URL_RE.match(pr_url)
    api_url = "https://api.github.com/repos/" + m.group(1) + "/" + m.group(2) + "/pulls/" + m.group(3)
    headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_pr_metadata(pr_url, token=None):
    m = PR_URL_RE.match(pr_url)
    base = "https://api.github.com/repos/" + m.group(1) + "/" + m.group(2) + "/pulls/" + m.group(3)
    pr_data = fetch_json(base, token)
    files_data = fetch_json(base + "/files", token)
    changed_files = []
    for f in files_data:
        changed_files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes": f["changes"],
        })
    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", ""),
        "state": pr_data.get("state", ""),
        "changed_files": changed_files,
        "total_changes": sum(f["changes"] for f in changed_files),
    }


def analyze_pr(diff, metadata):
    risks = []
    suggestions = []
    summary_parts = []

    diff_lines = diff.split("\n")
    new_code_lines = [l for l in diff_lines if l.startswith("+") and not l.startswith("+++")]

    summary_parts.append(
        "Reviews " + str(metadata["total_changes"]) + " changes (+" +
        str(sum(f["additions"] for f in metadata["changed_files"])) + "/-" +
        str(sum(f["deletions"] for f in metadata["changed_files"])) +
        ") across " + str(len(metadata["changed_files"])) + " files."
    )

    # Detect hardcoded secrets
    for l in new_code_lines:
        if re.search(r"(?i)(api[_-]?key|secret|password|token|credential)\s*[:=]\s*['\"][^'\"]+['\"]", l):
            risks.append("Hardcoded credential: `" + l.strip()[:80] + "`")
            break

    for l in new_code_lines:
        if re.search(r"(?i)gh[pousr]_[a-zA-Z0-9]{36}", l):
            risks.append("GitHub token in code: `" + l.strip()[:80] + "`")
            break

    # Count TODO/FIXME
    todo_count = sum(1 for l in new_code_lines if re.search(r"(?i)\b(TODO|FIXME|HACK|XXX|WORKAROUND)\b", l))
    if todo_count:
        suggestions.append("Found " + str(todo_count) + " TODO/FIXME comments — consider tracking as issues.")

    # Check for tests
    has_tests = any("test" in f["filename"].lower() for f in metadata["changed_files"])
    if not has_tests:
        suggestions.append("No test files detected — consider adding tests for the changes.")

    # Check for dangerous patterns
    for l in new_code_lines:
        s = l.strip()[:80]
        if re.search(r"\beval\s*\(", l):
            risks.append("`eval()` usage — potential code injection risk: `" + s + "`")
        if re.search(r"\bexec\s*\(", l):
            risks.append("`exec()` usage — potential code injection risk: `" + s + "`")
        if re.search(r"subprocess\.(Popen|call|run)\s*\(.*shell=True", l):
            risks.append("`shell=True` in subprocess — command injection risk: `" + s + "`")

    # Large PR
    if metadata["total_changes"] > 500:
        suggestions.append(
            "Large PR (" + str(metadata["total_changes"]) + " changes) — consider splitting into smaller commits."
        )

    # Large single file
    for f in metadata["changed_files"]:
        if f["changes"] > 300:
            suggestions.append(
                "Large change in `" + f["filename"] + "` (" + str(f["changes"]) +
                " lines) — could benefit from refactoring."
            )

    summary = "### " + metadata["title"] + "\n\n"
    if metadata.get("body"):
        summary += metadata["body"][:500]
    else:
        summary += "*No description provided*"
    summary += "\n\n" + "\n".join(summary_parts)

    confidence = "high"
    if risks:
        confidence = "medium"
    if len(risks) > 2:
        confidence = "low"

    return ReviewResult(summary=summary, risks=risks, suggestions=suggestions, confidence=confidence)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("claude_review v" + VERSION)
        print("Usage: python " + sys.argv[0] + " <PR_URL> [--token GITHUB_TOKEN]")
        print("Example: python " + sys.argv[0] + " https://github.com/owner/repo/pull/123")
        sys.exit(0)

    pr_url = sys.argv[1]
    token = None
    if "--token" in sys.argv:
        idx = sys.argv.index("--token")
        if idx + 1 < len(sys.argv):
            token = sys.argv[idx + 1]

    if not PR_URL_RE.match(pr_url):
        print("Error: Invalid PR URL format: " + pr_url, file=sys.stderr)
        print("Expected: https://github.com/{owner}/{repo}/pull/{number}", file=sys.stderr)
        sys.exit(1)

    print("Fetching PR metadata...", file=sys.stderr)
    metadata = fetch_pr_metadata(pr_url, token)

    print("Fetching diff...", file=sys.stderr)
    diff = fetch_diff(pr_url, token)

    print("Analyzing...", file=sys.stderr)
    result = analyze_pr(diff, metadata)

    print(result.to_markdown(pr_url))


if __name__ == "__main__":
    main()
