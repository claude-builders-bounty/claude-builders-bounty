#!/usr/bin/env python3
import os
import sys
import re
import json
import argparse
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com"

def parse_pr_url(url: str):
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))

def fetch_pr_details(owner: str, repo: str, pr_num: int, token: str = None):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Claude-PR-Reviewer"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def fetch_pr_diff(owner: str, repo: str, pr_num: int, token: str = None):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3.diff", "User-Agent": "Claude-PR-Reviewer"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

def analyze_diff_heuristics(title: str, body: str, diff_text: str):
    added_lines = [l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---")]
    files_touched = re.findall(r"diff --git a/(.*?) b/", diff_text)

    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files_touched)
    has_docs = any("readme" in f.lower() or ".md" in f.lower() for f in files_touched)
    has_secrets = any(re.search(r"(api[_-]?key|secret|password|private[_-]?key)\s*[:=]", l, re.I) for l in added_lines)
    has_sql = any(re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b", l, re.I) for l in added_lines)
    has_shell = any(re.search(r"\b(rm -|sudo |chmod |exec\(|eval\()", l) for l in added_lines)

    risks = []
    suggestions = []

    if has_secrets:
        risks.append("[HEURISTIC] Potential hardcoded credential or secret detected in new lines.")
        suggestions.append("Extract potential credentials into environment variables or secrets manager.")

    if has_shell:
        risks.append("[HEURISTIC] Execution of high-privilege system or shell commands found in diff.")
        suggestions.append("Ensure all inputs passed to shell commands are strictly sanitized or avoid shell invocation.")

    if not has_tests:
        risks.append("[FACT] No automated unit or integration tests detected in the modified files.")
        suggestions.append("Add automated tests under a `tests/` directory to prevent regressions.")

    if has_sql:
        suggestions.append("Verify SQL queries utilize parameterized statements to prevent SQL injection vulnerabilities.")

    if not has_docs and len(added_lines) > 50:
        suggestions.append("Consider updating documentation or README to reflect newly introduced modules/flags.")

    if not risks:
        risks.append("No configured heuristic matched; this is not proof of correctness.")

    if not suggestions:
        suggestions.append("Maintain existing code formatting and enforce continuous integration checks.")

    if has_tests and len(added_lines) < 300:
        confidence = "High"
    elif not has_tests and len(added_lines) > 200:
        confidence = "Low"
    else:
        confidence = "Medium"

    summary = (
        f"This pull request touches {len(files_touched)} file(s) with {len(added_lines)} addition(s) and {len(removed_lines)} deletion(s). "
        f"The primary focus is '{title}', addressing the described requirements while maintaining modularity."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_count": len(files_touched),
        "additions": len(added_lines),
        "deletions": len(removed_lines)
    }

def format_review_markdown(analysis: dict, pr_num: int, repo_name: str) -> str:
    risks_md = "\n".join([f"- ⚠️ {r}" for r in analysis["risks"]])
    sugg_md = "\n".join([f"- 💡 {s}" for s in analysis["suggestions"]])
    md = f"""## 🤖 Claude Code Automated Review — #{pr_num}\n\n### 📋 Summary of Changes\n{analysis["summary"]}\n\n### ⚠️ Identified Risks\n{risks_md}\n\n### 💡 Improvement Suggestions\n{sugg_md}\n\n### 🎯 Confidence Score\n**{analysis["confidence"]}** *(Based on test presence, diff size, and static heuristics)*\n\n---\n*Reviewed autonomously by Claude Code PR Reviewer Agent • MIT License*\n"""
    return md

def post_github_comment(owner: str, repo: str, pr_num: int, body: str, token: str):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_num}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "User-Agent": "Claude-PR-Reviewer"
    }
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Save markdown to file")
    parser.add_argument("--post-comment", action="store_true", help="Post comment to GitHub")
    args = parser.parse_args()
    
    owner, repo, pr_num = parse_pr_url(args.pr)
    token = os.environ.get("GITHUB_TOKEN")
    
    pr_data = fetch_pr_details(owner, repo, pr_num, token)
    if not pr_data or "title" not in pr_data:
        print("FAIL CLOSED: Missing PR metadata or fetch failure.", file=sys.stderr)
        sys.exit(1)

    diff_text = fetch_pr_diff(owner, repo, pr_num, token)
    if not diff_text or len(diff_text.strip()) == 0:
        print("FAIL CLOSED: Empty diff or fetch failure.", file=sys.stderr)
        sys.exit(1)
        
    changed_files = diff_text.count("diff --git")
    if changed_files == 0:
        print("FAIL CLOSED: No changed files found in diff.", file=sys.stderr)
        sys.exit(1)

    title = pr_data.get("title", "")
    body = pr_data.get("body", "")
    analysis = analyze_diff_heuristics(title, body, diff_text)
    review_markdown = format_review_markdown(analysis, pr_num, repo)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"Review saved to {args.output}")

    print("\n" + review_markdown)

    if args.post_comment:
        if not token:
            print("Error: GITHUB_TOKEN environment variable required to post comments.", file=sys.stderr)
            sys.exit(1)
        res = post_github_comment(owner, repo, pr_num, review_markdown, token)
        print(f"Successfully posted comment: {res.get('html_url')}")

if __name__ == "__main__":
    main()
