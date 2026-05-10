#!/usr/bin/env python3
from __future__ import annotations

"""
claude-review — Multi-agent PR Review CLI

Usage:
  python claude-review.py --pr <url> [--post] [--json] [--token <TOKEN>]

Examples:
  python claude-review.py --pr https://github.com/psf/requests/pull/7401
  python claude-review.py --pr https://github.com/astral-sh/uv/pull/19322 --json
  python claude-review.py --pr https://github.com/owner/repo/pull/42 --post
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from typing import Any

# ── HTTP setup (httpx + certifi, same as github-issue-solver) ──────────────
try:
    import certifi
    import httpx

    _TRANSPORT = httpx.HTTPTransport(verify=certifi.where())
    _CLIENT = httpx.Client(transport=_TRANSPORT, timeout=30)
except ImportError:
    import urllib.request
    import ssl

    _CLIENT = None  # fallback to urllib


# ── GitHub API helpers ─────────────────────────────────────────────────────

def _api_headers(token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_get(url: str, token: str | None, **kwargs) -> dict:
    headers = _api_headers(token)
    if _CLIENT:
        r = _CLIENT.get(url, headers=headers, **kwargs)
    else:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    r.raise_for_status()
    return r.json()


def _api_post(url: str, token: str, body: dict) -> dict:
    headers = _api_headers(token)
    headers["Content-Type"] = "application/json"
    if _CLIENT:
        r = _CLIENT.post(url, headers=headers, json=body)
    else:
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    r.raise_for_status()
    return r.json()


# ── Parse PR URL ────────────────────────────────────────────────────────────

_PR_URL_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = _PR_URL_RE.match(url)
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return m.group("owner"), m.group("repo"), int(m.group("number"))


# ── Fetch PR data ──────────────────────────────────────────────────────────

def fetch_pr(owner: str, repo: str, number: int, token: str | None) -> dict:
    """Fetch PR metadata + diff."""
    base = f"https://api.github.com/repos/{owner}/{repo}"

    # PR metadata
    pr = _api_get(f"{base}/pulls/{number}", token)

    # Changed files (paginated)
    files = []
    page = 1
    while True:
        batch = _api_get(
            f"{base}/pulls/{number}/files",
            token,
            params={"per_page": 100, "page": page},
        )
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    # Full diff
    headers = _api_headers(token)
    if _CLIENT:
        headers["Accept"] = "application/vnd.github.v3.diff"
        r = _CLIENT.get(f"{base}/pulls/{number}", headers=headers)
        diff = r.text
    else:
        req = urllib.request.Request(f"{base}/pulls/{number}", headers=headers)
        with urllib.request.urlopen(req) as resp:
            diff = resp.read().decode()

    return {"pr": pr, "files": files, "diff": diff}


# ── Heuristic analysis (no AI key needed) ─────────────────────────────────

_SEC_PATTERNS: list[tuple[str, str, str]] = [
    # (severity, label, regex_pattern)
    ("CRITICAL", "Hardcoded credential", r'(?:api_key|password|secret|token)\s*=\s*["\'][^"\']{8,}["\']'),
    ("CRITICAL", "Private key", r"BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY"),
    ("CRITICAL", "AWS key", r"AKIA[0-9A-Z]{16}"),
    ("HIGH", "Code injection", r"\b(?:eval|exec|compile)\s*\("),
    ("HIGH", "Shell injection", r"shell\s*=\s*True"),
    ("HIGH", "SQL injection", r'(?:SELECT|INSERT|UPDATE|DELETE).*[f"]\s*(?:WHERE|VALUES).*\{'),
    ("HIGH", "Dangerous HTML", r"dangerouslySetInnerHTML|innerHTML\s*="),
    ("MEDIUM", "Missing rate limit", r"@(?:app|router)\.(?:route|get|post|put|delete)\("),
    ("MEDIUM", "Insecure temp file", r"\bmktemp\b"),
    ("LOW", "Debug print", r"\bprint\s*\(|console\.log\s*\("),
]

_QUALITY_PATTERNS: list[tuple[str, str, str]] = [
    ("HIGH", "Bare exception", r"except\s*:"),
    ("HIGH", "Swallowed exception", r"except\s+\w+.*:\s*pass"),
    ("MEDIUM", "Large function", r"^def \w+\(.*\):",),  # needs line-count check
    ("MEDIUM", "TODO/FIXME", r"\b(?:TODO|FIXME|HACK|XXX)\b"),
    ("LOW", "Missing docstring", r"^def \w+\(.*\):\s*$"),
]


def _heuristic_security(diff: str) -> list[dict]:
    findings = []
    for severity, label, pattern in _SEC_PATTERNS:
        for m in re.finditer(pattern, diff, re.IGNORECASE | re.MULTILINE):
            # Get surrounding line
            start = max(0, m.start() - 60)
            end = min(len(diff), m.end() + 60)
            snippet = diff[start:end].replace("\n", " ").strip()
            findings.append({"severity": severity, "type": label, "snippet": snippet})
    return findings


def _heuristic_quality(files: list[dict], diff: str) -> list[dict]:
    findings = []

    # No test files?
    has_tests = any(
        "test" in f.get("filename", "").lower() or "spec" in f.get("filename", "").lower()
        for f in files
    )
    src_files = [
        f for f in files
        if not any(
            x in f.get("filename", "").lower()
            for x in ("test", "spec", "docs", "changelog", ".md")
        )
    ]
    if src_files and not has_tests:
        findings.append({
            "severity": "HIGH",
            "type": "Missing tests",
            "detail": f"PR changes {len(src_files)} source file(s) but adds no tests",
        })

    # Large diff
    total_add = sum(f.get("additions", 0) for f in files)
    total_del = sum(f.get("deletions", 0) for f in files)
    delta = total_add + total_del
    if delta > 1500:
        findings.append({
            "severity": "MEDIUM",
            "type": "Large diff",
            "detail": f"PR has {delta} lines changed (>{1500}), hard to review thoroughly",
        })
    elif delta > 500:
        findings.append({
            "severity": "LOW",
            "type": "Medium diff",
            "detail": f"PR has {delta} lines changed, consider splitting",
        })

    # Pattern-based
    for severity, label, pattern in _QUALITY_PATTERNS:
        for m in re.finditer(pattern, diff, re.MULTILINE):
            start = max(0, m.start() - 40)
            end = min(len(diff), m.end() + 40)
            snippet = diff[start:end].replace("\n", " ").strip()
            findings.append({"severity": severity, "type": label, "snippet": snippet})

    # Empty PR description
    return findings


# ── Confidence score ───────────────────────────────────────────────────────

def compute_confidence(
    pr: dict,
    security_findings: list[dict],
    quality_findings: list[dict],
) -> dict:
    score = 0.85

    # Size penalty
    delta = pr.get("additions", 0) + pr.get("deletions", 0)
    if delta > 1500:
        score -= 0.45
    elif delta > 500:
        score -= 0.25
    elif delta > 150:
        score -= 0.10

    # Security deductions
    critical = sum(1 for f in security_findings if f.get("severity") == "CRITICAL")
    high = sum(1 for f in security_findings if f.get("severity") == "HIGH")
    score -= 0.25 * min(critical, 3)
    score -= 0.10 * min(high, 4)

    # Quality deductions
    q_high = sum(1 for f in quality_findings if f.get("severity") == "HIGH")
    score -= 0.10 * min(q_high, 3)

    # Empty description
    if not pr.get("body", "").strip():
        score -= 0.10

    # Clamp
    score = max(0.05, min(0.95, score))

    label = "High" if score >= 0.70 else ("Medium" if score >= 0.40 else "Low")

    return {"score": round(score, 2), "label": label}


# ── Markdown report builder ────────────────────────────────────────────────

def _severity_emoji(s: str) -> str:
    return {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🟡", "LOW": "🔵"}.get(s, "•")


def build_report(
    pr: dict,
    security: list[dict],
    quality: list[dict],
    confidence: dict,
    json_mode: bool = False,
) -> str:
    if json_mode:
        return json.dumps({
            "pr": pr["number"],
            "title": pr.get("title", ""),
            "author": pr.get("user", {}).get("login", ""),
            "security_findings": security,
            "quality_findings": quality,
            "confidence": confidence,
            "generated": datetime.now(timezone.utc).isoformat(),
        }, indent=2, ensure_ascii=False)

    lines = []
    lines.append("<!-- open-reviewer:do-not-remove -->")
    lines.append("## 🤖 Claude Review\n")
    lines.append(f"**PR:** #{pr['number']} — {pr.get('title', '')}")
    lines.append(f"**Author:** @{pr.get('user', {}).get('login', 'unknown')}")
    lines.append(
        f"**Reviewers:** security-reviewer + code-quality-reviewer"
    )
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Summary
    lines.append("### Summary\n")
    delta = pr.get("additions", 0) + pr.get("deletions", 0)
    changed = pr.get("changed_files", 0)
    lines.append(
        f"This PR changes **{changed} file(s)** with **{delta} lines** modified "
        f"(+{pr.get('additions', 0)}/-{pr.get('deletions', 0)}).\n"
    )

    # Security
    lines.append("### Security Analysis ⚠️\n")
    if security:
        by_sev = {}
        for f in security:
            by_sev.setdefault(f["severity"], []).append(f)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            items = by_sev.get(sev, [])
            if not items:
                continue
            lines.append(f"**{sev}** ({len(items)}):\n")
            for item in items:
                detail = item.get("snippet") or item.get("detail", "")
                lines.append(f"- {_severity_emoji(sev)} **{item['type']}**: `{detail[:100]}`")
            lines.append("")
    else:
        lines.append("✅ No security issues detected by heuristic scan.\n")

    # Quality
    lines.append("### Code Quality Analysis 📋\n")
    if quality:
        by_sev = {}
        for f in quality:
            by_sev.setdefault(f["severity"], []).append(f)
        for sev in ("HIGH", "MEDIUM", "LOW"):
            items = by_sev.get(sev, [])
            if not items:
                continue
            lines.append(f"**{sev}** ({len(items)}):\n")
            for item in items:
                detail = item.get("snippet") or item.get("detail", "")
                lines.append(f"- {_severity_emoji(sev)} **{item['type']}**: `{detail[:100]}`")
            lines.append("")
    else:
        lines.append("✅ No quality issues detected by heuristic scan.\n")

    # Combined risks
    lines.append("### Combined Risks\n")
    all_findings = security + quality
    all_findings.sort(key=lambda f: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(f.get("severity", "LOW"), 99))
    if all_findings:
        for f in all_findings[:10]:  # Top 10
            sev = f.get("severity", "LOW")
            lines.append(f"- {_severity_emoji(sev)} **{sev}**: {f.get('type', 'unknown')}")
    else:
        lines.append("✅ No significant risks identified.")
    lines.append("")

    # Suggestions
    lines.append("### Improvement Suggestions\n")
    suggestions = []
    if any(f.get("severity") == "CRITICAL" for f in security):
        suggestions.append("- 🚨 **Fix critical security issues before merging** — hardcoded credentials or keys must be rotated immediately")
    if any(f.get("type") == "Missing tests" for f in quality):
        suggestions.append("- 🧪 **Add tests** — PR changes source code without corresponding test coverage")
    if delta > 1500:
        suggestions.append("- ✂️ **Split the PR** — large diffs are hard to review; consider breaking into focused changes")
    if not pr.get("body", "").strip():
        suggestions.append("- 📝 **Add a PR description** — explain what this change does and why")
    if not suggestions:
        suggestions.append("- ✅ PR looks good from a heuristic standpoint — consider a deeper AI review for complex logic")
    lines.extend(suggestions)
    lines.append("")

    # Confidence
    lines.append("### Confidence Score\n")
    lines.append(f"**{confidence['score']}** — **{confidence['label']}**\n")
    lines.append(
        f"| Factor | Impact |\n|---|---|\n"
        f"| Base | 0.85 |\n"
        f"| Size penalty | {delta} lines |\n"
        f"| Security findings | {len(security)} |\n"
        f"| Quality findings | {len(quality)} |\n"
        f"| **Final** | **{confidence['score']} ({confidence['label']})** |\n"
    )

    return "\n".join(lines)


# ── Post comment ────────────────────────────────────────────────────────────

def post_comment(owner: str, repo: str, number: int, token: str, body: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    _api_post(url, token, {"body": body})
    print(f"✅ Review posted as comment on #{number}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent PR Review — open-reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              claude-review --pr https://github.com/psf/requests/pull/7401
              claude-review --pr https://github.com/owner/repo/pull/42 --json
              claude-review --pr https://github.com/owner/repo/pull/42 --post
        """),
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of Markdown")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub token (or set GITHUB_TOKEN env)",
    )
    args = parser.parse_args()

    # Parse URL
    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching PR #{number} from {owner}/{repo}...")

    # Fetch PR data
    data = fetch_pr(owner, repo, number, args.token or None)
    pr = data["pr"]
    files = data["files"]
    diff = data["diff"]

    print(f"  → {pr.get('title', '')}")
    print(f"  → {len(files)} file(s) changed, {pr.get('additions', 0)}+/{pr.get('deletions', 0)}-")

    # Run heuristic analysis
    print("\n🛡️  Running security analysis...")
    security = _heuristic_security(diff)
    print(f"  → {len(security)} finding(s)")

    print("📋 Running quality analysis...")
    quality = _heuristic_quality(files, diff)
    print(f"  → {len(quality)} finding(s)")

    # Compute confidence
    confidence = compute_confidence(pr, security, quality)
    print(f"\n🎯 Confidence: {confidence['score']} ({confidence['label']})")

    # Build report
    report = build_report(pr, security, quality, confidence, json_mode=args.json)

    if args.json:
        print("\n" + report)
    else:
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

    # Post if requested
    if args.post:
        if not args.token:
            print("❌ --post requires --token or GITHUB_TOKEN env", file=sys.stderr)
            sys.exit(1)
        post_comment(owner, repo, number, args.token, report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
