#!/usr/bin/env python3
"""
claude-review — Claude Code PR Review Agent
Reviews a GitHub Pull Request and generates a structured Markdown review.
"""

import argparse
import json
import os
import re
import sys
import urllib.request


# Simple pattern strings (raw strings, no complex groups)
HIGH_RISK_PATTERNS = [
    (r"password\s*=", "Hardcoded password/credential"),
    (r"secret\s*=", "Hardcoded secret"),
    (r"api_key\s*=", "Hardcoded API key"),
    (r"apiKey\s*=", "Hardcoded API key"),
    (r"token\s*=", "Possible hardcoded token"),
    (r"subprocess\.call", "Dangerous code execution"),
    (r"subprocess\.Popen", "Dangerous subprocess execution"),
    (r"os\.system", "Dangerous system call"),
    (r"\bexec\(", "Dangerous exec call"),
    (r"\beval\(", "Dangerous eval call"),
    (r"DROP TABLE", "Destructive database operation"),
    (r"DROP DATABASE", "Destructive database operation"),
    (r"TRUNCATE ", "Bulk data deletion"),
    (r"rm\s+-rf", "Destructive filesystem operation"),
    (r"git push --force", "Force push may rewrite history"),
    (r"innerHTML\s*=", "Dangerous HTML injection"),
    (r"dangerouslySetInnerHTML", "Dangerous React HTML injection"),
    (r"v-html=", "Dangerous Vue HTML injection"),
    (r"Access-Control-Allow-Origin: \*", "Overly permissive CORS"),
]

MEDIUM_RISK_PATTERNS = [
    (r"\bTODO\b", "Unresolved TODO"),
    (r"\bFIXME\b", "Unresolved FIXME"),
    (r"\bHACK\b", "Unresolved HACK note"),
    (r"console\.log", "Stray console.log debug output"),
    (r"console\.debug", "Stray console.debug debug output"),
    (r"\bprint\(.*\)", "Possible debug print statement"),
    (r"\.skip\(", "Skipped test indicator"),
    (r"\.only\(", "Focused test indicator"),
    (r"# type: ignore", "Suppressed type error"),
    (r"# ts-ignore", "Suppressed TypeScript error"),
    (r"@ts-ignore", "Suppressed TypeScript error"),
    (r"sleep\(\d{3,}", "Long sleep may indicate race condition workaround"),
    (r"is\s+None", "Direct None comparison prefer proper null checking"),
    (r"===\s*null", "Direct null comparison prefer proper null checking"),
]


