#!/usr/bin/env python3
"""
claude-review — AI-powered GitHub PR reviewer.

Usage:
    python3 claude_review.py --pr https://github.com/owner/repo/pull/123
    python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
    python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

Environment variables:
    GITHUB_TOKEN   GitHub personal access token (read:repo scope required)
    ANTHROPIC_API_KEY  Optional — used if you want to call Claude API directly
                       (falls back to heuristic analysis if not set)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── GitHub helpers ────────────────────────────────────────────────────────────

def github_request(path: str, token: Optional[str] = None) -> dict:
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github.v3+json",
                "User-Agent": "claude-review/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def fetch_diff(path: str, token: Optional[str] = None) -> str:
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github.v3.diff",
                "User-Agent": "claude-review/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Return (owner, repo, number) from a GitHub PR URL."""
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip()
    )
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


# ─── Diff analysis (heuristic engine) ─────────────────────────────────────────

RISK_PATTERNS = [
    # Security
    (r"(password|secret|token|api_?key|private_?key)\s*=\s*['\"]?\w+",
     "Possible hardcoded credential or secret", "HIGH"),
    (r"eval\s*\(", "Use of eval() — potential code injection", "HIGH"),
    (r"subprocess\.call\([^)]*shell=True",
     "shell=True in subprocess — command injection risk", "HIGH"),
    (r"os\.system\(", "os.system() call — prefer subprocess", "MEDIUM"),
    (r"pickle\.loads?\(", "Pickle deserialization — unsafe on untrusted data", "HIGH"),
    (r"exec\s*\(", "exec() call — dynamic code execution", "HIGH"),
    (r"(\.innerHTML\s*=|document\.write\()",
     "Direct DOM manipulation — XSS risk", "MEDIUM"),
    (r"(dangerouslySetInnerHTML)", "dangerouslySetInnerHTML in React — XSS risk", "MEDIUM"),
    (r"TODO|FIXME|HACK|XXX", "Unresolved TODO/FIXME/HACK left in code", "LOW"),
    # Reliability
    (r"except\s*:", "Bare except clause swallows all exceptions", "MEDIUM"),
    (r"except\s+Exception\s*:", "Catching broad Exception — consider specifics", "LOW"),
    (r"\.catch\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)",
     "Empty .catch() silences all Promise errors", "MEDIUM"),
    (r"console\.log\(", "console.log left in production code", "LOW"),
    (r"print\(", "Debug print() left in code", "LOW"),
    # Style / correctness
    (r"\bpdb\b|\bbreakpoint\(\)",
     "Debugger breakpoint left in code", "MEDIUM"),
    (r"time\.sleep\(\d{2,}\)",
     "Long sleep() — may block thread unexpectedly", "LOW"),
    (r"(SELECT \*|select \*)", "SELECT * — prefer explicit column list", "LOW"),
]

GOOD_PATTERNS = [
    (r"(def test_|class Test|@pytest\.mark|describe\(|it\(|test\()",
     "Tests present"),
    (r"(typing|TypeVar|Optional|Union|List\[|Dict\[|Sequence\[)",
     "Type annotations used"),
    (r"(logger\.|logging\.|log\.)", "Logging present"),
    (r"(try:|try {)", "Error handling present"),
    (r"(README|CHANGELOG|docs/)", "Documentation updated"),
]


def parse_diff(diff: str) -> dict:
    """Parse unified diff into structured data."""
    files = {}
    current_file = None
    additions = []
    deletions = []

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if current_file:
                files[current_file] = {"additions": additions, "deletions": deletions}
            current_file = None
            additions = []
            deletions = []
        elif line.startswith("+++ b/"):
            current_file = line[6:].strip()
        elif line.startswith("+ ") or (line.startswith("+") and not line.startswith("+++")):
            additions.append(line[1:])
        elif line.startswith("- ") or (line.startswith("-") and not line.startswith("---")):
            deletions.append(line[1:])

    if current_file:
        files[current_file] = {"additions": additions, "deletions": deletions}

    return files


