#!/usr/bin/env python3
"""claude-review — Structured PR review agent.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr owner/repo#123
    python claude_review.py --repo owner/repo --number 123

Requires GITHUB_TOKEN env var.
"""
import argparse, json, os, sys, urllib.request, urllib.parse, re
from datetime import datetime

TOKEN = os.environ.get("GITHUB_TOKEN", "")

def gh(method, path, data=None, accept=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", accept or "application/vnd.github+json")
    req.add_header("User-Agent", "claude-review")
    if data: req.add_header("Content-Type", "application/json")
    try:
        return urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        return e.read() if e.fp else b""

def gh_json(method, path, data=None):
    raw = gh(method, path, data)
    return json.loads(raw.decode()) if raw else {}

def parse_pr_arg(s):
    """Extract owner/repo and PR number from various formats."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", s)
    if m: return m.group(1), m.group(2), int(m.group(3))
    m = re.search(r"([\w.-]+)/([\w.-]+)#(\d+)", s)
    if m: return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Cannot parse PR: {s}")

def fetch_pr(owner, repo, number):
    pr = gh_json("GET", f"/repos/{owner}/{repo}/pulls/{number}")
    files = gh_json("GET", f"/repos/{owner}/{repo}/pulls/{number}/files")
    return pr, files

def analyze_changes(pr, files):
    """Analyze PR content — returns summary, risks, suggestions, confidence."""
    # Basic stats
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    changed = len(files)
    # Detect language from file extensions
    exts = {}
    for f in files:
        e = os.path.splitext(f.get("filename", ""))[1].lower() or "(none)"
        exts[e] = exts.get(e, 0) + 1
    primary_lang = max(exts, key=exts.get) if exts else "unknown"
    # Look for risky patterns in patch
    risky_patterns = {
        "hardcoded-secret": r"(api[_-]?key|secret|token|password|auth)\s*=\s*['\"][\w\-]{16,}['\"]",
        "eval-or-exec": r"\b(eval|exec|subprocess\.call|os\.system|shell=True)\b",
        "unbounded-loop": r"while\s+True\s*:",
        "db-no-transaction": r"(INSERT|UPDATE|DELETE)[^;]*;\s*(INSERT|UPDATE|DELETE)[^;]*;\s*(INSERT|UPDATE|DELETE)",
        "catch-all-except": r"except\s*:",
        "no-input-validation": r"request\.(args|form|json)\b",
        "TODO-FIXME": r"\b(TODO|FIXME|HACK|XXX)\b",
        "force-push": r"force\s*=\s*True|\-\-force",
        "debug-code": r"console\.log|print\(|debugger;",
        "unchecked-error": r"except\s+Exception\s*:\s*\n\s*pass",
    }
    found_risks = []
    for f in files:
        patch = f.get("patch", "") or ""
        fname = f.get("filename", "?")
        for label, pat in risky_patterns.items():
            if re.search(pat, patch, re.MULTILINE):
                found_risks.append((fname, label))
    # File-type suggestions
    suggestions = []
    # Large PR warning
    if additions + deletions > 500:
        suggestions.append("PR exceeds 500 lines — consider splitting into smaller PRs for easier review")
    if changed > 15:
        suggestions.append("PR touches >15 files — consider grouping by feature")
    # New file without tests
    for f in files:
        fn = f.get("filename", "")
        if fn.endswith(".py") and "test" not in fn.lower():
            # Check if there's a corresponding test file
            has_test = any("test" in g.get("filename", "").lower() for g in files)
            if not has_test and f.get("status") == "added":
                suggestions.append(f"New file `{fn}` has no tests — add coverage before merge")
                break
    # Security suggestions
    filenames = [f.get("filename", "") for f in files]
    if any("password" in fn.lower() or "secret" in fn.lower() or ".env" in fn.lower() for fn in filenames):
        suggestions.append("Credentials or env files in the diff — double-check nothing sensitive is committed")
    # Confidence scoring
    if len(found_risks) >= 3:
        confidence = "Low"
    elif len(found_risks) >= 1 or additions + deletions > 300:
        confidence = "Medium"
    else:
        confidence = "High"
    return {
        "additions": additions, "deletions": deletions, "changed_files": changed,
        "primary_lang": primary_lang, "ext_distribution": exts,
        "risks": found_risks, "suggestions": suggestions,
        "confidence": confidence,
    }

def format_review(pr, analysis):
    author = pr.get("user", {}).get("login", "?")
    title = pr.get("title", "")
    # Summary
    summary = f"{author} 提交了 *{title}*。本次变更涉及 **{analysis['changed_files']} 个文件** (+{analysis['additions']}/-{analysis['deletions']})，主要语言 {analysis['primary_lang']}。"
    if analysis.get("ext_distribution"):
        parts = ", ".join(f"{e} ×{n}" for e, n in analysis["ext_distribution"].items())
        summary += f" 文件分布: {parts}。"
    # Risks section
    if analysis["risks"]:
        risk_lines = []
        for fname, label in analysis["risks"]:
            risk_lines.append(f"- ⚠️ **{label}** found in `{fname}`")
        risks_md = "\n".join(risk_lines)
    else:
        risks_md = "- ✅ 未发现明显风险模式"
    # Suggestions
    if analysis["suggestions"]:
        sug_md = "\n".join(f"- 💡 {s}" for s in analysis["suggestions"])
    else:
        sug_md = "- ✅ 无特别建议"
    # Confidence badge
    badges = {"High": "🟢 High", "Medium": "🟡 Medium", "Low": "🔴 Low"}
    conf = badges.get(analysis["confidence"], analysis["confidence"])
    md = f"""## Claude Code PR Review Agent

> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Confidence: **{conf}**

### Summary (2–3 sentences)

{summary}

### Identified Risks

{risks_md}

### Improvement Suggestions

{sug_md}

### Confidence: **{conf}**

---
*This review was auto-generated by claude-review agent. Always supplement with your own judgment.*
"""
    return md

def main():
    ap = argparse.ArgumentParser(description="Structured PR review agent")
    ap.add_argument("--pr", help="GitHub PR URL or owner/repo#number")
    ap.add_argument("--repo", help="owner/repo")
    ap.add_argument("--number", type=int, help="PR number")
    ap.add_argument("--output", default="-", help="Output file (default: stdout)")
    ap.add_argument("--post", action="store_true", help="Post review as PR comment (not yet supported)")
    args = ap.parse_args()
    if not TOKEN:
        print("❌ GITHUB_TOKEN not set", file=sys.stderr); sys.exit(1)
    if args.pr:
        owner, repo, number = parse_pr_arg(args.pr)
    elif args.repo and args.number:
        owner, repo = args.repo.split("/")
        number = args.number
    else:
        ap.print_help(); sys.exit(1)
    print(f"🔍 Fetching {owner}/{repo}#{number}...")
    pr, files = fetch_pr(owner, repo, number)
    if not pr or "number" not in pr:
        print(f"❌ Cannot fetch PR: {pr}", file=sys.stderr); sys.exit(1)
    print(f"  {pr.get('title')} — {len(files)} files")
    analysis = analyze_changes(pr, files)
    review_md = format_review(pr, analysis)
    if args.output == "-":
        print(review_md)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_md)
        print(f"✅ Wrote review → {args.output}")
    # Post comment if requested
    if args.post:
        r = gh_json("POST", f"/repos/{owner}/{repo}/issues/{number}/comments", {"body": review_md})
        if "id" in r:
            print(f"✅ Posted review comment")
        else:
            print(f"⚠️ Post failed: {r}")

if __name__ == "__main__":
    main()
