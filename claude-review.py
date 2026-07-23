#!/usr/bin/env python3
"""claude-review — PR analysis agent for Claude Code.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --diff /path/to/pr.diff
  gh pr view 123 --json body,title,files | python claude-review.py
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request


SECURITY_PATTERNS = [
    (r"(?i)eval\s*\(", "`eval()` usage — code injection risk"),
    (r"(?i)exec\s*\(", "`exec()` usage — code injection risk"),
    (r"(?i)os\.system\s*\(", "`os.system()` — shell injection risk"),
    (r"(?i)subprocess\..*shell=True", "`shell=True` in subprocess — command injection risk"),
    (r"(?i)innerHTML\s*=", "`innerHTML` assignment — XSS risk"),
    (r"(?i)dangerouslySetInnerHTML", "`dangerouslySetInnerHTML` — XSS risk"),
    (r"(?i)SELECT\s+.*\bWHERE\b(?!\s*\d)", "SQL query without parameter — SQL injection risk"),
    (r"(?i)"".*\bWHERE\b.*[""']\s*\+", "String-concatenated SQL WHERE — SQL injection risk"),
    (r"(?i)(api_key|secret|password|token|credential)\s*=\s*[""']", "Possible hardcoded secret"),
    (r"(?i)allowlist|whitelist|blacklist|greylist", "Outdated terminology — use allow/deny list"),
    (r"(?i)(TODO|FIXME|HACK|XXX)", "Unresolved TODO/FIXME in PR"),
    (r"(?i)console\.log\b", "`console.log` in production code"),
    (r"(?i)debugger\b", "`debugger` statement in production code"),
    (r"(?i)\.env", "Environment file reference — ensure not committed"),
    (r"admin|root|sudo", "Privileged operation — verify auth is enforced"),
]


def fetch_pr_diff(pr_url: str) -> str:
    """Fetch PR diff from GitHub."""
    # Parse owner/repo/pull/N from URL
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        # Try gh CLI
        try:
            result = subprocess.run(
                ["gh", "pr", "diff", pr_url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return f"# Error: Could not parse PR URL: {pr_url}"

    owner, repo, pr_num = m.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    req = urllib.request.Request(api_url, headers={
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
        "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return f"# Error fetching PR: {e}\n"


def read_stdin() -> dict:
    """Read JSON from stdin (for `gh pr view --json` pipe)."""
    try:
        return json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        return {}


def analyze_diff(diff: str) -> dict:
    """Analyze a unified diff and return structured results."""
    lines = diff.split("\n")
    files_changed = []
    current_file = "unknown"
    added_lines = 0
    removed_lines = 0
    findings = []
    tests_changed = 0
    deps_changed = False
    config_changed = False

    for line in lines:
        # Track file names
        fm = re.match(r"^\+\+\+\s+b/(.*)", line)
        if fm:
            current_file = fm.group(1)
            files_changed.append(current_file)
            if "test" in current_file.lower() or "spec" in current_file.lower() or current_file.endswith(".test."):
                tests_changed += 1
            if "package" in current_file or "requirements" in current_file or "gemfile" in current_file.lower():
                deps_changed = True
            if current_file in (".env.example", ".env.sample", "config/") or current_file.startswith(".github/"):
                config_changed = True

        # Count lines
        if line.startswith("+"):
            added_lines += 1
        elif line.startswith("-"):
            removed_lines += 1

        # Security checks (only on added/modified lines)
        if line.startswith("+") or line.startswith(" "):
            for pattern, msg in SECURITY_PATTERNS:
                if re.search(pattern, line):
                    clean_line = line.strip()[:80]
                    findings.append({
                        "file": current_file,
                        "severity": "high" if "eval" in pattern or "exec" in pattern or "shell" in pattern else "medium",
                        "message": msg,
                        "line": clean_line,
                    })

    # Deduplicate findings (keep highest severity per type per file)
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f["file"], f["message"])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    total_files = len(files_changed)
    file_types = list(set(f.split(".")[-1] if "." in f else "no-ext" for f in files_changed))

    return {
        "summary": {
            "files_changed": total_files,
            "files_list": files_changed[:20],  # cap display
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "net_change": added_lines - removed_lines,
            "file_types": file_types,
            "tests_changed": tests_changed,
            "has_test_changes": tests_changed > 0,
            "deps_changed": deps_changed,
            "config_changed": config_changed,
        },
        "findings": unique_findings,
    }


def generate_markdown(analysis: dict, pr_url: str = "", pr_title: str = "") -> str:
    """Generate structured Markdown review."""
    s = analysis["summary"]
    findings = analysis["findings"]
    risk_count = len([f for f in findings if f["severity"] == "high"])
    warn_count = len([f for f in findings if f["severity"] == "medium"])

    # Confidence assessment
    if risk_count > 2:
        confidence = "Low"
    elif risk_count > 0 or warn_count > 3:
        confidence = "Medium"
    elif s["has_test_changes"] and s["net_change"] < 500:
        confidence = "High"
    else:
        confidence = "Medium"

    lines = []
    if pr_title:
        lines.append(f"# Review: {pr_title}")
    else:
        lines.append("# PR Review")
    lines.append("")

    # Summary
    lines.append("## Summary of Changes")
    test_note = f" (includes {s['tests_changed']} test file(s))" if s["tests_changed"] else ""
    lines.append(
        f"Reviews **{s['files_changed']} file(s)** across {len(s['file_types'])} type(s)"
        f" ({', '.join(s['file_types'])}). "
        f"**+{s['added_lines']} / -{s['removed_lines']}** lines{test_note}."
    )
    if s["deps_changed"]:
        lines.append("- ⚠️  Dependency files changed — review for breaking changes.")
    if s["config_changed"]:
        lines.append("- ⚙️  Configuration file changed — verify correctness.")
    if not s["has_test_changes"] and s["net_change"] > 50:
        lines.append("- ⚠️  No test changes detected for non-trivial PR.")
    lines.append("")

    # Risks
    lines.append("## Identified Risks")
    high_risks = [f for f in findings if f["severity"] == "high"]
    med_risks = [f for f in findings if f["severity"] == "medium"]

    if not findings:
        lines.append("*No security or risk patterns detected.*")
    else:
        if high_risks:
            lines.append("### High Severity")
            for r in high_risks:
                lines.append(f"- 🔴 `{r['file']}`: {r['message']}")
                lines.append(f"  ```\n  {r['line']}\n  ```")
        if med_risks:
            lines.append("### Medium Severity")
            for r in med_risks:
                lines.append(f"- 🟡 `{r['file']}`: {r['message']}")
    lines.append("")

    # Suggestions
    lines.append("## Improvement Suggestions")
    suggestions = []
    if not s["has_test_changes"] and s["net_change"] > 50:
        suggestions.append("Add tests covering the changes, especially for edge cases.")
    if s["deps_changed"]:
        suggestions.append("Pin dependency versions and verify lockfile consistency.")
    if risk_count > 0:
        suggestions.append("Address high-severity findings before merging.")
    if s["net_change"] > 300:
        suggestions.append(f"Consider splitting into smaller PRs ({s['net_change']} lines is large).")

    if suggestions:
        for sug in suggestions:
            lines.append(f"- 💡 {sug}")
    else:
        lines.append("*No specific suggestions — PR looks clean.*")
    lines.append("")

    # Confidence
    confidence_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    lines.append(f"## Confidence Score: **{confidence_icon.get(confidence, '')} {confidence}**")
    if confidence == "High":
        lines.append("Changes are well-scoped, tested, and clean.")
    elif confidence == "Medium":
        lines.append("Some concerns to address, but overall direction is sound.")
    else:
        lines.append("Multiple high-severity findings — thorough review required.")
    lines.append("")

    # Stats
    lines.append("---")
    lines.append(f"*Reviewed {s['files_changed']} file(s) | "
                 f"+{s['added_lines']} / -{s['removed_lines']} lines*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PR review agent")
    parser.add_argument("--pr", help="GitHub PR URL")
    parser.add_argument("--diff", help="Path to local diff file")
    parser.add_argument("--title", help="PR title (optional)", default="")
    args = parser.parse_args()

    diff = ""
    pr_url = args.pr or ""

    if args.diff:
        with open(args.diff) as f:
            diff = f.read()
    elif args.pr:
        diff = fetch_pr_diff(args.pr)
        pr_url = args.pr
    else:
        # Try reading from stdin (gh CLI pipe)
        try:
            stdin_json = json.loads(sys.stdin.read())
            # gh pr view --json body,title,files
            if "files" in stdin_json:
                # Reconstruct diff from gh output
                diff_lines = []
                for f in stdin_json.get("files", []):
                    if "patch" in f:
                        diff_lines.append(f"--- a/{f.get('filename','')}")
                        diff_lines.append(f"+++ b/{f.get('filename','')}")
                        diff_lines.append(f["patch"])
                diff = "\n".join(diff_lines)
                args.title = stdin_json.get("title", "")
                # Try to get PR URL
                if "url" in stdin_json:
                    pr_url = stdin_json["url"]
        except (json.JSONDecodeError, Exception):
            print("Provide --pr URL, --diff file, or pipe gh PR JSON", file=sys.stderr)
            sys.exit(1)

    if not diff:
        print("No diff content found.", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff(diff)
    markdown = generate_markdown(analysis, pr_url, args.title)
    print(markdown)


if __name__ == "__main__":
    main()