def fetch_pr_data(pr_url: str):
    """Fetch PR diff and metadata from GitHub."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, pr_number = match.group(1), match.group(2), match.group(3)
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    diff_headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        diff_headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(diff_url, headers=diff_headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        diff = resp.read().decode("utf-8")
    md_headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent",
    }
    if token:
        md_headers["Authorization"] = f"Bearer {token}"
    md_req = urllib.request.Request(diff_url, headers=md_headers)
    with urllib.request.urlopen(md_req, timeout=30) as resp:
        metadata = json.loads(resp.read().decode("utf-8"))
    pr_title = metadata.get("title", "")
    pr_body = (metadata.get("body") or "")[:500]
    return pr_title, pr_body, diff


def read_diff_from_file(filepath):
    with open(filepath, "r") as f:
        return f.read()


def analyze_diff(diff):
    findings = {
        "summary": {"files_changed": 0, "additions": 0, "deletions": 0},
        "high_risks": [],
        "medium_risks": [],
        "improvements": [],
        "files": {},
    }
    current_file = ""
    file_additions = 0
    file_deletions = 0
    for line in diff.split("\n"):
        file_match = re.match(r"^\+\+\+\s+(?:b/)?(.+)", line)
        if file_match:
            if current_file:
                findings["files"][current_file] = {"additions": file_additions, "deletions": file_deletions}
            current_file = file_match.group(1)
            file_additions = 0
            file_deletions = 0
            findings["summary"]["files_changed"] += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            file_additions += 1
            findings["summary"]["additions"] += 1
            content = line[1:].strip()
            for pattern, desc in HIGH_RISK_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    findings["high_risks"].append({
                        "file": current_file or "unknown",
                        "line_content": content[:120],
                        "description": desc,
                    })
            for pattern, desc in MEDIUM_RISK_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    findings["medium_risks"].append({
                        "file": current_file or "unknown",
                        "line_content": content[:120],
                        "description": desc,
                    })
        if line.startswith("-") and not line.startswith("---"):
            file_deletions += 1
            findings["summary"]["deletions"] += 1
    if current_file:
        findings["files"][current_file] = {"additions": file_additions, "deletions": file_deletions}
    # Improvement suggestions
    large_files = {f: d for f, d in findings["files"].items() if d["additions"] > 200}
    for f in large_files:
        findings["improvements"].append(
            f"Consider splitting `{f}` into smaller files ({large_files[f]['additions']} lines added)."
        )
    if findings["summary"]["additions"] > 500:
        findings["improvements"].append(
            f"PR is large ({findings['summary']['additions']} additions). Consider breaking into smaller PRs."
        )
    has_test = any("test" in f.lower() or "spec" in f.lower() or "__tests__" in f for f in findings["files"])
    if not has_test and findings["summary"]["additions"] > 50:
        findings["improvements"].append("No test files detected. Consider adding tests.")
    has_docs = any("doc" in f.lower() or "readme" in f.lower() for f in findings["files"])
    if not has_docs and findings["summary"]["files_changed"] > 3:
        findings["improvements"].append("Consider updating documentation.")
    # Confidence
    risk_count = len(findings["high_risks"]) * 3 + len(findings["medium_risks"])
    total = findings["summary"]["additions"] + findings["summary"]["deletions"]
    if total == 0:
        findings["confidence"] = "Low"
    elif risk_count > 10:
        findings["confidence"] = "Low"
    elif risk_count > 3:
        findings["confidence"] = "Medium"
    elif total > 1000:
        findings["confidence"] = "Medium"
    else:
        findings["confidence"] = "High"
    return findings


def format_review(findings, pr_title, pr_body, pr_url):
    lines = []
    s = findings["summary"]
    lines.append("# PR Review Report")
    lines.append("")
    if pr_title:
        lines.append(f"**{pr_title}**")
        lines.append("")
    if pr_url:
        lines.append(f"Link: {pr_url}")
        lines.append("")
    lines.append("## Summary")
    lines.append("")
    if pr_body:
        lines.append(f"> {pr_body}")
        lines.append("")
    lines.append(f"This PR changes **{s['files_changed']}** files (+{s['additions']}/-{s['deletions']} lines).")
    lines.append("")
    if findings.get("files"):
        lines.append("### Changed Files")
        lines.append("")
        lines.append("| File | + | - |")
        lines.append("|------|---|---|")
        for f, d in sorted(findings["files"].items()):
            lines.append(f"| `{f}` | +{d['additions']} | -{d['deletions']} |")
        lines.append("")
    high_risks = findings.get("high_risks", [])
    medium_risks = findings.get("medium_risks", [])
    if high_risks:
        lines.append("## High Risk Issues")
        lines.append("")
        for risk in high_risks:
            lines.append(f"- **{risk['description']}** in `{risk['file']}`")
            lines.append(f"  ```\n  {risk['line_content']}\n  ```")
        lines.append("")
    if medium_risks:
        lines.append("## Medium Risk / Concerns")
        lines.append("")
        for risk in medium_risks:
            lines.append(f"- **{risk['description']}** in `{risk['file']}`")
            lines.append(f"  ```\n  {risk['line_content']}\n  ```")
        lines.append("")
    improvements = findings.get("improvements", [])
    if improvements:
        lines.append("## Improvement Suggestions")
        lines.append("")
        for i, suggestion in enumerate(improvements, 1):
            lines.append(f"{i}. {suggestion}")
        lines.append("")
    confidence = findings.get("confidence", "Medium")
    emoji_map = {"High": "✅", "Medium": "⚠️", "Low": "❌"}
    lines.append("## Review Confidence")
    lines.append("")
    lines.append(f"**{emoji_map.get(confidence, '⚠️')} Confidence: {confidence}**")
    lines.append("")
    if confidence == "High":
        lines.append("Clean PR with minimal concerns. Ready for human review.")
    elif confidence == "Medium":
        lines.append("Some items to address before merge. Review flagged issues above.")
    else:
        lines.append("Significant concerns detected. Requires thorough human review.")
    lines.append("")
    lines.append("---")
    lines.append("_Generated by claude-review-agent_")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", type=str, help="GitHub PR URL")
    parser.add_argument("--diff", type=str, help="Direct diff URL")
    parser.add_argument("--file", type=str, help="Path to a local diff file")
    parser.add_argument("--output", "-o", type=str, help="Output file")
    args = parser.parse_args()
    pr_title = ""
    pr_body = ""
    diff = ""
    pr_url = ""
    if args.pr:
        pr_url = args.pr
        print(f"Fetching PR: {args.pr}")
        pr_title, pr_body, diff = fetch_pr_data(args.pr)
        print(f"  Title: {pr_title}")
    elif args.diff:
        print(f"Fetching diff: {args.diff}")
        req = urllib.request.Request(args.diff, headers={"User-Agent": "claude-review-agent"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            diff = resp.read().decode("utf-8")
        pr_url = args.diff
    elif args.file:
        print(f"Reading diff from file: {args.file}")
        diff = read_diff_from_file(args.file)
    else:
        if not sys.stdin.isatty():
            diff = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)
    if not diff.strip():
        print("No diff content found.")
        sys.exit(1)
    print(f"Analyzing diff ({len(diff)} bytes)...")
    findings = analyze_diff(diff)
    report = format_review(findings, pr_title, pr_body, pr_url)
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print(report)
    print(f"\nStats: {findings['summary']['files_changed']} files, "
          f"+{findings['summary']['additions']}/-{findings['summary']['deletions']} lines, "
          f"confidence={findings['confidence']}")


if __name__ == "__main__":
    main()
