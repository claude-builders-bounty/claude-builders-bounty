#!/usr/bin/env python3
"""Claude Code PR Review Agent — CLI tool for structured PR reviews.

Usage:
    ./review.py --pr https://github.com/owner/repo/pull/123
    ./review.py --repo /path/to/local/repo --pr 123
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    patterns = [
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/pull/(\d+)',
        r'github\.com[:/]([^/]+)/([^/]+)/pull/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2), int(match.group(3))
    raise ValueError(f"Invalid PR URL: {url}")


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the diff of a PR using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number),
             "--repo", f"{owner}/{repo}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        # Fallback to raw URL
        url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "pr-review-agent"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode()
    except Exception as e:
        return f"Error fetching diff: {e}"


def fetch_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata: title, description, changed files."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number),
             "--repo", f"{owner}/{repo}",
             "--json", "title,body,additions,deletions,files,changedFiles,headRefName,baseRefName,state",
             "--jq", "."],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {"title": "Unknown", "body": "", "additions": 0, "deletions": 0,
            "changedFiles": 0, "files": []}


def get_changed_files(diff: str) -> list[str]:
    """Extract list of changed files from a diff."""
    files = []
    for line in diff.split("\n"):
        if line.startswith("diff --git a/"):
            file_path = line.split(" b/")[-1]
            files.append(file_path)
    return files


def analyze_diff(diff: str) -> dict:
    """Analyze the diff and produce a structured review."""
    files = get_changed_files(diff)
    
    # Parse per-file diffs
    file_reviews = {}
    current_file = None
    current_lines = []
    
    for line in diff.split("\n"):
        if line.startswith("diff --git a/"):
            if current_file and current_lines:
                file_reviews[current_file] = analyze_file_diff(current_lines)
            current_file = line.split(" b/")[-1]
            current_lines = [line]
        elif current_file:
            current_lines.append(line)
    
    if current_file and current_lines:
        file_reviews[current_file] = analyze_file_diff(current_lines)
    
    # Aggregate findings
    all_risks = []
    all_suggestions = []
    all_positive = []
    overall_confidence = "High"
    risk_count = 0
    total_lines = 0
    
    for fname, review in file_reviews.items():
        all_risks.extend([f"**{fname}**: {r}" for r in review.get("risks", [])])
        all_suggestions.extend([f"**{fname}**: {s}" for s in review.get("suggestions", [])])
        all_positive.extend([f"**{fname}**: {p}" for p in review.get("positive", [])])
        risk_count += len(review.get("risks", []))
        total_lines += sum(sum(1 for _ in v.split('\n')) for v in review.get("_lines", []))
    
    if risk_count >= 5:
        overall_confidence = "Low"
    elif risk_count >= 2:
        overall_confidence = "Medium"
    
    summary = generate_summary(file_reviews, len(files), total_lines)
    
    return {
        "summary": summary,
        "files_changed": files,
        "risks": all_risks[:10],
        "suggestions": all_suggestions[:10],
        "positive": all_positive[:5],
        "confidence": overall_confidence,
        "file_reviews": file_reviews,
    }


def analyze_file_diff(lines: list[str]) -> dict:
    """Analyze the diff for a single file."""
    risks = []
    suggestions = []
    positive = []
    
    diff_text = "\n".join(lines)
    added_lines = []
    
    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
    
    added_text = "\n".join(added_lines)
    
    # Risk patterns
    risk_patterns = [
        (r'(?i)(password|secret|api_key|token|credential)\s*[:=]\s*["\']', "Potential hardcoded secret detected"),
        (r'(?i)(subprocess\.call|os\.system|eval|exec)\s*\(', "Use of dangerous function that could lead to code injection"),
        (r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\+', "Possible SQL injection via string concatenation"),
        (r'(?i)(\.format\(|%\s*\(|\+ )', "Possible injection via unsafe string interpolation in sensitive contexts"),
        (r'ALLOWED_HOSTS\s*=\s*\[\s*"\*"', "Overly permissive ALLOWED_HOSTS"),
        (r'(?i)(DEBUG\s*=\s*True|DEBUG\s*=\s*1)', "Debug mode enabled in production"),
        (r'(?i)(except:\s*(#.*)?$)', "Bare except clause catches all exceptions"),
        (r'(?i)(\.env|SECRET_KEY)\s*[:=]\s*["\'][^"\']+', "Potentially committing environment secrets"),
        (r'(?i)(os\.environ)', "Direct use of environment variables; ensure input validation"),
        (r'(?i)(print\s*\()', "Debug print statement left in code"),
        (r'(?i)(TODO|FIXME|HACK|XXX)', "Unresolved TODO/FIXME marker"),
        (r'(?i)(shutil\.rmtree|os\.remove|os\.unlink)', "File deletion operation; ensure path validation"),
        (r'(?i)(pickle\.loads?|yaml\.load\b|marshal)', "Unsafe deserialization; prefer safe_load"),
    ]
    
    for pattern, message in risk_patterns:
        if re.search(pattern, added_text):
            risks.append(message)
    
    # Suggestion patterns
    suggestion_patterns = [
        (r'(?i)if\s+(a|b|c|d|e|f)\s*(!=|==|is|is not)\s*(None|True|False)', "Consider simplifying boolean comparison"),
        (r'(?i)def\s+\w+\(.*\)\s*:\s*$', "Function with no type hints; consider adding them"),
        (r'(?i)(#.*list|#.*for|\bfor\b)', "Consider if list comprehension could replace loop"),
        (r'(?i)(range\(len\(', "Consider using enumerate() instead of range(len())"),
        (r'(\+\s*1|\-\s*1)', "Magic number; consider using a named constant"),
    ]
    
    for pattern, message in suggestion_patterns:
        if re.search(pattern, added_text):
            suggestions.append(message)
    
    # Positive patterns
    if re.search(r'(?i)(\bclass\b|\bdef\b|\bimport\b|\benum\b)', diff_text):
        positive.append("Well-structured with clear separations")
    if re.search(r'(?i)("""|\'\'\'|# )', diff_text):
        positive.append("Good code documentation present")
    if re.search(r'(?i)(@property|@staticmethod|@classmethod)', diff_text):
        positive.append("Uses Pythonic patterns (decorators)")
    if len(added_text) < 50:
        positive.append("Concise, focused change")
    
    return {
        "risks": risks[:5],
        "suggestions": suggestions[:3],
        "positive": positive[:3],
        "_lines": lines,
    }


