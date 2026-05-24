#!/usr/bin/env python3
"""
claude-review.py — PR Review Agent (Bounty #4, $150)
CLI tool that analyzes GitHub PR diffs and produces structured code reviews.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ============ GitHub API ============

def gh_request(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-agent")
    if data:
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, json.dumps(data).encode(), timeout=30)
    else:
        resp = urllib.request.urlopen(req, timeout=30)
    return resp

def parse_pr_url(pr_url):
    """Parse a GitHub PR URL into owner/repo/pull_number."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    return m.group(1), m.group(2), int(m.group(3))

def fetch_pr_diff(owner, repo, pr_num):
    """Fetch the unified diff for a PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    resp = gh_request("GET", url)
    body = resp.read().decode("utf-8", errors="replace")
    return body

def fetch_pr_metadata(owner, repo, pr_num):
    """Fetch PR metadata (title, description, files changed)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "claude-review-agent")
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    return {
        "title": data.get("title", ""),
        "body": data.get("body", "") or "",
        "author": data.get("user", {}).get("login", "unknown"),
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
        "changed_files": data.get("changed_files", 0),
        "state": data.get("state", ""),
    }


# ============ Diff Parser ============

def parse_diff(diff_text):
    """Parse unified diff into structured hunks per file."""
    files = []
    current_file = None
    current_hunk = None

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files.append(current_file)
            path = re.search(r" b/(.+)", line)
            current_file = {
                "path": path.group(1) if path else "unknown",
                "hunks": [],
                "additions": 0,
                "deletions": 0,
            }
        elif line.startswith("@@") and current_file:
            current_hunk = {
                "header": line,
                "lines": [],
                "adds": 0,
                "dels": 0,
            }
            current_file["hunks"].append(current_hunk)
        elif current_file and current_hunk:
            if line.startswith("+"):
                current_hunk["lines"].append(("add", line[1:]))
                current_hunk["adds"] += 1
                current_file["additions"] += 1
            elif line.startswith("-"):
                current_hunk["lines"].append(("del", line[1:]))
                current_hunk["dels"] += 1
                current_file["deletions"] += 1
            elif line.startswith(" "):
                current_hunk["lines"].append(("ctx", line[1:]))

    if current_file:
        files.append(current_file)

    return files


# ============ Review Engine ============

