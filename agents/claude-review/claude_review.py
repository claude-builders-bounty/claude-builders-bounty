#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

GITHUB_API = "https://api.github.com"


def parse_pr_url(pr_url: str) -> Tuple[str, str, str]:
    """
    Extract owner, repo and pull number from a GitHub PR URL.
    """
    parsed = urllib.parse.urlparse(pr_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 4 or path_parts[2] != "pull":
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, _, number = path_parts[:4]
    return owner, repo, number


def github_request(url: str) -> dict:
    """
    Perform a GET request to the GitHub API, handling authentication if GITHUB_TOKEN is set.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_pr_data(owner: str, repo: str, number: str) -> dict:
    """
    Retrieve PR metadata and file diffs.
    """
    pr_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    pr_meta = github_request(pr_url)

    files_url = pr_meta.get("url") + "/files"
    files_data = github_request(files_url)

    diff_parts = []
    changed_files = []
    for f in files_data:
        changed_files.append(f.get("filename", ""))
        patch = f.get("patch")
        if patch:
            diff_parts.append(patch)

    pr_meta["changed_files"] = changed_files
    pr_meta["unified_diff"] = "\n".join(diff_parts)
    return pr_meta


def heuristic_analysis(diff: str, files: List[str]) -> dict:
    """
    Simple static analysis without external services.
    """
    added = len(re.findall(r'^\+', diff, re.MULTILINE))
    removed = len(re.findall(r'^\-', diff, re.MULTILINE))

    risks = []
    suggestions = []

    # Detect insecure patterns
    insecure_patterns = {
        "eval(": "Use of eval can lead to code injection.",
        "exec(": "Use of exec can lead to code injection.",
        "subprocess.Popen": "Spawning subprocesses without sanitization may be unsafe.",
        "os.system": "Direct shell command execution can be unsafe.",
        "pickle.load": "Untrusted pickle loading can be unsafe.",
    }
    for pat, msg in insecure_patterns.items():
        if re.search(re.escape(pat), diff):
            risks.append(f"- Potential security issue: `{pat}` – {msg}")

    # Detect TODO/FIXME
    todo_matches = re.findall(r'^\+.*?(TODO|FIXME).*', diff, re.MULTILINE)
    for match in todo_matches:
        risks.append(f"- Leftover `{match}` comment in added code.")

    # Simple performance hint
    if re.search(r'\bfor\s+.*\brange\(\s*len\(', diff):
        suggestions.append("- Consider iterating directly over the iterable instead of using `range(len(...))` for better readability and performance.")

    # General suggestions
    if added > 200:
        suggestions.append("- Large addition of lines; ensure changes are well‑tested.")
    if removed > 200:
        suggestions.append("- Large removal of lines; verify that no required functionality was unintentionally deleted.")

    confidence = "Medium"
    justification = "Heuristic analysis based on pattern matching."

    return {
        "added": added,
        "removed": removed,
        "risks": risks or ["- No obvious risks detected."],
        "suggestions": suggestions or ["- No specific suggestions; code looks clean."],
        "confidence": confidence,
        "justification": justification,
    }


def build_review(pr: dict, analysis: dict) -> str:
    """
    Assemble the markdown review.
    """
    title = pr.get("title", "Untitled PR")
    body = pr.get("body", "")
    files = pr.get("changed_files", [])
    added = analysis["added"]
    removed = analysis["removed"]

    summary = (
        f"The PR **{title}** modifies {len(files)} file(s) with "
        f"{added} additions and {removed} deletions. "
        f"It appears to aim at {body.splitlines()[0] if body else 'the intended changes'}."
    )

    md = [
        "## PR Review Summary",
        summary,
        "",
        "### Identified Risks",
        "\n".join(analysis["risks"]),
        "",
        "### Improvement Suggestions",
        "\n".join(analysis["suggestions"]),
        "",
        "### Confidence Score",
        f"{analysis['confidence']} – {analysis['justification']}",
    ]
    return "\n".join(md)


def post_comment(owner: str, repo: str, number: str, comment: str) -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set; cannot post comment.")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments"
    data = json.dumps({"body": comment}).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        resp_data = json.load(resp)
    print(f"Comment posted: {resp_data.get('html_url', '')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude‑style PR reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post review as a comment")
    args = parser.parse_args()

    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        sys.exit(str(e))

    try:
        pr_data = fetch_pr_data(owner, repo, number)
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error: {e.code} {e.reason}")

    diff = pr_data.get("unified_diff", "")
    analysis = heuristic_analysis(diff, pr_data.get("changed_files", []))
    review_md = build_review(pr_data, analysis)

    print(review_md)

    if args.post:
        try:
            post_comment(owner, repo, number, review_md)
        except Exception as e:
            sys.exit(f"Failed to post comment: {e}")


if __name__ == "__main__":
    main()
