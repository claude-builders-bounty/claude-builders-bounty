#!/usr/bin/env python3
"""
claude-review - CLI tool to review GitHub PRs with structured Markdown output.

Usage:
    ./claude-review.py --pr https://github.com/owner/repo/pull/123
    ./claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
"""

import argparse
import json
import os as osmod
import re
import sys
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = osmod.environ.get("GITHUB_TOKEN", "")


def api_request(url, accept="application/vnd.github.v3+json"):
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review-agent"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if accept == "application/vnd.github.v3.diff":
                return data.decode("utf-8")
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(url):
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print("Invalid PR URL", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def count_pattern(text, pattern):
    return len(re.findall(pattern, text, re.IGNORECASE))


def generate_review(pr_url, verbose=False):
    owner, repo, pr_num = parse_pr_url(pr_url)
    
    pr_data = api_request(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}")
    pr_title = pr_data.get("title", "N/A")
    pr_state = pr_data.get("state", "N/A")
    author = pr_data.get("user", {}).get("login", "N/A")
    created = pr_data.get("created_at", "N/A")
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)
    
    pr_diff = api_request(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}",
        accept="application/vnd.github.v3.diff"
    )
    
    diff_length = len(pr_diff)
    if diff_length > 50000:
        pr_diff = pr_diff[:50000]
    
    commits_data = api_request(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}/commits")
    commits = []
    for c in commits_data[:10]:
        msg = c["commit"]["message"].split("\n")[0]
        author_login = c.get("commit", {}).get("author", {}).get("name", "unknown")
        commits.append(f"- {msg} ({author_login})")
    
    files_data = api_request(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}/files")
    files_list = []
    for f in files_data[:20]:
        files_list.append(f"- {f['filename']} (+{f['additions']}/-{f['deletions']})")
    
    added_lines = [l for l in pr_diff.split("\n") if l.startswith("+") and not l.startswith("+++")]
    added_text = "\n".join(added_lines)
    
    todos = count_pattern(added_text, r"TODO|FIXME|HACK|XXX")
    console_logs = count_pattern(added_text, r"console\.\s*(log|error|warn|debug)|print\s*\(")
    hardcoded_secrets = count_pattern(added_text, r"api[_-]?key|apikey|secret|password|token|sk-[a-zA-Z0-9]+")
    commented_code = count_pattern(added_text, r"^\+\s*//\s|^\+\s*#\s|^\+\s*/\*")
    magic_numbers = count_pattern(added_text, r"\b\d{6,}\b")
    async_await = count_pattern(added_text, r"async|await")
    error_handling = count_pattern(added_text, r"try\s*\{|catch\s*\(|\.catch\s*\(|error|reject")
    type_annotations = count_pattern(added_text, r":\s*(string|number|boolean|void|any|unknown|never)\b")
    
    test_files = sum(1 for f in files_list if re.search(r"test|spec|__tests__", f, re.IGNORECASE))
    
    summary_lines = []
    summary_lines.append(f"This PR **{pr_title}** ({author}) changes **{changed_files} files** with **+{additions}/-{deletions}** lines.")
    
    if changed_files <= 3:
        summary_lines.append("The change is relatively focused.")
    else:
        summary_lines.append(f"The change touches {changed_files} files - consider splitting into smaller PRs.")
    
    if todos > 0:
        summary_lines.append(f"Contains {todos} TODO/FIXME/HACK markers - resolve before merge.")
    if test_files > 0:
        summary_lines.append("Includes test file changes.")
    elif diff_length > 500:
        summary_lines.append("No test files detected - consider adding tests.")
    if console_logs > 0:
        summary_lines.append(f"Contains {console_logs} debug logging statements.")
    
    summary = "\n".join(f"- {l}" for l in summary_lines)
    
    risks = []
    rn = 1
    if hardcoded_secrets > 0:
        risks.append(f"| {rn} | Hardcoded secrets/tokens | HIGH | {hardcoded_secrets} potential secrets. Use env variables. |")
        rn += 1
    if console_logs > 0:
        risks.append(f"| {rn} | Debug logging | MEDIUM | {console_logs} console.log/print found. |")
        rn += 1
    if todos > 0:
        risks.append(f"| {rn} | Incomplete work markers | MEDIUM | {todos} TODO/FIXME markers. |")
        rn += 1
    if magic_numbers > 0:
        risks.append(f"| {rn} | Magic numbers | MEDIUM | {magic_numbers} unexplained numeric literals. |")
        rn += 1
    if test_files == 0 and diff_length > 500:
        risks.append(f"| {rn} | Missing tests | MEDIUM | No test file changes. |")
        rn += 1
    if commented_code > 0:
        risks.append(f"| {rn} | Commented-out code | LOW | {commented_code} lines. Remove if unused. |")
        rn += 1
    if not risks:
        risks.append("| - | No significant risks detected | LOW | Static analysis clean. |")
    
    suggestions = []
    if error_handling == 0 and diff_length > 1000:
        suggestions.append("- **Error handling**: No try/catch patterns. Add error handling for edge cases.")
    if async_await > 0 and error_handling == 0:
        suggestions.append("- **Async safety**: Async/await without error handling. Ensure error boundaries.")
    if test_files == 0 and diff_length > 500:
        suggestions.append("- **Tests**: Consider adding tests.")
    if not suggestions:
        suggestions.append("- No specific suggestions - well-structured change.")
    
    commit_convention = "Good" if any(kw in str(commits) for kw in ["fix", "feat", "refactor", "docs", "test", "chore"]) else "Check convention"
    error_status = "Present" if error_handling > 0 else "Consider adding"
    debug_status = f"{console_logs} artifacts" if console_logs > 0 else "Clean"
    
    if diff_length < 500:
        confidence = "High (small focused change)"
    elif diff_length < 5000:
        confidence = "High (moderate size)"
    elif diff_length < 20000:
        confidence = "Medium (large diff)"
    else:
        confidence = "Medium (very large diff)"
    
    review = f"""## PR Review

### Overview
| Field | Value |
|-------|-------|
| Repo | {owner}/{repo} |
| PR | #{pr_num} |
| Title | {pr_title} |
| Author | {author} |
| State | {pr_state} |
| Created | {created} |
| Changes | +{additions}/-{deletions}, {changed_files} files |

### Summary
{summary}

### Files
{chr(10).join(files_list) if files_list else "- N/A"}

### Commits
{chr(10).join(commits) if commits else "- N/A"}

### Risks
| # | Risk | Severity | Detail |
|---|------|----------|--------|
{chr(10).join(risks)}

### Suggestions
{suggestions[0] if suggestions else "- None"}

### Quality
- Commit convention: {commit_convention}
- Error handling: {error_status}
- Debug artifacts: {debug_status}

### Confidence
**{confidence}**

---
*Generated by claude-review*"
"""
    return review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True)
    parser.add_argument("--output")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    review = generate_review(args.pr, verbose=args.verbose)
    print(review)
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)


if __name__ == "__main__":
    main()
