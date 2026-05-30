#!/usr/bin/env python3
"""
claude-review.py — Claude Code PR review sub-agent

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --diff /path/to/diff.txt
  python3 claude-review.py --pr 123 --repo owner/repo
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def run(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        eprint(f"Command failed: {' '.join(cmd)}")
        eprint(result.stderr)
    return result.stdout, result.stderr, result.returncode


def fetch_pr_diff(owner, repo, pr_number, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        eprint(f"HTTP Error {e.code}: {e.reason}")
        return None


def fetch_pr_metadata(owner, repo, pr_number, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        eprint(f"HTTP Error {e.code}: {e.reason}")
        return None


def parse_pr_url(url):
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))
    return None, None, None


def count_lines(diff_text):
    additions = 0
    deletions = 0
    for line in diff_text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return additions, deletions


def parse_diff_files(diff_text):
    files = []
    current_file = None
    current_additions = 0
    current_deletions = 0
    current_changes = []

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files.append({
                    "path": current_file,
                    "additions": current_additions,
                    "deletions": current_deletions,
                    "changes": current_changes,
                })
            current_file = line.split()[-1].lstrip("a/")
            current_additions = 0
            current_deletions = 0
            current_changes = []
        elif line.startswith("+") and not line.startswith("+++"):
            current_additions += 1
            current_changes.append(("add", line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            current_deletions += 1
            current_changes.append(("del", line[1:]))

    if current_file:
        files.append({
            "path": current_file,
            "additions": current_additions,
            "deletions": current_deletions,
            "changes": current_changes,
        })

    return files


def classify_changes(files):
    types = {
        "feat": [],
        "fix": [],
        "refactor": [],
        "docs": [],
        "test": [],
        "config": [],
        "other": [],
    }

    feat_patterns = [r"feat", r"add", r"implement", r"new", r"feature"]
    fix_patterns = [r"fix", r"bug", r"patch", r"correct", r"resolve"]
    refactor_patterns = [r"refactor", r"rename", r"move", r"restruct", r"clean"]
    docs_patterns = [r"doc", r"readme", r"comment", r"md$", r"rst$"]
    test_patterns = [r"test", r"spec", r"__test", r"\.test\."]
    config_patterns = [r"\.json$", r"\.yaml$", r"\.yml$", r"\.toml$", r"\.cfg$",
                       r"dockerfile", r"docker-compose", r"Makefile",
                       r"\.gitignore", r"\.editorconfig"]

    for f in files:
        path = f["path"]
        if any(re.search(p, path, re.I) for p in feat_patterns):
            types["feat"].append(f)
        elif any(re.search(p, path, re.I) for p in fix_patterns):
            types["fix"].append(f)
        elif any(re.search(p, path, re.I) for p in refactor_patterns):
            types["refactor"].append(f)
        elif any(re.search(p, path, re.I) for p in docs_patterns):
            types["docs"].append(f)
        elif any(re.search(p, path, re.I) for p in test_patterns):
            types["test"].append(f)
        elif any(re.search(p, path, re.I) for p in config_patterns):
            types["config"].append(f)
        else:
            types["other"].append(f)

    return types


def find_risks(files):
    risks = []

    for f in files:
        path = f["path"]
        for change_type, content in f["changes"]:
            content_lower = content.strip().lower()

            if "password" in content_lower or "secret" in content_lower or "api_key" in content_lower:
                risks.append(f"Possible secret/credential exposure in `{path}`")

            if re.search(r"(rm|remove|delete)\s+(-rf\s+)?[/~]", content_lower):
                risks.append(f"Potentially destructive command in `{path}`")

            if "eval(" in content or "exec(" in content:
                risks.append(f"Use of eval()/exec() in `{path}` — security concern")

            if "sudo" in content_lower:
                risks.append(f"Sudo usage in `{path}` — may require privilege escalation")

            if "chmod 777" in content or "chmod 0" in content:
                risks.append(f"Overly permissive file permissions in `{path}`")

            if "injection" in content_lower or "sql" in content_lower and "select" in content_lower:
                risks.append(f"Possible injection risk in `{path}`")

            if "TODO" in content or "FIXME" in content or "HACK" in content:
                risks.append(f"Unresolved TODO/FIXME/HACK in `{path}`")

            if "console.log(" in content or "print(" in content and "debug" not in content_lower:
                pass

            if "localhost" in content_lower or "127.0.0.1" in content:
                risks.append(f"Hardcoded localhost reference in `{path}` — may not work in production")

            if "http://" in content:
                risks.append(f"Insecure HTTP URL in `{path}` — use HTTPS")

    return list(set(risks))


def find_improvements(files):
    suggestions = []

    for f in files:
        path = f["path"]
        for change_type, content in f["changes"]:
            content_stripped = content.strip()

            if "except:" in content_stripped and "Exception" not in content_stripped:
                suggestions.append(f"Bare `except:` in `{path}` — catch specific exceptions")

            if "import *" in content_stripped:
                suggestions.append(f"Wildcard import in `{path}` — import specific names instead")

            if content_stripped.count("\t") > 0:
                suggestions.append(f"Tab characters detected in `{path}` — consider using spaces")

            if len(content_stripped) > 120:
                suggestions.append(f"Line too long in `{path}` ({len(content_stripped)} chars) — consider wrapping")

            if "TypeError" in content_stripped or "AttributeError" in content_stripped:
                suggestions.append(f"Unhandled potential exception in `{path}` — add type guards")

    if len(files) > 10:
        suggestions.append("PR is large — consider splitting into smaller, focused PRs")

    return list(set(suggestions))


def compute_confidence(total_additions, total_deletions, risks, files):
    score = 70

    if total_additions + total_deletions > 500:
        score -= 10
    elif total_additions + total_deletions < 50:
        score += 5

    if len(risks) == 0:
        score += 10
    elif len(risks) <= 2:
        score -= 5
    elif len(risks) <= 5:
        score -= 10
    else:
        score -= 20

    if all(f["additions"] <= 50 for f in files):
        score += 5

    if score >= 80:
        return "High"
    elif score >= 50:
        return "Medium"
    else:
        return "Low"


def generate_review(diff_text, pr_url=None, pr_title=None, pr_author=None):
    additions, deletions = count_lines(diff_text)
    files = parse_diff_files(diff_text)
    classifications = classify_changes(files)
    risks = find_risks(files)
    suggestions = find_improvements(files)
    confidence = compute_confidence(additions, deletions, risks, files)

    file_count = len(files)

    change_types = []
    for ctype, flist in classifications.items():
        if flist:
            change_types.append(f"{ctype} ({len(flist)} files)")
    change_summary = ", ".join(change_types)

    total_effort = additions + deletions
    if total_effort < 30:
        size_label = "small"
    elif total_effort < 150:
        size_label = "moderate"
    elif total_effort < 500:
        size_label = "large"
    else:
        size_label = "very large"

    summary_sentences = []
    if pr_title:
        summary_sentences.append(f"This PR {pr_title.lower().strip().lstrip('feat').lstrip('fix').lstrip(':').lstrip()}")
    else:
        summary_sentences.append(f"This PR makes changes across {file_count} file(s) ({additions}+, {deletions}-).")

    summary_sentences.append(f"The changes are predominantly {change_summary} and represent a {size_label} change set.")
    summary_text = " ".join(summary_sentences) + " "

    if pr_url:
        summary_text += f"The PR can be reviewed at {pr_url}. "

    if confidence == "High":
        confidence_note = "The changes appear well-scoped and low-risk."
    elif confidence == "Medium":
        confidence_note = "Some areas warrant closer inspection, particularly the identified risks."
    else:
        confidence_note = "This PR has significant risk factors and should be reviewed carefully."

    summary_text += confidence_note

    review = f"""## PR Review: {pr_title or 'Code Changes'}