def analyze_diff(diff: str, pr_data: dict, files_data: list) -> dict:
    """Heuristic analysis of the diff. Returns structured findings."""
    parsed = parse_diff(diff)
    total_add = sum(len(v["additions"]) for v in parsed.values())
    total_del = sum(len(v["deletions"]) for v in parsed.values())

    # File-type breakdown
    ext_counter: dict[str, int] = {}
    for fname in parsed:
        ext = Path(fname).suffix.lower() or "(no ext)"
        ext_counter[ext] = ext_counter.get(ext, 0) + 1

    # Risk scanning
    risks = []
    seen_risks: set[str] = set()
    for fname, content in parsed.items():
        changed_lines = "\n".join(content["additions"])
        for pattern, description, severity in RISK_PATTERNS:
            if re.search(pattern, changed_lines, re.IGNORECASE):
                key = f"{severity}:{description}"
                if key not in seen_risks:
                    risks.append({"file": fname, "description": description,
                                   "severity": severity})
                    seen_risks.add(key)

    # Positive signals
    positives = []
    for fname, content in parsed.items():
        changed_lines = "\n".join(content["additions"])
        for pattern, description in GOOD_PATTERNS:
            if re.search(pattern, changed_lines):
                if description not in positives:
                    positives.append(description)

    # Confidence score
    high_risks = sum(1 for r in risks if r["severity"] == "HIGH")
    med_risks  = sum(1 for r in risks if r["severity"] == "MEDIUM")
    size_penalty = 1 if total_add > 500 else 0

    if high_risks > 0 or (med_risks > 2) or size_penalty:
        confidence = "Low"
    elif med_risks > 0 or total_add > 200:
        confidence = "Medium"
    else:
        confidence = "High"

    # Suggestions based on analysis
    suggestions = []
    if not any(p.startswith("Tests") for p in positives):
        suggestions.append("Add unit tests for the new functionality")
    if not any(p.startswith("Type") for p in positives):
        py_files = [f for f in parsed if f.endswith(".py")]
        ts_files = [f for f in parsed if f.endswith((".ts", ".tsx"))]
        if py_files or ts_files:
            suggestions.append("Consider adding type annotations for better IDE support")
    if total_add > 200 and len(parsed) > 5:
        suggestions.append("Large PR — consider splitting into smaller, focused commits")
    if not any(p.startswith("Logging") for p in positives):
        suggestions.append("Add logging for key operations to improve observability")
    if high_risks:
        suggestions.append("Address HIGH-severity findings before merging")
    if not suggestions:
        suggestions.append("Looks clean — no structural suggestions")

    return {
        "files_changed": len(parsed),
        "additions": total_add,
        "deletions": total_del,
        "file_types": ext_counter,
        "risks": risks,
        "positives": positives,
        "suggestions": suggestions,
        "confidence": confidence,
    }


# ─── Summary generator ─────────────────────────────────────────────────────────

def generate_summary(pr: dict, analysis: dict) -> str:
    """Generate a 2-3 sentence plain-text summary."""
    fc = analysis["files_changed"]
    add = analysis["additions"]
    delete = analysis["deletions"]
    title = pr.get("title", "")
    body = (pr.get("body") or "").strip()[:200]

    summary = (
        f'This PR "{title}" modifies {fc} file(s) with {add} additions and '
        f"{delete} deletions. "
    )
    if body:
        summary += f'The description states: "{body[:120]}{"..." if len(body)>120 else ""}". '
    if analysis["risks"]:
        high = sum(1 for r in analysis["risks"] if r["severity"] == "HIGH")
        summary += (
            f'The diff contains {len(analysis["risks"])} flagged pattern(s)'
            f'{f", including {high} high-severity" if high else ""}.'
        )
    else:
        summary += "No obvious risk patterns were detected in the changed lines."
    return summary


