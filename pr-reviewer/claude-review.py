#!/usr/bin/env python3
"""Claude Code PR Reviewer Agent.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo  (shorthand)

Requires: requests, gh CLI (for authenticated GitHub API access)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime


def parse_pr_url(pr_input: str) -> tuple[str, str, int]:
    if pr_input.startswith("http"):
        m = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_input)
        if not m:
            raise ValueError(f"Invalid PR URL: {pr_input}")
        return m.group(1), "github.com", int(m.group(2))
    raise ValueError(f"Unsupported PR URL format: {pr_input}")


def get_pr_data(owner: str, repo: str, pr_number: int) -> dict:
    cmd = [
        "gh", "pr", "view", str(pr_number),
        "--repo", f"{owner}/{repo}",
        "--json", "title,body,files,additions,deletions,author,state,createdAt",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"gh CLI failed: {result.stderr}")
    return json.loads(result.stdout)


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    cmd = ["gh", "pr", "diff", str(pr_number), "--repo", f"{owner}/{repo}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"gh CLI diff failed: {result.stderr}")
    return result.stdout


def analyze_diff(diff: str, pr_data: dict) -> dict:
    lines = diff.splitlines()
    file_changes = {}
    current_file = None

    for line in lines:
        if line.startswith("diff --git"):
            current_file = line.split(" b/")[-1] if " b/" in line else line
            file_changes[current_file] = {"additions": 0, "deletions": 0}
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                file_changes[current_file]["additions"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                file_changes[current_file]["deletions"] += 1

    total_files = len(file_changes)

    tests_found = any("test" in f.lower() or "spec" in f.lower() for f in file_changes)
    docs_found = any(f.endswith(".md") or f.endswith(".mdx") for f in file_changes)
    config_found = any(
        f.endswith(ext) for f in file_changes
        for ext in (".json", ".yaml", ".yml", ".toml", ".env.example", "Dockerfile")
    )

    risk_items = []
    if total_files > 10:
        risk_items.append(f"Large PR: {total_files} files changed — consider splitting")
    if not tests_found and total_files > 1:
        risk_items.append("No test files detected in changeset")
    if pr_data.get("additions", 0) > 500:
        risk_items.append(f"High line count: {pr_data['additions']} additions — review carefully")
    if any("TODO" in line or "FIXME" in line or "HACK" in line for line in lines):
        risk_items.append("Contains TODO/FIXME/HACK markers — may be incomplete")

    confidence = "High"
    if len(risk_items) >= 3:
        confidence = "Low"
    elif len(risk_items) >= 1:
        confidence = "Medium"

    suggestions = []
    if total_files > 10:
        suggestions.append("Consider splitting this PR into smaller, focused PRs")
    if not tests_found and total_files > 1:
        suggestions.append("Add unit tests for new/modified logic")
    if not docs_found and total_files > 5:
        suggestions.append("Consider adding documentation for new features")

    return {
        "files_analyzed": total_files,
        "total_additions": pr_data.get("additions", 0),
        "total_deletions": pr_data.get("deletions", 0),
        "has_tests": tests_found,
        "has_docs": docs_found,
        "has_config": config_found,
        "risks": risk_items,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def generate_review(pr_data: dict, analysis: dict, owner: str, repo: str, pr_number: int) -> str:
    lines = [
        f"# PR Review: {owner}/{repo}#{pr_number}",
        "",
        f"**Title:** {pr_data['title']}",
        f"**Author:** @{pr_data['author']['login']}",
        f"**State:** {pr_data['state']}",
        f"**Created:** {pr_data['createdAt']}",
        f"**Files:** {analysis['files_analyzed']} (+{analysis['total_additions']} / -{analysis['total_deletions']})",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"This PR modifies **{analysis['files_analyzed']} file(s)** with "
        f"**+{analysis['total_additions']}** additions and "
        f"**-{analysis['total_deletions']}** deletions.",
    ]

    if analysis["has_tests"]:
        lines.append("Test files are included in the changeset.")
    if analysis["has_docs"]:
        lines.append("Documentation files are included in the changeset.")
    if analysis["has_config"]:
        lines.append("Configuration files were modified.")

    lines += [
        "",
        "## Identified Risks",
        "",
    ]
    if analysis["risks"]:
        for risk in analysis["risks"]:
            lines.append(f"- ⚠️ {risk}")
    else:
        lines.append("- ✅ No significant risks identified")

    lines += [
        "",
        "## Improvement Suggestions",
        "",
    ]
    if analysis["suggestions"]:
        for sug in analysis["suggestions"]:
            lines.append(f"- 💡 {sug}")
    else:
        lines.append("- ✅ No improvement suggestions")

    confidence_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    emoji = confidence_emoji.get(analysis["confidence"], "⚪")

    lines += [
        "",
        "---",
        "",
        f"**Confidence Score:** {emoji} **{analysis['confidence']}**",
        "",
        f"*Generated by claude-review on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer")
    parser.add_argument("--pr", required=True, help="PR URL or number (with --repo)")
    parser.add_argument("--repo", help="Repository in owner/repo format")
    parser.add_argument("--output", default="-", help="Output file (default: stdout)")
    args = parser.parse_args()

    try:
        if args.repo and args.pr.isdigit():
            owner, repo_name = args.repo.split("/")
            pr_number = int(args.pr)
        else:
            repo_full, _, pr_number = parse_pr_url(args.pr)
            owner, repo_name = repo_full.split("/")

        pr_data = get_pr_data(owner, repo_name, pr_number)
        diff = get_pr_diff(owner, repo_name, pr_number)
        analysis = analyze_diff(diff, pr_data)
        review = generate_review(pr_data, analysis, owner, repo_name, pr_number)

        if args.output == "-":
            print(review)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review)
            print(f"Review saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()