def generate_summary(file_reviews: dict, num_files: int, total_lines: int) -> str:
    """Generate a 2-3 sentence summary of the PR."""
    total_risks = sum(len(f.get("risks", [])) for f in file_reviews.values())
    total_suggestions = sum(len(f.get("suggestions", [])) for f in file_reviews.values())
    
    if total_risks == 0 and total_suggestions == 0:
        return f"This PR modifies {num_files} file(s) with clean, well-structured changes. The diff is straightforward and follows good practices. Ready for review with confidence."
    elif total_risks <= 2:
        return f"This PR modifies {num_files} file(s) ({total_lines} lines). Found {total_risks} minor risk(s) and {total_suggestions} suggestion(s). Overall the changes are clean with a few areas to verify."
    else:
        return f"This PR modifies {num_files} file(s) ({total_lines} lines). Found {total_risks} risk(s) and {total_suggestions} suggestion(s). Recommend addressing the highlighted issues before merging."


def format_review(review: dict, pr_url: str) -> str:
    """Format the review as structured Markdown."""
    lines = []
    lines.append("## 🤖 PR Review by Claude Code Agent")
    lines.append("")
    lines.append(f"**PR:** {pr_url}")
    lines.append(f"**Confidence:** {review['confidence']}")
    lines.append(f"**Files Changed:** {len(review['files_changed'])}")
    lines.append("")
    
    # Summary
    lines.append("### 📋 Summary of Changes")
    lines.append(review["summary"])
    lines.append("")
    
    # Risks
    lines.append("### ⚠️ Identified Risks")
    if review["risks"]:
        for i, risk in enumerate(review["risks"], 1):
            lines.append(f"- {risk}")
    else:
        lines.append("- No significant risks detected")
    lines.append("")
    
    # Positive
    lines.append("### ✅ What's Good")
    if review["positive"]:
        for pos in review["positive"]:
            lines.append(f"- {pos}")
    else:
        lines.append("- Changes serve their intended purpose")
    lines.append("")
    
    # Improvements
    lines.append("### 💡 Improvement Suggestions")
    if review["suggestions"]:
        for sug in review["suggestions"]:
            lines.append(f"- {sug}")
    else:
        lines.append("- None at this time")
    lines.append("")
    
    # File list
    lines.append("### 📁 Files Changed")
    for f in review["files_changed"]:
        lines.append(f"- `{f}`")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("*Generated by PR Review Agent*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — structured Markdown review comments"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    group.add_argument("--local", help="Local PR number in the current repo")
    parser.add_argument("--repo", help="GitHub repo (owner/repo) for local PR number mode")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    if args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
        pr_url = args.pr
    elif args.local:
        pr_number = int(args.local)
        if args.repo:
            owner, repo = args.repo.split("/")
        else:
            # Try to detect from git remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                print("Error: Could not determine repo. Use --repo owner/repo")
                sys.exit(1)
            remote_url = result.stdout.strip()
            match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(\.git)?$', remote_url)
            if not match:
                print("Error: Could not parse repo from git remote")
                sys.exit(1)
            owner, repo = match.group(1), match.group(2)
        pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
    else:
        print("Error: Provide --pr or --local")
        sys.exit(1)
    
    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    
    meta = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)
    
    if diff.startswith("Error"):
        print(diff, file=sys.stderr)
        sys.exit(1)
    
    print(f"📊 Analyzing {len(diff)} bytes of diff...", file=sys.stderr)
    review = analyze_diff(diff)
    review["pr_title"] = meta.get("title", "")
    review["pr_author"] = meta.get("author", "")
    
    output = format_review(review, pr_url)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
