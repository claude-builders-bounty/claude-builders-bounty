#!/usr/bin/env python3
import argparse
import dataclasses
import re
import subprocess
import sys
import urllib.parse
import urllib.request


@dataclasses.dataclass
class ReviewResult:
    files_changed: int
    added_lines: int
    removed_lines: int
    risks: list[str]
    suggestions: list[str]
    confidence: str


def fetch_pr_diff(pr_url):
    parsed = urllib.parse.urlparse(pr_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, _, number = parts[:4]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    request = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3.diff"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_pr_diff_with_gh(pr_url):
    parsed = urllib.parse.urlparse(pr_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, _, number = parts[:4]
    result = subprocess.run(
        ["gh", "pr", "diff", number, "--repo", f"{owner}/{repo}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh pr diff failed")
    return result.stdout


def changed_files(diff_text):
    return re.findall(r"^diff --git a/(.*?) b/(.*?)$", diff_text, flags=re.M)


def analyze_diff(diff_text):
    files = changed_files(diff_text)
    added = 0
    removed = 0
    added_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
            added_lines.append(line[1:])
        elif line.startswith("-"):
            removed += 1

    joined_added = "\n".join(added_lines)
    risks = []
    suggestions = []

    if re.search(r"shell\s*=\s*True", joined_added):
        risks.append("New subprocess usage with `shell=True` can allow command injection when input is not fully controlled.")
        suggestions.append("Avoid `shell=True`; pass an argument list to `subprocess.run` and validate user-controlled values.")
    if re.search(r"\beval\s*\(", joined_added):
        risks.append("New `eval()` usage can execute arbitrary code.")
        suggestions.append("Replace `eval()` with explicit parsing or a constrained interpreter.")
    if re.search(r"\bconsole\.log\b", joined_added) or re.search(r"print\s*\(", joined_added) and "print(json.dumps(" not in joined_added:
        risks.append("New debug output may leak sensitive data or make logs noisy if left in production paths.")
        suggestions.append("Use structured logging with redaction or remove temporary debug prints before merge.")
    if re.search(r"password|secret|token|api[_-]?key", joined_added, re.I):
        risks.append("Diff touches secret-like names; verify no credentials or tokens are committed.")
        suggestions.append("Move secrets into environment variables and add tests or docs for required configuration.")
    if re.search(r"TODO|FIXME", joined_added):
        risks.append("New TODO/FIXME markers may indicate incomplete behavior.")
        suggestions.append("Resolve TODOs or convert them into tracked issues before merge.")
    if re.search(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", joined_added, re.I):
        risks.append("New SQL delete statement appears to lack a `WHERE` clause.")
        suggestions.append("Add a scoped `WHERE` clause or explicit safeguards around bulk deletes.")

    if not risks:
        risks.append("No high-risk patterns were detected by the static diff scan.")
        suggestions.append("Confirm the changed behavior with targeted tests and review domain-specific edge cases.")

    if added + removed > 400:
        confidence = "Low"
    elif risks and risks[0].startswith("No high-risk"):
        confidence = "Medium"
    else:
        confidence = "High"

    return ReviewResult(
        files_changed=len(files),
        added_lines=added,
        removed_lines=removed,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
    )


def render_review(result, pr_url):
    summary = (
        f"This review scanned `{pr_url}` and found {result.files_changed} changed file(s), "
        f"with {result.added_lines} added line(s) and {result.removed_lines} removed line(s). "
        "The findings below are based on static diff heuristics and should be paired with maintainer domain review."
    )
    risk_lines = "\n".join(f"- {risk}" for risk in result.risks)
    suggestion_lines = "\n".join(f"- {suggestion}" for suggestion in result.suggestions)
    return f"""## Summary

{summary}

## Identified Risks

{risk_lines}

## Improvement Suggestions

{suggestion_lines}

## Confidence

{result.confidence}
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR diff.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--use-gh", action="store_true", help="Use the gh CLI instead of GitHub's diff API")
    args = parser.parse_args(argv)

    diff_text = fetch_pr_diff_with_gh(args.pr) if args.use_gh else fetch_pr_diff(args.pr)
    print(render_review(analyze_diff(diff_text), args.pr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