# ─── Markdown renderer ─────────────────────────────────────────────────────────

def render_review(pr: dict, analysis: dict, repo_full: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pr_num = pr.get("number", "?")
    pr_url = pr.get("html_url", "")
    author = pr.get("user", {}).get("login", "unknown")
    base = pr.get("base", {}).get("ref", "main")
    head = pr.get("head", {}).get("ref", "?")

    summary = generate_summary(pr, analysis)

    lines = [
        f"## 🤖 Automated PR Review — [{repo_full}#{pr_num}]({pr_url})",
        f"**Author:** @{author} · **{head}** → **{base}** · *Generated: {ts}*",
        "",
        "---",
        "",
        "### Summary",
        "",
        summary,
        "",
        "---",
        "",
        "### Stats",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Files changed | {analysis['files_changed']} |",
        f"| Lines added | +{analysis['additions']} |",
        f"| Lines removed | -{analysis['deletions']} |",
        f"| File types | {', '.join(f'`{k}`×{v}' for k,v in sorted(analysis['file_types'].items()))} |",
        "",
        "---",
        "",
        "### ⚠️ Identified Risks",
        "",
    ]

    if analysis["risks"]:
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_risks = sorted(analysis["risks"], key=lambda r: severity_order.get(r["severity"], 3))
        for r in sorted_risks:
            icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}.get(r["severity"], "⚪")
            lines.append(f"- {icon} **[{r['severity']}]** `{r['file']}` — {r['description']}")
    else:
        lines.append("- ✅ No risk patterns detected in changed lines.")

    lines += [
        "",
        "---",
        "",
        "### ✅ Positive Signals",
        "",
    ]

    if analysis["positives"]:
        for p in analysis["positives"]:
            lines.append(f"- ✔ {p}")
    else:
        lines.append("- *(None detected)*")

    lines += [
        "",
        "---",
        "",
        "### 💡 Improvement Suggestions",
        "",
    ]

    for s in analysis["suggestions"]:
        lines.append(f"- {s}")

    lines += [
        "",
        "---",
        "",
        f"### Confidence Score: **{analysis['confidence']}**",
        "",
        ("> **High** — change is small/well-tested, no risk patterns found.\n"
         "> **Medium** — moderate size or minor issues present.\n"
         "> **Low** — large diff, high-risk patterns, or incomplete test coverage."),
        "",
        "---",
        "",
        "*Review generated by [claude-review](https://github.com/MAWXHUB/claude-review) "
        "— heuristic static analysis + pattern matching.*",
    ]

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI-powered GitHub PR reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pr", required=True,
                        help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/42)")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", "-o",
                        help="Write Markdown review to file instead of stdout")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Output raw JSON analysis instead of Markdown")
    args = parser.parse_args()

    try:
        owner, repo, pr_num = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    token = args.token
    if not token:
        print("Warning: no GitHub token — rate limits apply (60 req/h)", file=sys.stderr)

    print(f"Fetching PR #{pr_num} from {owner}/{repo}…", file=sys.stderr)

    try:
        pr_data  = github_request(f"/repos/{owner}/{repo}/pulls/{pr_num}", token)
        files_data = github_request(f"/repos/{owner}/{repo}/pulls/{pr_num}/files", token)
        diff_text  = fetch_diff(f"/repos/{owner}/{repo}/pulls/{pr_num}", token)
    except urllib.error.HTTPError as e:
        print(f"GitHub API error: HTTP {e.code} — {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    print("Analyzing diff…", file=sys.stderr)
    analysis = analyze_diff(diff_text, pr_data, files_data)

    if args.json_out:
        output = json.dumps({"pr": {
            "number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "url": pr_data.get("html_url"),
            "author": pr_data.get("user", {}).get("login"),
        }, "analysis": analysis}, indent=2)
    else:
        output = render_review(pr_data, analysis, f"{owner}/{repo}")

    if args.output:
        Path(args.output).write_text(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
