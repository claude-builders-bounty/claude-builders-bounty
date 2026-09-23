#!/usr/bin/env python3
"""PR reviewer: read a GitHub PR, produce a structured Markdown review.

Usage:
    python3 review_pr.py <owner> <repo> <pr_number> [output_file]
    python3 review_pr.py --post [--force] <owner> <repo> <pr_number>

Reads the PR's diff, changed files, and body via the GitHub API
(no auth required for public repos; set GITHUB_TOKEN for private
repos or higher rate limits). Writes a structured Markdown review to
stdout or to output_file.

The review has four sections (per the bounty acceptance criteria):
  - Summary of changes
  - Identified risks (categorised: security / style / performance / follow-up)
  - Improvement suggestions (test / CI / doc gaps, TODOs, style nits)
  - Confidence score: Low / Medium / High

With --post the review is posted as a PR comment instead of printed
(requires GITHUB_TOKEN). Draft PRs are refused unless --force is
given.
"""
import json
import os
import sys
import time
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
VERSION = "1.1"


def headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "pr-review-agent/1.0"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def get_json(url):
    req = urllib.request.Request(url, headers=headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def post_comment(owner, repo, pr_number, body):
    url = f"{API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_pr(owner, repo, number):
    return get_json(f"{API}/repos/{owner}/{repo}/pulls/{number}")


def fetch_files(owner, repo, number, per_page=100):
    files = []
    page = 1
    while True:
        url = (f"{API}/repos/{owner}/{repo}/pulls/{number}/files"
               f"?per_page={per_page}&page={page}")
        data = get_json(url)
        files.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return files


def categorize_line(line):
    """Classify a diff line into a review concern if it looks risky."""
    low = line.lower()
    findings = []
    if any(k in low for k in ("eval(", "exec(", "subprocess.call(", "os.system(")):
        findings.append("security: dynamic code execution")
    is_env_read = any(k in low for k in ("process.env.", "process.env[",
                                         "os.environ", "os.getenv("))
    if any(k in low for k in ("password", "secret", "api_key", "token")) and "=" in low and not is_env_read:
        findings.append("security: possible hardcoded credential")
    if "except:" in low or "catch (e)" in low:
        findings.append("style: bare except / empty catch swallows errors")
    if any(k in low for k in ("console.log(", "print(")):
        findings.append("style: leftover debug output")
    if any(k in low for k in ("while (true", "for (;;)", "while true")):
        findings.append("performance: unbounded loop")
    if any(k in low for k in ("drop table", "truncate", "delete from")) and " where" not in low:
        findings.append("security: destructive SQL without WHERE")
    if "as any" in low:
        findings.append("style: TypeScript any leak")
    if "fixme" in low or "todo" in low:
        findings.append("follow-up: TODO/FIXME marker")
    return findings


TEST_SUFFIXES = (".test.ts", ".test.tsx", ".test.js", ".test.jsx",
                 ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx")
SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx")


def is_test_path(filename):
    """精确判断测试文件：测试命名后缀（.test.ts/.spec.js...）或明确的
    tests/ / test/ / __tests__/ 目录段。
    旧的 `"test" in filename` 子串匹配会把 app/latest.ts、testify.py、
    contest.js 误判成测试文件，吞掉"缺少测试"这条 gap。"""
    fn = filename.lower()
    if fn.endswith(TEST_SUFFIXES):
        return True
    return any(part in ("tests", "test", "__tests__") for part in fn.split("/"))


def calc_confidence(n_files, n_additions, has_security_risk, has_tests):
    """Deterministic Low/Medium/High score for the review's verdict.

    The findings themselves are heuristic (pattern matching on diff
    lines), so the score expresses how much weight to give them:
    security hits or test coverage raise it, very large diffs lower it.
    """
    if n_files > 40 or n_additions > 2000:
        return "Low"
    if has_security_risk or has_tests:
        return "High"
    if n_files <= 15:
        return "Medium"
    return "Low"


def build_review(pr, files):
    """Return a structured Markdown review string."""
    title = pr.get("title", "")
    body = pr.get("body") or ""
    base = pr.get("base", {}).get("ref", "")
    head = pr.get("head", {}).get("ref", "")
    diff = ""
    for f in files:
        # GitHub 对二进制文件不返回 patch（可能缺键或为 null），or "" 防 TypeError
        diff += (f.get("patch") or "") + "\n"

    findings = []
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for tag in categorize_line(line):
                findings.append(tag)

    # De-dup and count
    seen = {}
    for f in findings:
        seen[f] = seen.get(f, 0) + 1
    risks = [(t, c) for t, c in seen.items() if "follow-up" not in t and "style" not in t]
    improvements = [t for t in seen if "follow-up" in t or "style" in t]

    has_tests = any(is_test_path(f["filename"]) for f in files)
    has_ci = any(f["filename"].startswith(".github/workflows/") for f in files)
    has_docs = any(f["filename"].lower().endswith((".md", ".rst")) for f in files)
    confidence = calc_confidence(len(files),
                                 int(pr.get("additions", 0) or 0),
                                 any(t.startswith("security:") for t, _ in risks),
                                 has_tests)

    lines = []
    lines.append("## PR Review")
    lines.append("")
    lines.append(f"**PR:** {title} ({pr.get('html_url','')})")
    lines.append(f"**Branch:** `{head}` → `{base}`  ·  "
                 f"{'draft' if pr.get('draft') else 'ready'}  ·  "
                 f"{pr.get('additions',0):+} / {pr.get('deletions',0):+} lines, "
                 f"{len(files)} files")
    lines.append("")

    lines.append(f"_Generated by pr-reviewer v{VERSION} on {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}_")
    lines.append("")
    lines.append("### Summary of changes")
    if body:
        first_para = body.strip().split("\n\n")[0][:300]
        lines.append(first_para or "(no description)")
    else:
        lines.append(f"Adds/modifies {len(files)} file(s) on `{head}`.")
    lines.append("")

    lines.append("### Identified risks")
    if risks:
        for tag, count in sorted(risks, key=lambda x: -x[1]):
            lines.append(f"- **{tag}** × {count}")
    else:
        lines.append("- No risky patterns detected in the diff.")
    lines.append("")

    lines.append("### Improvement suggestions")
    gaps = []
    if not has_tests:
        gaps.append("No test files changed in this PR — add a unit or integration test for the new behaviour.")
    if not has_ci:
        gaps.append("No CI workflow changed — verify the new code path is covered by existing CI.")
    if not has_docs and any(
        f["filename"].endswith(SOURCE_EXTS) and not is_test_path(f["filename"])
        for f in files
    ):
        gaps.append("No documentation updated — consider a short doc note for public-facing changes.")
    if gaps:
        lines.extend(f"- {g}" for g in gaps)
    if improvements:
        lines.extend(f"- {g}" for g in improvements)
    if not gaps and not improvements:
        lines.append("- Tests, CI, and docs all touched. No obvious gap.")
    lines.append("")

    lines.append("### Confidence score")
    lines.append(f"**{confidence}**")
    lines.append("")
    lines.append("How much weight to give the findings above: **Low** — large or "
                 "sparse diff, treat as a checklist, not a verdict; **Medium** — "
                 "smaller diff with no strong signal either way; **High** — the "
                 "diff is small enough to trust the scan, or it carries test "
                 "coverage / a security hit worth acting on.")
    lines.append("")

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    post = "--post" in args
    force = "--force" in args
    args = [a for a in args if a not in ("--post", "--force")]

    if len(args) < 3:
        print(f"usage: {sys.argv[0]} [--post [--force]] <owner> <repo> "
              f"<pr_number> [output_file]")
        sys.exit(1)

    owner, repo, number = args[0], args[1], args[2]
    out = args[3] if len(args) > 3 else None

    pr = fetch_pr(owner, repo, number)
    files = fetch_files(owner, repo, number)
    review = build_review(pr, files)

    if post:
        if pr.get("draft") and not force:
            print(f"Refusing to post to a draft PR {owner}/{repo}#{number} "
                  f"without --force (see Safety rules in agents/pr-reviewer.md).",
                  file=sys.stderr)
            sys.exit(2)
        url = post_comment(owner, repo, number, review)
        print(f"Posted review: {url['html_url']}")
    elif out:
        with open(out, "w") as f:
            f.write(review + "\n")
        print(f"Wrote {out}")
    else:
        print(review)


if __name__ == "__main__":
    main()