**Confidence Score:** {confidence}

### Summary
{summary_text}

### Changes by File
| File | + | - | Type |
|------|---|---|------|
"""

    for f in files:
        path = f["path"]
        ftype = "—"
        for ctype, flist in classifications.items():
            if f in flist:
                ftype = ctype
                break
        review += f"| `{path}` | {f['additions']} | {f['deletions']} | {ftype} |\n"

    if risks:
        review += "\n### Identified Risks\n"
        for i, risk in enumerate(risks, 1):
            review += f"- ⚠️ {risk}\n"
    else:
        review += "\n### Identified Risks\nNo significant risks detected.\n"

    if suggestions:
        review += "\n### Improvement Suggestions\n"
        for i, sugg in enumerate(suggestions, 1):
            review += f"- 💡 {sugg}\n"
    else:
        review += "\n### Improvement Suggestions\nNo improvement suggestions.\n"

    file_details = "\n### Detailed File Analysis\n"
    for f in files:
        path = f["path"]
        added_lines = [c[1] for c in f["changes"] if c[0] == "add"]
        removed_lines = [c[1] for c in f["changes"] if c[0] == "del"]

        file_details += f"\n#### `{path}`\n"
        if added_lines:
            file_details += f"Added {len(added_lines)} line(s)\n"
        if removed_lines:
            file_details += f"Removed {len(removed_lines)} line(s)\n"

    review += file_details

    return review


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR review sub-agent")
    parser.add_argument("--pr", help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", help="Path to diff file")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--token", help="GitHub token (default: GITHUB_TOKEN env var)")
    parser.add_argument("--json", action="store_true", help="Output raw analysis as JSON")

    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    diff_text = None
    pr_url = None
    pr_title = None
    pr_author = None

    if args.pr:
        pr_url = args.pr
        owner, repo, pr_number = parse_pr_url(args.pr)
        if not all([owner, repo, pr_number]):
            eprint(f"{RED}Error: Could not parse PR URL: {args.pr}{RESET}")
            sys.exit(1)

        eprint(f"{CYAN}Fetching PR #{pr_number} from {owner}/{repo}...{RESET}")
        diff_text = fetch_pr_diff(owner, repo, pr_number, token)
        if not diff_text:
            eprint(f"{RED}Error: Failed to fetch PR diff{RESET}")
            sys.exit(1)

        metadata = fetch_pr_metadata(owner, repo, pr_number, token)
        if metadata:
            pr_title = metadata.get("title", "")
            pr_author = metadata.get("user", {}).get("login", "")

            eprint(f"{GREEN}PR: {pr_title} by @{pr_author}{RESET}")
            eprint(f"Files changed: {metadata.get('changed_files', '?')}, "
                   f"+{metadata.get('additions', '?')}/-{metadata.get('deletions', '?')}")

    elif args.diff:
        if args.diff == "-":
            diff_text = sys.stdin.read()
        else:
            with open(args.diff, "r") as f:
                diff_text = f.read()
        eprint(f"{CYAN}Loaded diff from {args.diff}{RESET}")
    else:
        eprint(f"{RED}Error: Provide --pr URL or --diff path{RESET}")
        sys.exit(1)

    eprint(f"{CYAN}Analyzing changes...{RESET}")
    review = generate_review(diff_text, pr_url, pr_title, pr_author)

    if args.json:
        files = parse_diff_files(diff_text)
        additions, deletions = count_lines(diff_text)
        risks = find_risks(files)
        suggestions = find_improvements(files)
        confidence = compute_confidence(additions, deletions, risks, files)
        json_output = json.dumps({
            "pr_url": pr_url,
            "pr_title": pr_title,
            "pr_author": pr_author,
            "files_count": len(files),
            "additions": additions,
            "deletions": deletions,
            "risks": risks,
            "improvement_suggestions": suggestions,
            "confidence": confidence,
            "review_markdown": review,
        }, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(json_output)
            eprint(f"{GREEN}JSON output written to {args.output}{RESET}")
        else:
            print(json_output)
    else:
        if args.output:
            with open(args.output, "w") as f:
                f.write(review)
            eprint(f"{GREEN}Review written to {args.output}{RESET}")
        else:
            print(review)

    eprint(f"{GREEN}Done.{RESET}")


if __name__ == "__main__":
    main()