class ReviewEngine:
    """Rule-based PR review engine. No external AI API needed."""

    def __init__(self):
        self.risk_patterns = [
            ("hardcoded_secret", r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded credential detected"),
            ("sql_injection", r"(?i)execute\s*\(\s*['\"]\s*(SELECT|INSERT|UPDATE|DELETE)", "Raw SQL execution — potential injection risk"),
            ("eval_usage", r"(?i)\b(eval|exec)\s*\(", "Use of eval/exec — security risk"),
            ("print_debug", r"(?i)(console\.log|printf|print)\s*\(.*(?:debug|test|temp|fix)", "Debug print left in code"),
            ("todo_left", r"(?i)(TODO|FIXME|HACK|XXX)\s*:", "Unresolved TODO/FIXME"),
            ("insecure_http", r"http://[^s]", "Insecure HTTP URL detected"),
            ("infinite_loop", r"(?i)(while\s*True|while\s*\(true\))", "Potential infinite loop — ensure break condition"),
            ("exception_swallow", r"except\s*:\s*\n\s*(?:pass|#|''')", "Bare except without handling — swallows errors"),
            ("large_file", None, "Large file — consider splitting into modules", 300),
            ("no_error_handling", r"(?i)def\s+\w+\([^)]*\)\s*:\s*\n(?:[^#\n]*\n)*?(?=\S)", "Function lacks error handling — add try/except"),
        ]

        self.improvement_patterns = [
            ("type_hint_missing", r"def\s+\w+\([^)]*\)\s*->", "Good: has type hints"),
            ("type_hint", r"def\s+\w+\([^)]*\)\s*:", "Add return type annotation"),
            ("docstring_missing", r'def\s+\w+\([^)]*\):\s*\n\s+(?!""")', "Missing docstring"),
            ("magic_number", r"(?<!\w)(?:100|3600|86400|65535|1024|2048|4096|8192)(?!\w)", "Magic number — extract to named constant"),
            ("long_line", None, "Line too long (>100 chars)", 100),
            ("broad_import", r"(?i)from\s+\w+\s+import\s+\*", "Wildcard import — import only what's needed"),
        ]

    def _count_lines(self, diff_files):
        total = sum(f["additions"] + f["deletions"] for f in diff_files)
        return total

    def _get_added_lines(self, diff_files):
        """Get all added lines across all files."""
        lines = []
        for f in diff_files:
            for h in f["hunks"]:
                for kind, text in h["lines"]:
                    if kind == "add":
                        lines.append((f["path"], text))
        return lines

    def review(self, diff_text, metadata):
        """Run full review. Returns structured result."""
        files = parse_diff(diff_text)
        total_lines = self._count_lines(files)
        added_lines = self._get_added_lines(files)

        risks = []
        improvements = []
        scores = {"risks": 0, "improvements": 0}

        # --- Risk scanning ---
        for pattern_id, pattern, desc, *extra in self.risk_patterns:
            max_lines = extra[0] if extra else None
            if pattern is None and max_lines:
                # Size-based check
                for f in files:
                    if f["additions"] > max_lines:
                        risks.append({
                            "file": f["path"],
                            "severity": "medium",
                            "finding": f"File has {f['additions']} additions (>{max_lines}) — consider splitting",
                            "line": 1,
                        })
                        scores["risks"] += 1
            elif pattern:
                for f in files:
                    for h in f["hunks"]:
                        for kind, text in h["lines"]:
                            if kind == "add" and re.search(pattern, text):
                                risks.append({
                                    "file": f["path"],
                                    "severity": "high" if "secret" in pattern_id or "sql" in pattern_id else "medium",
                                    "finding": desc,
                                    "line": 1,
                                })
                                scores["risks"] += 1
                                break

        # --- Improvement scanning ---
        for pattern_id, pattern, desc, *extra in self.improvement_patterns:
            max_len = extra[0] if extra else None
            if pattern is None and max_len:
                for f in files:
                    for h in f["hunks"]:
                        for kind, text in h["lines"]:
                            if kind == "add" and len(text) > max_len:
                                improvements.append({
                                    "file": f["path"],
                                    "type": "style",
                                    "suggestion": f"Line too long ({len(text)} chars) — break into multiple lines",
                                })
                                scores["improvements"] += 1
            elif pattern:
                for f in files:
                    file_text = ""
                    for h in f["hunks"]:
                        for kind, text in h["lines"]:
                            if kind == "add":
                                file_text += text + "\n"
                    m = re.search(pattern, file_text)
                    if m:
                        improvements.append({
                            "file": f["path"],
                            "type": "quality",
                            "suggestion": desc,
                        })
                        scores["improvements"] += 1

        # --- Summary ---
        total = metadata["changed_files"]
        adds = metadata["additions"]
        dels = metadata["deletions"]

        summary_parts = []
        summary_parts.append(f"This PR modifies **{total} file(s)** with **+{adds}/-{dels}** lines.")
        if risks:
            summary_parts.append(f"Found **{len(risks)} risk(s)** and **{len(improvements)} improvement opportunity(ies)**.")
        else:
            summary_parts.append("No critical risks detected.")

        # --- Confidence ---
        risk_count = len(risks)
        file_count = total
        if file_count == 0:
            confidence = "Low — empty diff?"
        elif risk_count >= 3:
            confidence = "High — significant issues found"
        elif risk_count >= 1:
            confidence = "Medium — minor issues detected"
        else:
            confidence = "High — no issues found"

        return {
            "summary": " ".join(summary_parts),
            "risks": risks,
            "improvements": improvements,
            "confidence": confidence,
        }


# ============ Output Formatter ============

def format_markdown(review, metadata, pr_url):
    """Format review as structured Markdown."""
    lines = []
    lines.append(f"# 🔍 PR Review: {metadata['title']}")
    lines.append("")
    lines.append(f"**PR**: [{pr_url}]({pr_url})")
    lines.append(f"**Author**: @{metadata['author']}")
    lines.append(f"**Changed**: +{metadata['additions']}/-{metadata['deletions']} across {metadata['changed_files']} files")
    lines.append("")

    # Summary
    lines.append("## 📝 Summary of Changes")
    lines.append("")
    lines.append(review["summary"])
    lines.append("")

    # Risks
    lines.append("## ⚠️ Identified Risks")
    lines.append("")
    if review["risks"]:
        for r in review["risks"]:
            emoji = "🔴" if r["severity"] == "high" else "🟡"
            lines.append(f"- {emoji} **{r['finding']}** (in `{r['file']}`)")
        lines.append("")
    else:
        lines.append("_No risks detected._")
        lines.append("")

    # Improvements
    lines.append("## 💡 Improvement Suggestions")
    lines.append("")
    if review["improvements"]:
        for imp in review["improvements"]:
            lines.append(f"- 💭 **{imp['suggestion']}** (in `{imp['file']}`)")
        lines.append("")
    else:
        lines.append("_No improvement suggestions._")
        lines.append("")

    # Score
    risk_count = len(review["risks"])
    imp_count = len(review["improvements"])
    if risk_count == 0 and imp_count == 0:
        overall = "✅ Looks good!"
    elif risk_count <= 1:
        overall = "🟢 Minor improvements needed"
    elif risk_count <= 3:
        overall = "🟡 Some issues to address"
    else:
        overall = "🔴 Significant concerns"

    lines.append("## 📊 Review Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Risks Found | {risk_count} |")
    lines.append(f"| Improvements | {imp_count} |")
    lines.append(f"| Confidence | {review['confidence']} |")
    lines.append(f"| Overall | {overall} |")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"_Auto-generated review by [claude-review](https://github.com/Youan-ai/claude-builders-bounty) | {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")

    return "\n".join(lines)


