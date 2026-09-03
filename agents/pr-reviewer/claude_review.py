#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def parse_pr_url(url: str) -> tuple[str, str, int]:
    pattern = r"github\.com[/:]([\w.-]+)/([\w.-]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_data(owner: str, repo: str, pull_number: int, token: str | None = None) -> dict:
    headers = {
        "User-Agent": "ClaudeReview-SubAgent/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    # 1. Fetch metadata
    req = urllib.request.Request(base_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    # 2. Fetch files list
    files_url = f"{base_url}/files?per_page=100"
    files_req = urllib.request.Request(files_url, headers=headers)
    with urllib.request.urlopen(files_req) as resp:
        files = json.loads(resp.read().decode("utf-8"))

    return {"meta": meta, "files": files}


def analyze_diff(meta: dict, files: list[dict]) -> dict:
    title = meta.get("title", "")
    additions = meta.get("additions", 0)
    deletions = meta.get("deletions", 0)
    file_count = len(files)

    file_names = [f.get("filename", "") for f in files]
    has_tests = any(re.search(r"(?:test|spec|\.test\.|\.spec_)", f, re.IGNORECASE) for f in file_names)
    has_docs = any(re.search(r"\.(md|mdx|txt)$|docs?/", f, re.IGNORECASE) for f in file_names)
    has_db_migration = any(re.search(r"migration|schema|prisma|drizzle", f, re.IGNORECASE) for f in file_names)
    has_workflows = any(".github/workflows" in f for f in file_names)

    risks = []
    suggestions = []

    # Check dangerous patterns in patch hunks
    secret_patterns = [
        (r"(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})", "Possible raw GitHub token committed."),
        (r"(?:AKIA[0-9A-Z]{16})", "Possible AWS Access Key ID committed."),
        (r"(?:-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)", "Private cryptographic key detected in diff."),
        (r"(?:sk-[a-zA-Z0-9]{48,})", "Possible OpenAI/Anthropic secret key detected.")
    ]

    for f in files:
        patch = f.get("patch", "")
        # Only check added lines
        added_lines = [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
        added_text = "\n".join(added_lines)

        for pat, desc in secret_patterns:
            if re.search(pat, added_text):
                risks.append(f"Security: {desc} in `{f.get('filename')}`.")

        if re.search(r"\brm\s+-[a-zA-Z]*rf\b", added_text):
            risks.append(f"Command risk: Destructive recursive removal ('rm -rf') found in `{f.get('filename')}`.")
        if re.search(r"\bgit\s+push\b.*?--force\b", added_text):
            risks.append(f"Git risk: Forced push command found in `{f.get('filename')}`.")

    # High change volume risk
    if (additions + deletions) > 500:
        risks.append(f"High blast radius: Change diff spans {additions + deletions} lines across {file_count} files, increasing regression risk.")

    # Missing tests risk
    if not has_tests and any(f.endswith((".ts", ".js", ".py", ".go", ".rs", ".java")) for f in file_names):
        risks.append("Test coverage: Application logic was modified without new or updated test suites.")
        suggestions.append("Add unit or integration tests targeting the modified components to verify regression resistance.")

    # DB migration check
    if has_db_migration:
        risks.append("Database: Schema or migration definitions modified. Ensure non-destructive forward/backward compatibility.")
        suggestions.append("Verify rollback safety and data-loss prevention on database schema migrations.")

    # CI workflow modification
    if has_workflows:
        risks.append("CI/CD: GitHub Actions workflows modified. Verify runner permissions and external secret access.")

    # General suggestions
    if not has_docs and file_count > 3:
        suggestions.append("Ensure corresponding documentation or README files reflect architectural changes.")
    if additions > 300 and not suggestions:
        suggestions.append("Consider breaking down extensive multi-file changes into smaller, reviewable increments.")

    if not risks:
        risks.append("No critical security flaws, secrets, or high-risk patterns detected in diff.")

    if not suggestions:
        suggestions.append("Code changes adhere to expected module scope; proceed with standard integration tests.")

    # Confidence calculation
    if any("Security:" in r for r in risks) or (not has_tests and additions > 200):
        confidence = "Low"
    elif len(risks) > 2 or (additions + deletions) > 400:
        confidence = "Medium"
    else:
        confidence = "High"

    # Summary synthesis
    summary = (
        f"Pull Request titled '{title}' modifies {file_count} file(s) with {additions} additions and {deletions} deletions. "
        f"The changes primarily touch {', '.join(file_names[:3])}{' and other files' if file_count > 3 else ''}. "
        f"{'Test modifications are included.' if has_tests else 'No test changes were included in this changeset.'}"
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }


def format_review_markdown(analysis: dict) -> str:
    risks_md = "\n".join(f"- {r}" for r in analysis["risks"])
    suggestions_md = "\n".join(f"- {s}" for s in analysis["suggestions"])

    return f"""## Summary of Changes
{analysis["summary"]}

## Identified Risks
{risks_md}

## Improvement Suggestions
{suggestions_md}

## Confidence Score
**{analysis["confidence"]}**
"""


def post_github_comment(owner: str, repo: str, pull_number: int, comment_body: str, token: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "User-Agent": "ClaudeReview-SubAgent/1.0",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("html_url", "")


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default=None, help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--post-comment", action="store_true", help="Post review directly as a GitHub PR comment")

    args = parser.parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN")

    try:
        owner, repo, pr_num = parse_pr_url(args.pr)
        pr_data = fetch_pr_data(owner, repo, pr_num, token)
        analysis = analyze_diff(pr_data["meta"], pr_data["files"])
        review_md = format_review_markdown(analysis)

        sys.stdout.write(review_md)

        if args.post_comment:
            if not token:
                sys.stderr.write("\nError: GITHUB_TOKEN required to post review comment to GitHub.\n")
                sys.exit(1)
            comment_url = post_github_comment(owner, repo, pr_num, review_md, token)
            sys.stdout.write(f"\nReview comment successfully posted: {comment_url}\n")

    except Exception as err:
        sys.stderr.write(f"Error reviewing PR: {err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
