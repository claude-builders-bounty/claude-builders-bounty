#!/usr/bin/env python3
"""claude-review — AI-powered PR Review Agent."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument(
        "--pr",
        required=True,
        help="PR URL or number (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--repo",
        help="Repository (owner/repo). Required if --pr is a number.",
    )
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only fetch and print the diff, no review",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the review as a comment on the pull request",
    )
    return parser.parse_args()


def gh_api(path: str, token: str, accept: str = "application/vnd.github.v3+json") -> Any:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:500]
        print(f"API Error {exc.code} for {path}: {body}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as exc:
        print(f"Error fetching diff: {exc}", file=sys.stderr)
        return None


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh_api(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100&page={page}",
            token,
        )
        if not batch:
            break
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return files


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str) -> dict[str, Any]:
    pr = gh_api(f"/repos/{owner}/{repo}/pulls/{pr_number}", token)
    files = fetch_pr_files(owner, repo, pr_number, token)
    commits = gh_api(f"/repos/{owner}/{repo}/pulls/{pr_number}/commits", token)

    changed_files = [
        {
            "filename": item["filename"],
            "status": item["status"],
            "additions": item.get("additions", 0),
            "deletions": item.get("deletions", 0),
            "changes": item.get("changes", 0),
        }
        for item in files
    ]

    return {
        "title": pr["title"],
        "body": pr.get("body", "")[:2000],
        "state": pr["state"],
        "author": pr["user"]["login"],
        "base_branch": pr["base"]["ref"],
        "head_branch": pr["head"]["ref"],
        "changed_files": changed_files,
        "total_changes": sum(item.get("changes", 0) for item in files),
        "commits": len(commits),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "created_at": pr.get("created_at", ""),
        "labels": [label["name"] for label in pr.get("labels", [])],
    }


def build_narrative_summary(metadata: dict[str, Any]) -> str:
    file_count = len(metadata["changed_files"])
    title = metadata["title"]
    body = metadata.get("body", "").strip()

    if file_count == 0:
        return "No file changes were detected in this pull request."

    summary = (
        f'This pull request titled "{title}" updates {file_count} file(s) with '
        f'+{metadata["additions"]}/-{metadata["deletions"]} lines across '
        f'{metadata["commits"]} commit(s). '
    )

    if body:
        snippet = " ".join(body.split())[:200]
        summary += f"The author describes the change as: {snippet}"
        if not snippet.endswith("."):
            summary += "."
    else:
        summary += (
            "No PR description was provided, so reviewers should infer intent from the diff."
        )

    return summary


def analyze_pr(metadata: dict[str, Any], diff: str | None) -> dict[str, Any]:
    ext_summary: dict[str, dict[str, int]] = {}
    for file_info in metadata["changed_files"]:
        ext = os.path.splitext(file_info["filename"])[1] or "(no ext)"
        if ext not in ext_summary:
            ext_summary[ext] = {"files": 0, "additions": 0, "deletions": 0}
        ext_summary[ext]["files"] += 1
        ext_summary[ext]["additions"] += file_info["additions"]
        ext_summary[ext]["deletions"] += file_info["deletions"]

    risks: list[str] = []
    suggestions: list[str] = []

    if diff:
        if metadata["total_changes"] > 500:
            risks.append(
                f"Large diff ({metadata['total_changes']}+ changes). Consider splitting into "
                "smaller, more focused PRs for easier review."
            )

        todos = re.findall(r"(\+.*(?:TODO|FIXME|HACK|XXX).*)", diff)
        if todos:
            risks.append(
                f"{len(todos)} TODO/FIXME/HACK markers found in new code. "
                "Address them or track as follow-up issues."
            )

        debug_prints = re.findall(
            r"(\+.*(?:console\.log|pprint\(|logger\.debug).*)",
            diff,
        )
        debug_prints.extend(
            re.findall(
                r"(\+.*print\s*\([^)]*(?:debug|DEBUG|temp|tmp|xxx)[^)]*\).*)",
                diff,
                re.I,
            )
        )
        if debug_prints:
            risks.append(
                "Debug/console statements detected in new code. Remove before merging."
            )

        commented = re.findall(r"(\+#.*$)", diff, re.M)
        commented_blocks = [
            line
            for line in commented
            if any(keyword in line for keyword in ("import ", "def ", "class ", "function ", "return "))
        ]
        if commented_blocks:
            risks.append(
                "Commented-out code blocks detected. Remove dead code rather than commenting it out."
            )

        secrets = re.findall(
            r"(\+.*(?:api[_-]?key|secret|password|token|credential)\s*[:=]\s*"
            r'["\'](?![${\\<\']).{8,})',
            diff,
            re.I,
        )
        if secrets:
            risks.append(
                "Potential hardcoded secrets detected. Use environment variables or a secrets manager."
            )

        for file_info in metadata["changed_files"]:
            if file_info["additions"] > 200 and file_info["status"] != "removed":
                risks.append(
                    f"Large file addition: `{file_info['filename']}` ({file_info['additions']}+ lines). "
                    "Consider whether this can be modularized."
                )

        if ext_summary:
            suggestions.append(
                f"Changes span {len(ext_summary)} file types. Verify cross-language compatibility."
            )

        if metadata["commits"] == 1 and metadata["total_changes"] > 200:
            suggestions.append(
                "Single commit with a large changeset. Split into logical commits for traceability."
            )

        if not metadata.get("body") or len(metadata.get("body", "").strip()) < 50:
            suggestions.append(
                "PR description is brief or missing. Add context about the problem being solved."
            )

    detail_lines = []
    if metadata["changed_files"]:
        detail_lines.append("")
        detail_lines.append("**File type breakdown:**")
        for ext, info in sorted(ext_summary.items()):
            detail_lines.append(
                f"- `{ext or '(other)'}`: {info['files']} file(s) "
                f"({info['additions']}+, {info['deletions']}-)"
            )

    confidence = "High"
    if metadata["total_changes"] > 500:
        confidence = "Medium"
    if metadata["total_changes"] > 1000 or len(metadata["changed_files"]) > 15:
        confidence = "Low"

    summary = build_narrative_summary(metadata)
    if detail_lines:
        summary += "\n" + "\n".join(detail_lines)

    return {
        "summary": summary,
        "risks": risks or ["No significant risks identified."],
        "suggestions": suggestions or ["No additional suggestions."],
        "confidence": confidence,
    }


def format_markdown(metadata: dict[str, Any], review: dict[str, Any]) -> str:
    lines = [
        f"## PR Review: {metadata['title']}",
        "",
        (
            f"> **Repository:** `{metadata.get('owner', '')}/{metadata.get('repo', '')}` "
            f"| **PR #{metadata.get('pr_number', '')}** "
            f"| **Author:** @{metadata['author']}"
        ),
        "",
        "---",
        "",
        "### Summary of Changes",
        "",
        review["summary"],
        "",
        "---",
        "",
        "### Identified Risks",
        "",
    ]
    lines.extend(f"- [ ] {risk}" for risk in review["risks"])
    lines.extend(
        [
            "",
            "---",
            "",
            "### Improvement Suggestions",
            "",
        ]
    )
    lines.extend(f"- {suggestion}" for suggestion in review["suggestions"])
    lines.extend(
        [
            "",
            "---",
            "",
            f"### Confidence Score: **{review['confidence']}**",
            "",
            "### Review Metadata",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Files Changed | {len(metadata['changed_files'])} |",
            (
                f"| Total Changes | +{metadata['additions']}/-{metadata['deletions']} "
                f"({metadata['total_changes']} total) |"
            ),
            f"| Commits | {metadata['commits']} |",
            f"| Base Branch | `{metadata['base_branch']}` |",
            f"| Head Branch | `{metadata['head_branch']}` |",
            f"| Labels | {', '.join(metadata.get('labels', [])) or '(none)'} |",
            "",
            "---",
            "",
            "_Review generated by claude-review agent_",
        ]
    )
    return "\n".join(lines)


def post_review_comment(
    owner: str, repo: str, pr_number: int, body: str, token: str
) -> None:
    payload = json.dumps({"body": body}).encode()
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            print(
                f"Posted review comment: {data.get('html_url', '(no url)')}",
                file=sys.stderr,
            )
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode()[:500]
        print(f"Error posting comment: {exc.code} {err_body}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(pr_url: str) -> tuple[str | None, str | None, int | None]:
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))
    if pr_url.isdigit():
        return None, None, int(pr_url)
    return None, None, None


def main() -> None:
    args = parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "Error: GITHUB_TOKEN not set. Provide --token or set GITHUB_TOKEN env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo, pr_number = parse_pr_url(args.pr)
    if pr_number is None:
        print(f"Error: Cannot parse PR: {args.pr}", file=sys.stderr)
        sys.exit(1)

    if owner is None:
        if not args.repo or "/" not in args.repo:
            print("Error: --repo owner/repo is required when --pr is a number.", file=sys.stderr)
            sys.exit(1)
        owner, repo = args.repo.split("/", 1)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    metadata = fetch_pr_metadata(owner, repo, pr_number, token)
    diff = fetch_pr_diff(owner, repo, pr_number, token)

    if args.diff_only:
        print(diff or "No diff available")
        return

    if not diff:
        print(
            "Warning: Could not fetch diff. Review will be limited to metadata.",
            file=sys.stderr,
        )

    metadata["owner"] = owner
    metadata["repo"] = repo
    metadata["pr_number"] = pr_number

    review = analyze_pr(metadata, diff)
    output = format_markdown(metadata, review)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.post:
        post_review_comment(owner, repo, pr_number, output, token)


if __name__ == "__main__":
    main()
