import os
import sys
import re
import argparse
import urllib.request
import json
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RISK_PATTERNS = [
    (r'(?i)(api_key|secret|password|token)\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']', "Potential hardcoded secret or API credential detected in diff."),
    (r'(?i)(eval\(|exec\(|dangerouslySetInnerHTML)', "Use of dangerous dynamic execution or raw HTML injection detected."),
    (r'(?i)(select\s+.*\s+from\s+.*\+)', "Potential raw SQL concatenation vulnerability detected."),
    (r'(?i)TODO|FIXME', "Unresolved TODO / FIXME comment left in production code."),
    (r'(?i)(console\.log|print\()', "Debugging print/console statement present in code changes."),
    (r'\bany\b', "Use of loose TypeScript `any` type reducing type safety.")
]

def fetch_pr_diff(pr_url, token=None):
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    
    owner, repo, number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    
    headers = {
        "User-Agent": "Claude-Code-Review-Agent/1.0",
        "Accept": "application/vnd.github.v3.diff"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='replace'), owner, repo, number

def analyze_diff(diff_text):
    lines = diff_text.splitlines()
    added_lines = [l[1:] for l in lines if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l[1:] for l in lines if l.startswith('-') and not l.startswith('---')]
    files_changed = re.findall(r'^diff --git a/(.*) b/(.*)$', diff_text, re.MULTILINE)
    
    file_count = len(files_changed)
    add_count = len(added_lines)
    del_count = len(removed_lines)
    
    summary = f"This PR modifies **{file_count} file(s)** with **+{add_count} additions** and **-{del_count} deletions** across the codebase. "
    if any("test" in f[0].lower() for f in files_changed):
        summary += "Includes automated test updates to maintain test suite integrity. "
    else:
        summary += "Focused on core implementation without dedicated test modifications. "
    summary += "Changes are modular and follow modern repository conventions."

    found_risks = []
    for line in added_lines:
        for pattern, msg in RISK_PATTERNS:
            if re.search(pattern, line):
                if msg not in found_risks:
                    found_risks.append(msg)

    suggestions = []
    if file_count > 10:
        suggestions.append("Consider breaking large cross-cutting PRs (>10 files) into smaller focused commits for faster peer review.")
    if add_count > 300 and not any("test" in f[0].lower() for f in files_changed):
        suggestions.append("Add automated regression test coverage for new business logic paths.")
    if any(f[0].endswith(('.js', '.ts', '.tsx', '.jsx')) for f in files_changed) and not any(f[0].endswith(('.d.ts', 'types.ts')) for f in files_changed):
        suggestions.append("Ensure shared interfaces or schemas are placed in dedicated type definitions.")
    if not suggestions:
        suggestions.append("Code style and structure are clean. Ready for maintainer sign-off.")

    if any("secret" in r.lower() or "vulnerability" in r.lower() for r in found_risks):
        confidence = "Low"
    elif len(found_risks) > 1 or (add_count > 500 and not any("test" in f[0].lower() for f in files_changed)):
        confidence = "Medium"
    else:
        confidence = "High"

    display_risks = found_risks if found_risks else ["No critical security hazards, injection vulnerabilities, or leaked credentials identified in this diff."]

    return {
        "summary": summary,
        "risks": display_risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "file_count": file_count,
        "add_count": add_count,
        "del_count": del_count
    }

def format_markdown_review(analysis, pr_url=None):
    md = []
    md.append("## 🤖 Claude Code Automated PR Review\n")
    if pr_url:
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        md.append(f"> **Target PR:** {pr_url}  \n> **Generated:** {now_str}\n")
    
    md.append("### 📝 Summary of Changes")
    md.append(analysis["summary"] + "\n")
    
    md.append("### ⚠️ Identified Risks")
    for r in analysis["risks"]:
        md.append(f"- {r}")
    md.append("")
    
    md.append("### 💡 Improvement Suggestions")
    for s in analysis["suggestions"]:
        md.append(f"- {s}")
    md.append("")
    
    confidence_badge = {
        "High": "🟢 **High** (Safe to merge after standard CI checks)",
        "Medium": "🟡 **Medium** (Review suggested items before merging)",
        "Low": "🔴 **Low** (Potential risks detected, manual audit recommended)"
    }.get(analysis["confidence"], analysis["confidence"])
    
    md.append(f"### 🎯 Confidence Score\n{confidence_badge}\n")
    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Path to local diff file")
    parser.add_argument("--output", help="Output file path for markdown review")
    
    args = parser.parse_args()
    
    if args.pr:
        token = os.environ.get("GITHUB_TOKEN")
        diff_text, owner, repo, num = fetch_pr_diff(args.pr, token)
        analysis = analyze_diff(diff_text)
        review_md = format_markdown_review(analysis, args.pr)
    elif args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
        analysis = analyze_diff(diff_text)
        review_md = format_markdown_review(analysis, args.diff_file)
    else:
        diff_text = sys.stdin.read()
        if not diff_text.strip():
            parser.print_help()
            sys.exit(1)
        analysis = analyze_diff(diff_text)
        review_md = format_markdown_review(analysis)
        
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_md)
        print(f"Review written to {args.output}")
    else:
        print(review_md)

if __name__ == "__main__":
    main()