# ============ Sample Preview Mode ============

def generate_sample_outputs(output_dir):
    """Generate 2 sample PR review outputs for demonstration."""
    samples_dir = os.path.join(output_dir, "sample-outputs")
    os.makedirs(samples_dir, exist_ok=True)

    # Sample 1: Medium-size feature PR
    sample1_diff = """diff --git a/src/features/export/export-csv.ts b/src/features/export/export-csv.ts
index abc123..def456 100644
--- a/src/features/export/export-csv.ts
+++ b/src/features/export/export-csv.ts
@@ -1,5 +1,34 @@
+import { db } from '@/lib/db';
+import { writeFileSync, existsSync } from 'fs';
+
+export async function exportUserData(userId: string) {
+  const users = await db.execute('SELECT * FROM users WHERE id = ' + userId);
+  const apiKey = 'sk-1234567890abcdef';
+  console.log('debug: export started');
+  // TODO: add pagination for large datasets
+
+  const csv = users.map(u => `${u.name},${u.email}`).join('\\n');
+  writeFileSync('/tmp/export.csv', csv);
+  return { success: true };
+}
+"""

    sample1_meta = {
        "title": "Add CSV export feature for user data",
        "author": "developer-1",
        "additions": 29,
        "deletions": 0,
        "changed_files": 1,
        "state": "open",
    }

    engine = ReviewEngine()
    r1 = engine.review(sample1_diff, sample1_meta)
    out1 = format_markdown(r1, sample1_meta, "https://github.com/example/example-repo/pull/42")

    with open(os.path.join(samples_dir, "pr_42_review.md"), "w") as f:
        f.write(out1)
    print(f"  ✅ Sample 1: pr_42_review.md")

    # Sample 2: Large refactor PR
    sample2_diff = """diff --git a/src/lib/api-client.ts b/src/lib/api-client.ts
index 789abc..012def 100644
--- a/src/lib/api-client.ts
+++ b/src/lib/api-client.ts
@@ -1,3 +1,95 @@
+import https from 'https';
+
+interface ApiConfig {
+  baseUrl: string;
+  timeout?: number;
+}
+
+export function createApiClient(config: ApiConfig) {
+  const baseUrl = config.baseUrl;
+  const timeout = config.timeout || 30000;
+
+  async function get<T>(path: string): Promise<T> {
+    const url = baseUrl + path;
+    const response = await fetch(url, {
+      headers: { 'Content-Type': 'application/json' },
+    });
+    // TODO: add retry logic
+    return response.json();
+  }
+
+  async function post<T>(path: string, body: unknown): Promise<T> {
+    const url = baseUrl + path;
+    const response = await fetch(url, {
+      method: 'POST',
+      headers: { 'Content-Type': 'application/json' },
+      body: JSON.stringify(body),
+    });
+    if (!response.ok) {
+      throw new Error(`API error: ${response.status}`);
+    }
+    return response.json();
+  }
+
+  return { get, post };
+}
+"""

    sample2_meta = {
        "title": "Refactor: Extract reusable API client module",
        "author": "developer-2",
        "additions": 92,
        "deletions": 0,
        "changed_files": 1,
        "state": "open",
    }

    r2 = engine.review(sample2_diff, sample2_meta)
    out2 = format_markdown(r2, sample2_meta, "https://github.com/example/example-repo/pull/58")

    with open(os.path.join(samples_dir, "pr_58_review.md"), "w") as f:
        f.write(out2)
    print(f"  ✅ Sample 2: pr_58_review.md")

    print(f"\n  🔗 Sample outputs saved to {samples_dir}")
    return samples_dir


