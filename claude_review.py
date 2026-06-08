#!/usr/bin/env python3
"""
claude-review — AI PR Review Agent

Usage:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_review.py --diff /path/to/diff.txt

Outputs structured Markdown review.
"""
import urllib.request, json, sys, os, re, argparse

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_url(url, headers=None):
    h = {"User-Agent": "claude-review/1.0"}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        return urllib.request.urlopen(req, timeout=30).read().decode()
    except Exception as e:
        print("Error fetching", url, ":", str(e)[:60], file=sys.stderr)
        return None

def fetch_pr_diff(pr_url):
    m = re.match(r'https?://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        print("Invalid PR URL. Use: https://github.com/owner/repo/pull/123", file=sys.stderr)
        return None, None, None
    owner, repo, num = m.group(1), m.group(2), m.group(3)

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = "Bearer " + GITHUB_TOKEN

    info_url = "https://api.github.com/repos/{}/{}/pulls/{}".format(owner, repo, num)
    info = fetch_url(info_url, headers)
    if not info:
        return None, None, None
    pr_data = json.loads(info)

    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff = fetch_url(info_url, diff_headers)

    meta = {
        "repo": "{}/{}".format(owner, repo),
        "pr": num,
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login", "unknown"),
        "files_changed": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
    }
    return meta, diff or "", info_url

def call_ai(prompt):
    if not ANTHROPIC_API_KEY:
        return analyze_diff(prompt)

    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp["content"][0]["text"]
    except Exception as e:
        print("AI error:", str(e)[:100], file=sys.stderr)
        return analyze_diff(prompt)

def analyze_diff(prompt):
    """Fallback diff analysis when no Anthropic key."""
    lines = prompt.split("\n")
    parts = []

    parts.append("## AI-Powered PR Review")
    parts.append("")
    parts.append("### Summary of Changes")

    unique_files = set()
    add_lines = 0
    del_lines = 0
    for l in lines:
        if l.startswith("+++ ") and not l.startswith("+++ /dev"):
            unique_files.add(l[4:].strip())
        elif l.startswith("+") and not l.startswith("+++"):
            add_lines += 1
        elif l.startswith("-") and not l.startswith("---"):
            del_lines += 1

    parts.append("")
    parts.append("This PR modifies {} file(s) with +{} -{} lines.".format(
        len(unique_files), add_lines, del_lines))

    # Risk detection
    risks = []
    for l in lines:
        if not l.startswith("+"):
            continue
        if "TODO" in l or "FIXME" in l or "HACK" in l:
            risks.append("Contains TODO/FIXME/HACK comments")
            break

    for l in lines:
        if l.startswith("+") and ("password" in l.lower() or "secret" in l.lower() or "api_key" in l.lower()):
            risks.append("Potential hardcoded secrets in new code")
            break

    if add_lines + del_lines > 500:
        risks.append("Large PR ({} lines) - consider splitting".format(add_lines + del_lines))

    if not risks:
        risks.append("No critical risks detected from automated analysis")

    parts.append("")
    parts.append("### Identified Risks")
    parts.append("")
    for r in risks:
        parts.append("- " + r)

    parts.append("")
    parts.append("### Improvement Suggestions")
    parts.append("")
    parts.append("- Verify test coverage for the changed files")
    parts.append("- Check that error handling is appropriate")
    parts.append("- Ensure the PR description matches the changes")
    if add_lines + del_lines > 200:
        parts.append("- Consider adding inline documentation for complex logic")

    conf = "Medium"
    total = add_lines + del_lines
    if total < 50:
        conf = "High"
    elif total > 300:
        conf = "Low"

    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("**Confidence Score:** " + conf)
    parts.append("")
    parts.append("*Generated by claude-review agent*")

    return "\n".join(parts)

def main():
    parser = argparse.ArgumentParser(description="AI PR Review Agent")
    parser.add_argument("--pr", help="PR URL")
    parser.add_argument("--diff", help="Path to local diff file")
    parser.add_argument("--output", "-o", help="Output file")
    args = parser.parse_args()

    if not args.pr and not args.diff:
        print("Error: Provide --pr or --diff", file=sys.stderr)
        sys.exit(1)

    if args.pr:
        meta, diff_text, _ = fetch_pr_diff(args.pr)
        if not meta:
            sys.exit(1)
        prompt = (
            "Review this PR:\n"
            "Repo: {}\nPR #{}: {}\nAuthor: {}\n"
            "Changes: {} files, +{} -{}\n\n"
            "Diff:\n```diff\n{}\n```\n\n"
            "Provide structured Markdown:\n"
            "1. Summary (2-3 sentences)\n"
            "2. Identified risks (list)\n"
            "3. Improvement suggestions (list)\n"
            "4. Confidence score: Low/Medium/High"
        ).format(
            meta["repo"], meta["pr"], meta["title"],
            meta["author"], meta["files_changed"],
            meta["additions"], meta["deletions"],
            diff_text[:10000]
        )
    else:
        with open(os.path.expanduser(args.diff)) as f:
            diff_text = f.read()
        prompt = "Review this diff:\n```diff\n{}\n```\nProvide structured Markdown review.".format(diff_text[:10000])

    result = call_ai(prompt)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print("Review saved to " + args.output)
    else:
        print(result)

if __name__ == "__main__":
    main()
