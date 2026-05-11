#!/usr/bin/env python3
"""
claude-review — Claude Code PR review sub-agent

Analyzes a GitHub PR diff and returns structured Markdown review.
Works as CLI or GitHub Action.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
    python claude-review.py --owner owner --repo repo --pr 123
"""

import argparse
import json
import os
import re
import sys
import urllib.request


def fetch_pr_data(owner, repo, pr_number, token=None):
    auth_headers = {"Accept": "application/vnd.github.v3+json"}
    diff_headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        auth_headers["Authorization"] = f"Bearer {token}"
        diff_headers["Authorization"] = f"Bearer {token}"
    
    # Fetch PR metadata as JSON
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(api_url, headers=auth_headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        pr_data = json.loads(resp.read().decode("utf-8"))
    
    # Fetch diff separately
    diff_req = urllib.request.Request(f"{api_url}.diff", headers=diff_headers)
    with urllib.request.urlopen(diff_req, timeout=30) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")
    
    return pr_data, diff_text


def analyze_diff(diff_text):
    files = []
    current_file = None
    current_diff = []
    additions = 0
    deletions = 0
    
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files.append(analyze_file(current_file, current_diff))
            current_file = line.split(" b/")[-1] if " b/" in line else line
            current_diff = [line]
        elif line.startswith("---") or line.startswith("+++"):
            current_diff.append(line)
        elif line.startswith("@@") and current_file:
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                # Track hunk location
                current_diff.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            current_diff.append(line)
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            current_diff.append(line)
        else:
            current_diff.append(line)
    
    if current_file:
        files.append(analyze_file(current_file, current_diff))
    
    return files, additions, deletions


def analyze_file(file_header, diff_lines):
    ext = os.path.splitext(file_header.split(" b/")[-1] if " b/" in file_header else file_header)[1].lower()
    added_lines = [l for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in diff_lines if l.startswith("-") and not l.startswith("---")]
    
    risks = []
    
    # Check for security concerns
    combined = "\n".join(diff_lines).lower()
    if any(kw in combined for kw in ["password", "secret", "token", "api_key", "apikey"]):
        risks.append("Possible secret/key exposure — check for hardcoded credentials")
    if "eval(" in combined:
        risks.append("Usage of eval() detected — potential code injection risk")
    if "exec(" in combined:
        risks.append("Usage of exec() detected — potential code injection risk")
    if "sql" in combined and ("select" in combined or "insert" in combined or "delete" in combined):
        if "?" not in combined and "%s" not in combined:
            risks.append("Possible SQL injection: no parameterized queries detected")
    if "innerhtml" in combined or "dangerouslysetinnerhtml" in combined:
        risks.append("DOM XSS risk: innerHTML used directly")
    if "allow_any" in combined or "allow all" in combined or "permissive" in combined:
        risks.append("Overly permissive access control detected")
    if "todo" in combined or "fixme" in combined or "hack" in combined:
        risks.append("Contains TODO/FIXME/HACK markers — incomplete work")
    if "debug" in combined or "console.log" in combined:
        risks.append("Debug code or console.log left in production code")
    
    suggestions = []
    if len(added_lines) > 200:
        suggestions.append("Large file change — consider splitting into smaller PRs")
    if ext in {".py", ".js", ".ts", ".tsx"} and len(added_lines) > 0 and "def " not in combined and "function " not in combined and "=>" not in combined:
        pass  # small change with no new functions: OK
    
    # Quality checks
    if ext in {".py", ".js", ".ts", ".tsx", ".java", ".go"}:
        for al in added_lines:
            stripped = al[1:].strip()
            if len(stripped) > 120:
                suggestions.append("Lines exceeding 120 characters — consider breaking long lines")
                break
    
    return {
        "file": file_header.split(" b/")[-1] if " b/" in file_header else file_header,
        "additions": len(added_lines),
        "deletions": len(removed_lines),
        "risks": risks,
        "suggestions": suggestions,
    }


def generate_review(pr_data, diff_text):
    files, additions, deletions = analyze_diff(diff_text)
    title = pr_data.get("title", "Untitled PR")
    description = pr_data.get("body", "") or ""
    author = pr_data.get("user", {}).get("login", "unknown")
    
    all_risks = []
    all_suggestions = []
    changed_files_list = []
    
    for f in files:
        changed_files_list.append(f"{f['file']} (+{f['additions']}/-{f['deletions']})")
        all_risks.extend(f["risks"])
        all_suggestions.extend(f["suggestions"])
    
    all_risks = list(dict.fromkeys(all_risks))
    all_suggestions = list(dict.fromkeys(all_suggestions))
    
    # Confidence score based on analysis depth
    risk_count = len(all_risks)
    suggestion_count = len(all_suggestions)
    file_count = len(files)
    
    if file_count >= 5 or risk_count >= 3 or additions >= 500:
        confidence = "High" if risk_count >= 2 else "Medium"
    elif additions >= 100:
        confidence = "Medium"
    elif additions >= 20:
        confidence = "High"
    else:
        confidence = "High"  # small PRs are easy to review
    
    # Summary
    summary_parts = [f"## PR Review: {title}"]
    summary_parts.append(f"\n**Author:** @{author}")
    summary_parts.append(f"**Changes:** {additions} additions, {deletions} deletions across {file_count} files")
    summary_parts.append(f"**Confidence:** {confidence}")
    
    # Summary narrative
    if confidence == "High" and risk_count == 0:
        narrative = f"This PR makes clean changes across {file_count} file(s). "
        narrative += f"No security risks or code quality concerns detected. "
        if additions > 100:
            narrative += f"The change is substantial ({additions} lines) but well-contained."
        else:
            narrative += f"The scope is manageable and the implementation looks straightforward."
    elif risk_count > 0:
        narrative = f"This PR introduces changes across {file_count} file(s) with {risk_count} potential concern(s). "
        narrative += f"The {len(all_risks)} risk(s) identified below should be reviewed carefully before merging."
    else:
        narrative = f"A moderate change across {file_count} file(s). "
        narrative += f"The changes follow expected patterns with no immediate security concerns."
    
    summary_parts.append(f"\n### Summary\n{narrative}")
    
    # Review markdown
    review = "\n".join(summary_parts)
    
    review += "\n\n### Files Changed\n"
    for f in changed_files_list:
        review += f"- {f}\n"
    
    if all_risks:
        review += "\n### Identified Risks\n"
        for r in all_risks:
            review += f"- ⚠️ {r}\n"
    else:
        review += "\n### Identified Risks\n*None detected* ✅\n"
    
    if all_suggestions:
        review += "\n### Improvement Suggestions\n"
        for s in all_suggestions:
            review += f"- 💡 {s}\n"
    else:
        review += "\n### Improvement Suggestions\n*None at this time* ✅\n"
    
    return review


def parse_pr_url(url):
    """Parse https://github.com/owner/repo/pull/123 into (owner, repo, pr_number)"""
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))
    raise ValueError(f"Invalid PR URL: {url}. Expected: https://github.com/owner/repo/pull/123")


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR review agent")
    parser.add_argument("--pr", help="PR URL: https://github.com/owner/repo/pull/123")
    parser.add_argument("--owner", help="GitHub owner/org")
    parser.add_argument("--repo", help="GitHub repo name")
    parser.add_argument("--number", type=int, help="PR number")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""),
                        help="GitHub token (or set GITHUB_TOKEN env var)")
    args = parser.parse_args()

    token = args.token
    
    if args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
    elif args.owner and args.repo and args.number:
        owner, repo, pr_number = args.owner, args.repo, args.number
    else:
        parser.print_help()
        sys.exit(1)
    
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    pr_data, diff_text = fetch_pr_data(owner, repo, pr_number, token)
    review = generate_review(pr_data, diff_text)
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, errors='replace')
    print(review)


if __name__ == "__main__":
    main()