# ============ Main ============

def main():
    parser = argparse.ArgumentParser(
        description="PR Review Agent — Analyzes GitHub PRs and returns structured code reviews"
    )
    parser.add_argument("--pr", type=str, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--preview", action="store_true", help="Generate sample outputs for demo")
    parser.add_argument("--output", type=str, default="review-output.md", help="Output file path (default: review-output.md)")

    args = parser.parse_args()

    if args.preview:
        print("📋 Generating sample review outputs...")
        generate_sample_outputs(os.path.dirname(os.path.abspath(__file__)))
        print("\n✅ Preview samples generated!")
        return

    if not args.pr:
        parser.print_help()
        print("\n⚠️  Please provide a PR URL with --pr, or use --preview for demo outputs")
        sys.exit(1)

    global TOKEN
    if not TOKEN:
        TOKEN = os.environ.get("GH_TOKEN", "")

    print(f"🔍 Analyzing PR: {args.pr}")
    owner, repo, pr_num = parse_pr_url(args.pr)

    print(f"   Fetching diff from {owner}/{repo}#{pr_num}...")
    diff = fetch_pr_diff(owner, repo, pr_num)
    meta = fetch_pr_metadata(owner, repo, pr_num)

    print(f"   PR: {meta['title']} by @{meta['author']}")
    print(f"   +{meta['additions']}/-{meta['deletions']} across {meta['changed_files']} files")

    engine = ReviewEngine()
    review = engine.review(diff, meta)

    output = format_markdown(review, meta, args.pr)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n✅ Review saved to {args.output}")
    risk_count = len(review["risks"])
    imp_count = len(review["improvements"])
    print(f"   Found {risk_count} risk(s) and {imp_count} suggestion(s)")
    print(f"   Confidence: {review['confidence']}")

    # Print summary to stdout
    print("\n" + "=" * 60)
    print(review["summary"])
    print("=" * 60)


if __name__ == "__main__":
    main()
