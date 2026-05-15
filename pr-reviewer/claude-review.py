#!/usr/bin/env python3
"""
claude-review — Claude Code PR reviewer sub-agent.

Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123

Analyzes a PR diff and produces structured Markdown review with:
  - Summary (2-3 sentences)
  - Identified risks
  - Improvement suggestions
  - Confidence score: Low / Medium / High
"""

import argparse, json, os, re, sys, subprocess
from urllib.request import Request, urlopen


def parse_pr_url(url: str) -> tuple:
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def fetch_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = Request(url, headers=headers)
    resp = urlopen(req)
    return resp.read().decode("utf-8")


def analyze_diff(diff: str) -> dict:
    """Quick static analysis of the diff."""
    lines = diff.split("\n")
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    
    files_changed = set()
    for l in lines:
        if l.startswith("diff --git"):
            parts = l.split()
            if len(parts) >= 3:
                files_changed.add(parts[2].lstrip("a/"))

    risks = []
    diff_lower = diff.lower()
    
    if "console.log" in diff_lower or "console.debug" in diff_lower:
        risks.append("Contains console.log/debug — remove before production")
    if "TODO" in diff or "FIXME" in diff or "HACK" in diff:
        risks.append("Contains TODO/FIXME/HACK comments — address before merging")
    if re.search(r'\.innerHTML\s*=|dangerouslySetInnerHTML', diff):
        risks.append("Uses .innerHTML / dangerouslySetInnerHTML — XSS risk")
    if re.search(r'eval\(', diff):
        risks.append("Uses eval() — code injection risk")
    if re.search(r'password|secret|api_key|token', diff_lower) and not diff_lower.count("os.environ.get") and not diff_lower.count("process.env"):
        risks.append("Possible hardcoded secret — use environment variables")
    if "@ts-ignore" in diff or "@ts-expect-error" in diff:
        risks.append("Contains @ts-ignore/@ts-expect-error — weakens type safety")
    if re.search(r'catch\s*\([^)]*\)\s*\{[^}]*\}', diff):
        pass
    empty_catch = re.findall(r'catch\s*\([^)]*\)\s*\{\s*\}', diff, re.DOTALL)
    if empty_catch:
        risks.append("Contains empty catch block(s) — silent error swallowing")

    suggestions = []
    if additions > 500:
        suggestions.append("Large PR (>500 additions) — consider splitting into smaller PRs")
    if len(files_changed) > 10:
        suggestions.append(f"Touches {len(files_changed)} files — consider narrowing scope")
    if not any(l.startswith("+") and ("test" in l.lower() or "spec" in l.lower() or "describe" in l or "it(" in l) for l in lines):
        suggestions.append("No test additions detected — consider adding tests")
    if "package.json" in "\n".join(lines) and "\"+\"version\"" in diff:
        suggestions.append("Version bump detected — ensure changelog is updated")

    confidence = "High" if len(risks) == 0 and len(suggestions) <= 1 else ("Medium" if len(risks) <= 2 else "Low")

    return {
        "additions": additions,
        "deletions": deletions,
        "files_changed": sorted(files_changed),
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }


def format_review(pr_url: str, analysis: dict) -> str:
    lines = []
    lines.append("# PR Review")
    lines.append("")
    lines.append(f"**PR:** {pr_url}")
    lines.append("")
    
    lines.append("## Summary")
    lines.append("")
    n_files = len(analysis["files_changed"])
    lines.append(f"This PR modifies {n_files} file(s) with +{analysis['additions']}/-{analysis['deletions']} changes across `{', '.join(analysis['files_changed'][:5])}`" + (", ..." if n_files > 5 else "") + ".")
    lines.append("")

    lines.append("## Identified Risks")
    lines.append("")
    if analysis["risks"]:
        for risk in analysis["risks"]:
            lines.append(f"- **⚠️** {risk}")
    else:
        lines.append("- No significant risks identified.")
    lines.append("")

    lines.append("## Improvement Suggestions")
    lines.append("")
    if analysis["suggestions"]:
        for sug in analysis["suggestions"]:
            lines.append(f"- 📝 {sug}")
    else:
        lines.append("- No suggestions.")
    lines.append("")

    lines.append(f"## Confidence: **{analysis['confidence']}**")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        diff = fetch_pr_diff(owner, repo, pr_number)
    except Exception as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff(diff)
    review = format_review(args.pr, analysis)

    if args.stdout:
        print(review)
    else:
        out_file = f"review-{owner}-{repo}-{pr_number}.md"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {out_file}")


if __name__ == "__main__":
    main()