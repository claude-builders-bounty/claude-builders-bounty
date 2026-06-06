#!/usr/bin/env python3
"""
claude-review — AI-powered PR Review Agent

Analyzes a GitHub Pull Request and produces a structured Markdown review
with summary, risks, suggestions, and confidence score.

Usage:
  python claude-review --pr https://github.com/owner/repo/pull/123
  python claude-review --pr 123 --repo owner/repo

Requires GITHUB_TOKEN environment variable or --token argument.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


def parse_args():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", help="PR URL or number (e.g., https://github.com/owner/repo/pull/123 or just 123)")
    parser.add_argument("--repo", help="Repository (owner/repo). Required if --pr is a number.")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--diff-only", action="store_true", help="Only fetch and print the diff, no review")
    return parser.parse_args()


def gh_api(path, token, accept="application/vnd.github.v3+json"):
    """Call GitHub API and return parsed JSON."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"API Error {e.code} for {path}: {body}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_diff(owner, repo, pr_number, token):
    """Fetch the PR diff as text."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"Error fetching diff: {e}", file=sys.stderr)
        return None


def fetch_pr_metadata(owner, repo, pr_number, token):
    """Fetch PR metadata (title, description, changed files, commits)."""
    pr = gh_api(f"/repos/{owner}/{repo}/pulls/{pr_number}", token)
    files = gh_api(f"/repos/{owner}/{repo}/pulls/{pr_number}/files", token)
    commits = gh_api(f"/repos/{owner}/{repo}/pulls/{pr_number}/commits", token)

    changed_files = []
    for f in files[:30]:  # limit to 30 files
        changed_files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
        })

    return {
        "title": pr["title"],
        "body": pr.get("body", "")[:2000],
        "state": pr["state"],
        "author": pr["user"]["login"],
        "base_branch": pr["base"]["ref"],
        "head_branch": pr["head"]["ref"],
        "changed_files": changed_files,
        "total_changes": sum(f.get("changes", 0) for f in files),
        "commits": len(commits),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "created_at": pr.get("created_at", ""),
        "labels": [l["name"] for l in pr.get("labels", [])],
    }


def analyze_pr(metadata, diff):
    """Analyze a PR diff and produce structured review."""
    # Count changed lines split by language
    ext_summary = {}
    for f in metadata["changed_files"]:
        ext = os.path.splitext(f["filename"])[1] or "(no ext)"
        if ext not in ext_summary:
            ext_summary[ext] = {"files": 0, "additions": 0, "deletions": 0}
        ext_summary[ext]["files"] += 1
        ext_summary[ext]["additions"] += f["additions"]
        ext_summary[ext]["deletions"] += f["deletions"]

    # Analyze diff for risk patterns
    risks = []
    suggestions = []

    # Check for common issues in the diff
    if diff:
        # Risk: Large PR
        if metadata["total_changes"] > 500:
            risks.append("Large diff ({}+ changes). Consider splitting into smaller, more focused PRs for easier review.".format(metadata["total_changes"]))

        # Risk: Direct dependency changes
        if re.search(r'(requirements\.txt|package\.json|go\.mod|Cargo\.toml)', diff, re.I):
            pass  # Note but not necessarily a risk

        # Risk: TODO/FIXME/HACK left in code
        todos = re.findall(r'(\+.*(?:TODO|FIXME|HACK|XXX).*)', diff)
        if todos:
            risks.append("{} TODO/FIXME/HACK markers found in new code. These should be addressed or tracked as issues.".format(len(todos)))

        # Risk: Debug/print statements left in
        debug_prints = re.findall(r'(\+.*(?:console\.log|print\(|pprint|logger\.debug).*)', diff)
        if debug_prints and metadata["total_changes"] > 100:
            risks.append("Debug/console statements detected in new code. Remove before merging.")

        # Risk: Commented-out code
        commented = re.findall(r'(\+#.*$)', diff, re.M)
        # Filter to find suspicious commented blocks
        commented_blocks = [l for l in commented if any(kw in l for kw in 
                           ['import ', 'def ', 'class ', 'function ', 'return '])]
        if commented_blocks:
            risks.append("Commented-out code blocks detected (likely old implementations). Remove dead code rather than commenting it out.")

        # Risk: Hardcoded secrets
        secrets = re.findall(r'(\+.*(?:api[_-]?key|secret|password|token|credential)\s*[:=]\s*["\'](?![${\\<\']).{8,})', diff, re.I)
        if secrets:
            risks.append("Potential hardcoded secrets detected. Use environment variables or a secrets manager.")

        # Risk: Large file additions
        for f in metadata["changed_files"]:
            if f["additions"] > 200 and f["status"] != "removed":
                risks.append("Large file addition: `{}` ({}+ lines). Consider whether this can be modularized.".format(
                    f["filename"], f["additions"]))

        # Suggestions
        changed_exts = list(ext_summary.keys())
        if changed_exts:
            suggestions.append("Changes span {} file types. Verify cross-language compatibility.".format(len(changed_exts)))

        if metadata["commits"] == 1 and metadata["total_changes"] > 200:
            suggestions.append("Single commit with large changeset. Consider splitting into logical commits for better traceability.")

        if not metadata.get("body") or len(metadata.get("body", "").strip()) < 50:
            suggestions.append("PR description is brief or missing. Adding context about the problem being solved helps reviewers.")

    # Generate summary
    summary_lines = []
    if metadata["changed_files"]:
        summary_lines.append("This PR modifies **{} files** with **+{}** / **-{}** changes across **{} commit(s)**.".format(
            len(metadata["changed_files"]),
            metadata["additions"],
            metadata["deletions"],
            metadata["commits"],
        ))
        summary_lines.append("")
        summary_lines.append("**File type breakdown:**")
        for ext, info in sorted(ext_summary.items()):
            summary_lines.append("- `{}`: {} file(s) ({}+, {}-)".format(ext or "(other)", info["files"], info["additions"], info["deletions"]))

    summary = "\n".join(summary_lines) if metadata["changed_files"] else "No file changes detected."

    # Confidence score
    confidence = "High"
    if metadata["total_changes"] > 500:
        confidence = "Medium"
    if metadata["total_changes"] > 1000:
        confidence = "Low"
    if len(metadata["changed_files"]) > 15:
        confidence = "Low"

    return {
        "summary": summary,
        "risks": risks if risks else ["No significant risks identified."],
        "suggestions": suggestions if suggestions else ["No additional suggestions."],
        "confidence": confidence,
    }


def format_markdown(metadata, review):
    """Format the review as structured Markdown."""
    lines = []
    lines.append("## PR Review: {}".format(metadata["title"]))
    lines.append("")
    lines.append("> **Repository:** `{}/{}` | **PR #{}** | **Author:** @{} | **Confidence:** {}".format(
        metadata.get("owner", ""), metadata.get("repo", ""),
        metadata.get("pr_number", ""), metadata["author"], review["confidence"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Summary of Changes")
    lines.append("")
    lines.append(review["summary"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Identified Risks")
    lines.append("")
    for r in review["risks"]:
        lines.append("- [ ] {}".format(r))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Improvement Suggestions")
    lines.append("")
    for s in review["suggestions"]:
        lines.append("- {}".format(s))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Review Metadata")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Files Changed | {} |".format(len(metadata["changed_files"])))
    lines.append("| Total Changes | +{}/-{} ({} total) |".format(metadata["additions"], metadata["deletions"], metadata["total_changes"]))
    lines.append("| Commits | {} |".format(metadata["commits"]))
    lines.append("| Base Branch | `{}` |".format(metadata["base_branch"]))
    lines.append("| Head Branch | `{}` |".format(metadata["head_branch"]))
    labels_str = ", ".join(metadata.get("labels", [])) or "(none)"
    lines.append("| Labels | {} |".format(labels_str))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Review generated by claude-review agent_")
    return "\n".join(lines)


def parse_pr_url(pr_url):
    """Parse a PR URL or number into (owner, repo, number)."""
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Just a number
    if pr_url.isdigit():
        return None, None, int(pr_url)
    return None, None, None


def main():
    args = parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not set. Provide --token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    if not args.pr:
        print("Error: --pr is required.", file=sys.stderr)
        sys.exit(1)

    owner, repo, pr_number = parse_pr_url(args.pr)
    if pr_number is None:
        print(f"Error: Cannot parse PR: {args.pr}", file=sys.stderr)
        sys.exit(1)

    # If URL didn't contain owner/repo, use --repo
    if owner is None:
        if not args.repo:
            print("Error: --repo is required when --pr is a number.", file=sys.stderr)
            sys.exit(1)
        if "/" not in args.repo:
            print("Error: --repo must be in format owner/repo.", file=sys.stderr)
            sys.exit(1)
        owner, repo = args.repo.split("/", 1)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    # Fetch metadata
    metadata = fetch_pr_metadata(owner, repo, pr_number, token)
    diff = fetch_pr_diff(owner, repo, pr_number, token)

    if args.diff_only:
        print(diff or "No diff available")
        return

    if not diff:
        print("Warning: Could not fetch diff. Review will be limited to metadata.", file=sys.stderr)

    # Add owner/repo/pr_number for formatting
    metadata["owner"] = owner
    metadata["repo"] = repo
    metadata["pr_number"] = pr_number

    # Analyze
    review = analyze_pr(metadata, diff)

    # Format output
    output = format_markdown(metadata, review)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
