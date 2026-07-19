#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
       python claude-review.py --diff-file path/to/diff.patch
       python claude-review.py --pr <URL> --claude  # AI-powered review via Claude API
"""

import sys, os, json, argparse, re
from subprocess import check_output, CalledProcessError


def fetch_pr_diff(pr_url):
    """Fetch PR diff via gh CLI or direct curl."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, pr_num = m.groups()

    try:
        diff = check_output(
            ["gh", "pr", "view", pr_num, "--repo", f"{owner}/{repo}", "--json", "body,title,files,additions,deletions"],
            text=True
        )
        pr_data = json.loads(diff)
        files = check_output(
            ["gh", "pr", "diff", pr_num, "--repo", f"{owner}/{repo}"],
            text=True
        )
        return {
            "title": pr_data.get("title", ""),
            "body": pr_data.get("body", ""),
            "files_changed": len(pr_data.get("files", [])),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "diff": files,
            "files_list": [f["path"] for f in pr_data.get("files", [])],
        }
    except (CalledProcessError, FileNotFoundError):
        import urllib.request
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "claude-review-agent"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        diff_url = data.get("diff_url", "")
        req2 = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review-agent"})
        with urllib.request.urlopen(req2) as resp:
            diff_content = resp.read().decode()
        return {
            "title": data.get("title", ""),
            "body": data.get("body", ""),
            "files_changed": data.get("changed_files", 0),
            "additions": data.get("additions", 0),
            "deletions": data.get("deletions", 0),
            "diff": diff_content,
            "files_list": [],
        }


def analyze_diff(pr_info):
    """Analyze the PR diff and produce structured review."""
    diff = pr_info["diff"]
    files_changed = pr_info["files_changed"]
    additions = pr_info.get("additions", 0)
    deletions = pr_info.get("deletions", 0)

    risks = []
    suggestions = []

    # Security patterns
    if re.search(r'(password|secret|api_key|token|credential)\s*[:=]\s*["\'][^"\']{4,}["\']', diff, re.I):
        risks.append("⚠️  **Hardcoded secrets detected** — move to environment variables immediately")

    if re.search(r'(eval|exec|system|popen|subprocess\.call)\s*\(', diff):
        risks.append("⚠️  **Dynamic code execution** — eval/exec/system calls may be injection vectors")

    if re.search(r'(execute\s*\(.*\+|\.format\(.*sql|f["\'].*\bFROM\b|\.execute\s*\(\s*f["\'])', diff, re.I):
        risks.append("⚠️  **Potential SQL injection** — use parameterized queries")

    # Code quality patterns
    if re.search(r'console\.(log|debug|warn|error)', diff) and "test" not in pr_info.get("title", "").lower():
        suggestions.append("💡 Remove `console.log`/`console.debug` statements before merging")

    if re.search(r'\bTODO\b|\bFIXME\b|\bHACK\b|\bXXX\b', diff):
        count = len(re.findall(r'\bTODO\b|\bFIXME\b|\bHACK\b|\bXXX\b', diff))
        suggestions.append(f"💡 {count} TODO/FIXME/HACK/XXX markers found — address or create follow-up issues")

    if re.search(r'\.only\(|\.skip\(|xit\(|xdescribe\(', diff):
        suggestions.append("💡 `.only()` / `.skip()` test modifiers detected — remove before merge")

    if additions > 500:
        risks.append(f"⚠️  **Large PR** ({additions} additions) — consider splitting into smaller, reviewable chunks")

    if deletions > 300:
        risks.append(f"📌 **Large deletion** ({deletions} deletions) — verify no functionality is accidentally removed")

    # Type safety
    if re.search(r':\s*any\b|as\s+any\b|@ts-ignore|@ts-nocheck', diff):
        suggestions.append("💡 TypeScript `any` or `@ts-ignore` found — use proper types")

    # Testing
    has_test_changes = bool(re.search(r'(test|spec|__tests__|\.test\.|\.spec\.)', diff, re.I))
    if not has_test_changes and additions + deletions > 50:
        suggestions.append("💡 No test changes detected — consider adding tests for the modified behavior")

    # File-level checks
    if re.search(r'\.env\b(?!\.example)', diff):
        risks.append("⚠️  **.env file modified** — ensure no secrets are committed")

    if re.search(r'package-lock\.json|yarn\.lock|pnpm-lock\.yaml', diff):
        suggestions.append("💡 Lock file changed — review dependency updates carefully")

    # Confidence
    if len(risks) >= 3:
        confidence = "Low"
    elif len(risks) >= 1:
        confidence = "Medium"
    elif additions > 500:
        confidence = "Medium"
    else:
        confidence = "High"

    return risks, suggestions, confidence


