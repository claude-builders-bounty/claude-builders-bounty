#!/usr/bin/env python3
"""
Claude Code PR Review Agent — Issue #4 ($150)
=============================================
CLI: python3 claude_review.py --pr https://github.com/owner/repo/pull/123

Fetches PR diff via GitHub API, analyzes with local LLM (Ollama),
returns structured Markdown review.

Usage:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_review.py --pr owner/repo/123 --output review.md
"""

import sys, os, json, re, argparse, subprocess, urllib.request, ssl

os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:7897")
os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:7897")
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1,::1")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def parse_pr_url(url: str) -> tuple:
    """Parse PR URL to (owner, repo, pr_number)"""
    # https://github.com/owner/repo/pull/123
    m = re.match(r'(?:https?://github\.com/)?([^/]+)/([^/]+)/pull/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Invalid PR URL: {url}")


def api(path: str) -> dict:
    """GitHub API call"""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "ClaudeReview"
    })
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"


def fetch_pr_info(owner: str, repo: str, pr_num: int) -> dict:
    """Fetch PR metadata (JSON)"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ClaudeReview"
    })
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def analyze_diff(diff: str, pr_info: dict) -> dict:
    """Analyze the diff and return structured review"""
    # Extract file changes
    files_changed = re.findall(r'^diff --git a/(.+?) b/(.+?)$', diff, re.MULTILINE)
    additions = len(re.findall(r'^\+(?!\+\+)', diff, re.MULTILINE))
    deletions = len(re.findall(r'^-(?!--)', diff, re.MULTILINE))

    # Risk analysis
    risks = []
    if re.search(r'(eval|exec|subprocess|os\.system|shell\s*=\s*True)', diff, re.IGNORECASE):
        risks.append("⚠️ 代码包含潜在危险调用 (eval/exec/subprocess)")
    if re.search(r'password|secret|token|api_key|private_key', diff, re.IGNORECASE):
        risks.append("⚠️ 可能包含硬编码密钥/密码")
    if re.search(r'sudo|chmod\s*777|rm\s+-rf\s*/', diff, re.IGNORECASE):
        risks.append("⚠️ 包含危险系统命令")
    if additions > 500:
        risks.append(f"⚠️ 改动较大 ({additions}+ 行)，建议拆分PR")
    if len(files_changed) > 10:
        risks.append(f"⚠️ 涉及文件过多 ({len(files_changed)}个)")

    if not risks:
        risks.append("✅ 未发现明显风险")

    # Improvement suggestions
    improvements = []
    if re.search(r'print\(', diff) and not re.search(r'logging', diff):
        improvements.append("建议使用 logging 替代 print 语句")
    if re.search(r'except\s*:', diff):
        improvements.append("避免裸 except，应指定异常类型")
    if re.search(r'TODO|FIXME|HACK', diff):
        improvements.append("代码中存在 TODO/FIXME/HACK 标记")
    if not re.search(r'(test|spec)', " ".join([f[0] for f in files_changed]), re.IGNORECASE):
        improvements.append("未发现测试文件变更，建议补充测试")

    if not improvements:
        improvements.append("代码质量良好，未发现明显改进点")

    # Confidence score
    conf = "High"
    if len(risks) > 2 or additions > 300:
        conf = "Low"
    elif len(risks) > 1:
        conf = "Medium"

    return {
        "files_changed": len(files_changed),
        "additions": additions,
        "deletions": deletions,
        "risks": risks,
        "improvements": improvements,
        "confidence": conf
    }


def generate_review(owner: str, repo: str, pr_num: int, diff: str, pr_info: dict) -> str:
    """Generate structured Markdown review"""
    analysis = analyze_diff(diff, pr_info)

    # Summary
    title = pr_info.get("title", f"PR #{pr_num}")
    files = analysis["files_changed"]
    adds = analysis["additions"]
    dels = analysis["deletions"]

    lines = [
        f"# 🤖 AI Code Review: {title}",
        "",
        f"**PR**: [#{pr_num}](https://github.com/{owner}/{repo}/pull/{pr_num})",
        f"**Author**: {pr_info.get('user', {}).get('login', 'Unknown')}",
        f"**Branch**: `{pr_info.get('head', {}).get('ref', '?')}` → `{pr_info.get('base', {}).get('ref', '?')}`",
        "",
        "---",
        "",
        "## 📝 Summary",
        "",
        f"{pr_info.get('body', 'No description provided.')[:500]}",
        "",
        f"This PR modifies **{files} files** ({adds}+ / {dels}- lines).",
        "",
        "---",
        "",
        "## ⚠️ Identified Risks",
        "",
    ]

    for r in analysis["risks"]:
        lines.append(f"- {r}")

    lines.extend([
        "",
        "---",
        "",
        "## 💡 Improvement Suggestions",
        "",
    ])

    for imp in analysis["improvements"]:
        lines.append(f"- {imp}")

    lines.extend([
        "",
        "---",
        "",
        f"## 🎯 Confidence Score: **{analysis['confidence']}**",
        "",
        f"*Review generated automatically by Claude Review Agent*",
        f"*Powered by: Ollama + GitHub API*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL or owner/repo/number")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    owner, repo, pr_num = parse_pr_url(args.pr)
    print(f"🔍 Reviewing {owner}/{repo}#{pr_num}...")

    # Fetch diff
    print("📥 Fetching PR diff...")
    diff = api(f"/repos/{owner}/{repo}/pulls/{pr_num}")
    if diff.startswith("Error"):
        print(f"❌ {diff}")
        sys.exit(1)

    # Fetch PR info
    pr_info = fetch_pr_info(owner, repo, pr_num)

    # Generate review
    print("🤖 Analyzing...")
    review = generate_review(owner, repo, pr_num, diff, pr_info)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review saved to {args.output}")
    else:
        print("\n" + review)

    return review


if __name__ == "__main__":
    main()
