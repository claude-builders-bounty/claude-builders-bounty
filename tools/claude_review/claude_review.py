#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")
RISK_WORDS = {
    "auth": "Authentication code changed; reviewers should check permissions and token handling.",
    "password": "Secret or password handling appears in the diff.",
    "token": "Token handling appears in the diff.",
    "payment": "Payment-related code changed.",
    "workflow": "GitHub workflow changes can affect CI or repository automation.",
    "permissions": "Permission-related code changed.",
    "delete": "Delete behavior changed; check data loss paths.",
    "migration": "Migration code changed; check rollback and existing data.",
}


def parse_pr_url(url):
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def request_json(url, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {detail}") from exc


def request_text(url, token):
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub diff request failed: {exc.code} {detail}") from exc


def collect_changed_files(diff):
    files = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3][2:])
    return files


def count_changes(diff):
    added = 0
    removed = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def detect_risks(diff, files):
    text = diff.lower()
    risks = []
    for word, message in RISK_WORDS.items():
        if word in text:
            risks.append(message)

    workflow_files = [path for path in files if path.startswith(".github/workflows/")]
    if workflow_files and "GitHub workflow changes can affect CI or repository automation." not in risks:
        risks.append("GitHub workflow changes can affect CI or repository automation.")

    generated_or_lock = [path for path in files if path.endswith((".lock", "go.sum", "package-lock.json"))]
    if generated_or_lock:
        risks.append("Lockfile or generated dependency data changed; check that it matches the intended dependency update.")

    return list(dict.fromkeys(risks))


def suggestions_for(files, added, removed, risks):
    suggestions = []
    if added + removed > 400:
        suggestions.append("Split the change or call out the highest-risk files in the PR description.")
    if any(path.startswith(".github/workflows/") for path in files):
        suggestions.append("Include one run or screenshot showing the workflow passes on the target branch.")
    if risks:
        suggestions.append("Add a focused test or manual proof for the highest-risk path.")
    if not suggestions:
        suggestions.append("No changes suggested.")
    return suggestions


def confidence(files, added, removed):
    total = added + removed
    if not files or total > 800:
        return "Low"
    if total > 250 or len(files) > 12:
        return "Medium"
    return "High"


def plural(count, word):
    if count == 1:
        return f"1 {word}"
    return f"{count} {word}s"


def review_markdown(pr, diff):
    files = collect_changed_files(diff)
    added, removed = count_changes(diff)
    risks = detect_risks(diff, files)
    suggestions = suggestions_for(files, added, removed, risks)
    conf = confidence(files, added, removed)

    file_word = "file" if len(files) == 1 else "files"
    summary = (
        f"{pr['title']} changes {len(files)} {file_word} with {plural(added, 'added line')} "
        f"and {plural(removed, 'removed line')}. The main touched paths are "
        f"{', '.join(files[:5]) if files else 'not visible from the diff'}."
    )
    if len(files) > 5:
        summary += f" There are {len(files) - 5} more changed files beyond that."

    out = [
        "## Summary",
        "",
        summary,
        "",
        "## Risks",
        "",
    ]
    if risks:
        out.extend(f"- {risk}" for risk in risks)
    else:
        out.append("- None found from the diff.")

    out.extend(["", "## Suggestions", ""])
    out.extend(f"- {item}" for item in suggestions)
    out.extend(["", "## Confidence", "", conf])
    return "\n".join(out)


def build_review(pr_url, token):
    owner, repo, number = parse_pr_url(pr_url)
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    pr = request_json(api_base, token)
    diff = request_text(api_base, token)
    return review_markdown(pr, diff)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--output", help="Write the review to this file")
    args = parser.parse_args(argv)

    try:
        text = build_review(args.pr, os.getenv("GITHUB_TOKEN"))
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