def claude_review(pr_info):
    """Optional: use Claude API for AI-powered review."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    import urllib.request
    prompt = f"""You are a code reviewer. Review this PR diff and return a JSON object with:
- summary (2-3 sentence overview)
- risks (list of strings, each starting with emoji)
- suggestions (list of strings, each starting with emoji)
- confidence (Low/Medium/High)

PR Title: {pr_info.get('title', 'Unknown')}
Files changed: {pr_info['files_changed']}
Additions: {pr_info.get('additions', 0)}
Deletions: {pr_info.get('deletions', 0)}

Diff:
{pr_info['diff'][:12000]}

Return ONLY valid JSON, no other text."""

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            text = result["content"][0]["text"]
            return json.loads(text)
    except Exception:
        return None


def generate_review(pr_info, risks, suggestions, confidence):
    """Generate structured Markdown review."""
    summary_parts = [
        f"This PR modifies {pr_info['files_changed']} file(s)",
        f"with {pr_info['additions']} additions and {pr_info['deletions']} deletions",
    ]
    if pr_info.get("title"):
        summary_parts.insert(0, f"**{pr_info['title']}**")

    lines = [
        "# 🤖 AI Code Review",
        "",
        "## Summary",
        " — ".join(summary_parts) + ".",
    ]

    if risks:
        lines.append("")
        lines.append("## 🚨 Identified Risks")
        for r in risks:
            lines.append(f"- {r}")

    if suggestions:
        lines.append("")
        lines.append("## 💡 Improvement Suggestions")
        for s in suggestions:
            lines.append(f"- {s}")

    if not risks and not suggestions:
        lines.append("")
        lines.append("## ✅ No Issues Found")
        lines.append("No risks or suggestions identified. LGTM! 🚀")

    lines.append("")
    lines.append("---")
    lines.append(f"**Confidence Score: {confidence}** | Files: {pr_info['files_changed']} | +{pr_info['additions']} -{pr_info['deletions']}")
    lines.append("")
    lines.append("*🤖 This review was generated by Claude Code PR Reviewer Agent*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", help="GitHub PR URL")
    parser.add_argument("--diff-file", help="Local diff/patch file")
    parser.add_argument("--claude", action="store_true", help="Use Claude API for AI-powered review")
    args = parser.parse_args()

    if args.pr:
        pr_info = fetch_pr_diff(args.pr)
    elif args.diff_file:
        with open(args.diff_file) as f:
            diff_content = f.read()
        pr_info = {
            "title": "Local diff",
            "body": "",
            "files_changed": len(re.findall(r'^diff --git', diff_content, re.M)),
            "additions": len(re.findall(r'^\+[^+]', diff_content, re.M)),
            "deletions": len(re.findall(r'^-[^-]', diff_content, re.M)),
            "diff": diff_content,
        }
    else:
        print("Usage: python claude-review.py --pr <URL> [--claude]")
        print("       python claude-review.py --diff-file <file>")
        sys.exit(1)

    # Try Claude API if requested
    if args.claude:
        ai_result = claude_review(pr_info)
        if ai_result:
            review = generate_review(
                pr_info,
                ai_result.get("risks", []),
                ai_result.get("suggestions", []),
                ai_result.get("confidence", "Medium"),
            )
            print(review)
            return

    # Fall back to regex-based analysis
    risks, suggestions, confidence = analyze_diff(pr_info)
    review = generate_review(pr_info, risks, suggestions, confidence)
    print(review)


if __name__ == "__main__":
    main()
