#!/usr/bin/env python3
"""
claude-review — Claude Code PR review sub-agent.
Analyzes GitHub PR diffs for risks, improvements, and code quality.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  claude-review --pr https://github.com/owner/repo/pull/123 --format json
  claude-review --pr 123 --repo owner/repo
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ─── Config ─────────────────────────────────────────────────────
CONFIG_FILE = os.path.expanduser("~/.claude-review.json")
DEFAULT_CONFIG = {
    "max_diff_size": 500000,       # 500KB max diff
    "large_pr_threshold": 1000,     # lines changed
    "large_file_threshold": 200,    # additions per file
    "secrets_patterns": {
        "enabled": True,
        "min_entropy": 3.5,
    },
    "languages": {
        "enabled": True,
    }
}


def load_config():
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                user_config = json.load(f)
                config.update(user_config)
        except (json.JSONDecodeError, OSError):
            pass
    return config


CONFIG = load_config()


# ─── Utilities ───────────────────────────────────────────────────

def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"WARN: {msg}", file=sys.stderr)


def info(msg):
    print(f"INFO: {msg}", file=sys.stderr)


def parse_pr_input(pr, repo):
    """Parse PR identifier from various input formats."""
    # URL format
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # repo format covered by --repo flag
    if repo:
        m2 = re.match(r"([^/]+)/(.+)", repo)
        if m2:
            return m2.group(1), m2.group(2), int(pr)

    fatal(f"Invalid PR format: {pr}. Use URL (https://github.com/owner/repo/pull/123) or --repo flag")


def api_get(url, accept=None):
    """Fetch JSON from GitHub API with optional Accept header."""
    if not GITHUB_TOKEN:
        fatal("GITHUB_TOKEN environment variable not set")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("User-Agent", "claude-review")
    if accept:
        req.add_header("Accept", accept)
    else:
        req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        if e.code == 403 and "rate limit" in body.lower():
            fatal("GitHub API rate limit exceeded. Wait or use a token with higher limits.")
        if e.code == 404:
            fatal(f"PR not found (404): {url}")
        fatal(f"API error {e.code}: {body}")
    except Exception as e:
        fatal(f"Request failed: {e}")


# ─── Data Fetching ───────────────────────────────────────────────

def get_pr_diff(owner, repo, number):
    """Fetch raw PR diff."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("User-Agent", "claude-review")
    req.add_header("Accept", "application/vnd.github.diff")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        diff = resp.read().decode()
        if len(diff) > CONFIG["max_diff_size"]:
            warn(f"Diff is very large ({len(diff)} bytes). Analysis may be limited.")
        return diff
    except urllib.error.HTTPError as e:
        fatal(f"Diff fetch error {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        fatal(f"Diff request failed: {e}")


def get_pr_metadata(owner, repo, number):
    """Get comprehensive PR metadata."""
    pr_data = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    files_data = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files")
    issues_data = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/issues")

    # Try to get the PR's commit messages
    commits_data = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/commits")

    changed_files = []
    total_additions = 0
    total_deletions = 0
    languages = Counter()

    for f in files_data:
        ext = os.path.splitext(f["filename"])[1].lower()
        lang = extension_to_language(ext)
        languages[lang] += 1

        changed_files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes": f["changes"],
            "language": lang,
            "patch": f.get("patch", ""),
        })
        total_additions += f["additions"]
        total_deletions += f["deletions"]

    commit_messages = []
    for c in commits_data:
        msg = c.get("commit", {}).get("message", "").split("\n")[0]
        commit_messages.append(msg)

    return {
        "title": pr_data.get("title", ""),
        "description": pr_data.get("body", "") or "",
        "author": pr_data.get("user", {}).get("login", "unknown"),
        "state": pr_data.get("state", ""),
        "draft": pr_data.get("draft", False),
        "created_at": pr_data.get("created_at", ""),
        "updated_at": pr_data.get("updated_at", ""),
        "base_branch": pr_data.get("base", {}).get("ref", ""),
        "head_branch": pr_data.get("head", {}).get("ref", ""),
        "changed_files": changed_files,
        "total_changed_files": len(changed_files),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "total_changes": total_additions + total_deletions,
        "languages": dict(languages.most_common()),
        "primary_language": languages.most_common(1)[0][0] if languages else "Unknown",
        "commit_messages": commit_messages,
        "labels": [l["name"] for l in pr_data.get("labels", [])],
    }


# ─── Language Detection ──────────────────────────────────────────

def extension_to_language(ext):
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript/React", ".jsx": "JavaScript/React",
        ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
        ".php": "PHP", ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
        ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".r": "R", ".m": "Objective-C", ".mm": "Objective-C++",
        ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
        ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
        ".md": "Markdown", ".rst": "reStructuredText",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
        ".sql": "SQL", ".graphql": "GraphQL", ".gql": "GraphQL",
        ".dockerfile": "Dockerfile", "dockerfile": "Dockerfile",
        ".tf": "Terraform", ".proto": "Protobuf",
        ".vue": "Vue", ".svelte": "Svelte",
        ".wasm": "WebAssembly", ".zig": "Zig",
    }
    return mapping.get(ext, "Other")


# ─── Analysis ────────────────────────────────────────────────────

def analyze_diff(diff, metadata):
    """Comprehensive PR diff analysis."""
    findings = {
        "risks": [],
        "improvements": [],
        "positives": [],
        "secrets": [],
        "security_issues": [],
        "inline_comments": [],
    }

    # ── PR Description Quality Check ──
    desc = metadata["description"].strip()
    if not desc:
        findings["improvements"].append("PR has no description — add context for reviewers")
    elif len(desc) < 50:
        findings["improvements"].append(f"PR description is very short ({len(desc)} chars) — add more detail")

    # ── Branch Name Check ──
    branch = metadata["head_branch"]
    if branch in ("main", "master", "develop"):
        findings["risks"].append(f"PR is from `{branch}` branch — should use a feature branch")

    # ── Draft Check ──
    if metadata["draft"]:
        findings["improvements"].append("PR is in Draft mode — mark as Ready for Review when complete")

    # ── Commit Message Quality Check ──
    for msg in metadata["commit_messages"]:
        if not re.match(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?:", msg):
            findings["improvements"].append(
                f"Commit `{msg[:60]}` doesn't follow Conventional Commits format"
            )

    # ── Test Coverage Check ──
    has_tests = any(
        re.match(r"(test|spec|__tests__)", f["filename"]) or
        f["filename"].endswith((".test.js", ".test.ts", "_test.go", ".spec.py", "test_.py"))
        for f in metadata["changed_files"]
    )

    code_files = [
        f for f in metadata["changed_files"]
        if f["language"] not in ("Markdown", "YAML", "JSON", "Other", "CSS", "SCSS", "LESS", "HTML")
    ]

    if code_files and not has_tests and metadata["total_changes"] > 50:
        findings["improvements"].append(
            "PR modifies source code but doesn't include test changes — add tests for new/modified logic"
        )

    # ── Parse and Analyze Diff Lines ──
    lines = diff.split("\n")
    current_file = ""
    added_lines = []
    removed_lines = []
    current_file_patch = ""
    patch_line_num = 0

    for i, line in enumerate(lines):
        # Track file changes
        fm = re.match(r"\+\+\+ b/(.+)", line)
        if fm:
            current_file = fm.group(1)
            current_file_patch = ""
            patch_line_num = 0
            continue

        if line.startswith("@@"):
            current_file_patch = ""
            patch_line_num = 0
            continue

        if line.startswith("+"):
            code = line[1:]
            added_lines.append((current_file, code))
            if patch_line_num > 0:
                current_file_patch += code + "\n"
            patch_line_num += 1
        elif line.startswith("-"):
            removed_lines.append((current_file, line[1:]))
        else:
            if patch_line_num > 0:
                current_file_patch += line + "\n"
            patch_line_num += 1

    # ── Language-specific Analysis ──
    # (Run even when CONFIG.languages.enabled, but always check basic patterns)

    for fname, code in added_lines:
        code_stripped = code.strip()
        if not code_stripped or code_stripped.startswith(("#", "//", "/*", "*", "<!--")):
            continue

        # ── Secrets / Hardcoded Credentials ──
        secret_patterns = [
            (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"(?i)(secret|api_key|apikey|api\.key)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded API key/secret"),
            (r"(?i)(token|auth_token|bearer)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded token"),
            (r"(?i)(private_key|ssh_key|pem)\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded private key"),
            (r"(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----", "Embedded private key (PEM)"),
            (r"(?i)connection\s*string\s*[:=]\s*['\"].*password", "Connection string with password"),
            (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
            (r"(?i)sk-[a-zA-Z0-9]{20,}", "OpenAI/Anthropic API key pattern"),
            (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
            (r"(?i)gho_[a-zA-Z0-9]{36}", "GitHub OAuth Access Token"),
            (r"(?i)ghu_[a-zA-Z0-9]{36}", "GitHub User-to-Server Token"),
            (r"(?i)ghs_[a-zA-Z0-9]{36}", "GitHub Server-to-Server Token"),
        ]

        for pattern, desc in secret_patterns:
            if re.search(pattern, code):
                findings["risks"].append(f"Potential {desc} in `{fname}`")
                findings["secrets"].append({"file": fname, "type": desc, "line": code_stripped[:80]})

        # ── Security Issues ──
        security_patterns = [
            (r"(?i)eval\s*\(", "`eval()` call — risk of code injection"),
            (r"(?i)exec\s*\(", "`exec()` call — risk of code injection"),
            (r"(?i)subprocess\.[a-z]+\s*\(.*shell\s*=\s*True", "subprocess with shell=True — command injection risk"),
            (r"(?i)os\.system\s*\(", "os.system() — command injection risk"),
            (r"(?i)\$\(.*\)|\`.*\`", "Shell injection via command substitution"),
            (r"(?i)innerHTML\s*=", "innerHTML assignment — XSS risk"),
            (r"(?i)dangerouslySetInnerHTML", "dangerouslySetInnerHTML — XSS risk"),
            (r"(?i)document\.write\s*\(", "document.write() — XSS risk"),
            (r"(?i)pickle\.loads?\s*\(", "Pickle deserialization — remote code execution risk"),
            (r"(?i)yaml\.load\s*\([^)]*[^S]", "yaml.load() without SafeLoader — code execution risk"),
            (r"(?i)\.html\([^)]*\)", "jQuery .html() — XSS risk"),
            (r"(?i)Response\.(json|make|data)\s*\(.*user", "Might expose user-controlled data in response"),
            (r"(?i)@suppresswarnings\b", "Suppressed warnings — may hide real issues"),
            (r"(?i)sprintf\s*\(.*%s.*\$_(GET|POST|REQUEST)", "SQL injection risk via sprintf"),
            (r"(?i)/\*.*\bsecret\b.*\*/", "Secret in comment — may leak in logs/documentation"),
        ]

        for pattern, desc in security_patterns:
            if re.search(pattern, code):
                findings["risks"].append(f"{desc} in `{fname}`")
                findings["security_issues"].append({"file": fname, "description": desc, "code": code_stripped[:80]})

        # ── Code Quality Issues
        quality_patterns = [
            (r"\bprint\s*\(", "Debug print() left in code"),
            (r"\bconsole\.log\s*\(", "Debug console.log() left in code"),
            (r"TODO|FIXME|HACK|XXX|WORKAROUND", "Unresolved TODO/FIXME marker"),
            (r"except\s*:\s*\n?\s*(?:pass|#|$)", "Bare `except:` without exception type"),
            (r"catch\s*\{?\s*\}?\s*\{[^}]*\}", "Empty/generic catch block"),
            (r"(?i)var\s+\w+\s*=", "`var` keyword (consider `let`/`const`) — found in JS/TS"),
            (r"#\s*type:\s*ignore", "`# type: ignore` — suppressing type checker"),
            (r"@ts-ignore", "`@ts-ignore` — suppressing TypeScript checker"),
            (r"(?i)nocommit|DO_NOT_COMMIT|DEBUG_MODE", "Potentially intentional disable/override left in code"),
            (r"(?i)commented.{0,20}out", "Commented-out code"),
            (r"#\s*TODO", "TODO comment — incomplete work"),
            (r"#\s*FIXME", "FIXME comment — known bug"),
            (r"#\s*HACK", "HACK — non-ideal solution"),
            (r"#\s*XXX", "XXX — problematic code"),
            (r"(?i)sleep\s*\(\s*\d+\s*\)", "Hardcoded sleep/timing"),
            (r"fuck|shit|crap|stupid|wtf", "Inappropriate language in code/comment"),
        ]

        for pattern, desc in quality_patterns:
            if re.search(pattern, code):
                findings["improvements"].append(f"{desc} in `{fname}`")

        # ── Large functions/methods
        # (Simplified: just flag very long added lines)
        if len(code_stripped) > 200:
            findings["improvements"].append(
                f"Very long line ({len(code_stripped)} chars) in `{fname}` — consider splitting"
            )

    # ── File-level Analysis ──
    for f in metadata["changed_files"]:
        name = f["filename"]
        if f["additions"] > CONFIG["large_file_threshold"]:
            findings["improvements"].append(
                f"`{name}` has {f['additions']} additions — consider splitting into smaller changes"
            )

    # ── PR Size Analysis ──
    if metadata["total_changes"] > CONFIG["large_pr_threshold"]:
        findings["risks"].append(
            f"PR is very large ({metadata['total_changes']} changes) — hard to review thoroughly"
        )

    if metadata["total_changes"] < 20:
        findings["positives"].append("Small, focused change — easy to review")

    if metadata["total_changed_files"] <= 3 and metadata["total_changes"] > 0:
        findings["positives"].append(f"Change touches only {metadata['total_changed_files']} files — focused scope")

    # ── Package/Lock file check
    lock_files = [f["filename"] for f in metadata["changed_files"]
                  if f["filename"].endswith(("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.sum",
                                             "Cargo.lock", "Gemfile.lock", "poetry.lock", "composer.lock"))]
    if lock_files:
        findings["positives"].append(f"Dependency files updated ({', '.join(lock_files[:3])})")

    # ── Overall assessment
    if not findings["risks"] and not findings["security_issues"]:
        findings["positives"].append("No significant risks or security issues detected")

    if not findings["improvements"]:
        findings["positives"].append("Code quality looks clean — no debug artifacts or TODOs")

    return findings


def generate_review(metadata, diff, findings):
    """Generate structured Markdown (or JSON) review output."""
    lines = []
    lines.append(f"# PR Review: {metadata['title']}")
    lines.append("")
    lines.append(f"**Repository:** `{metadata.get('_owner','')}/{metadata.get('_repo','')}` | "
                 f"**Author:** `{metadata['author']}` | "
                 f"**Files:** {metadata['total_changed_files']} | "
                 f"**Changes:** +{metadata['total_additions']}/-{metadata['total_deletions']}")
    if metadata["languages"]:
        lang_str = ", ".join(f"{k} ({v})" for k, v in metadata["languages"].items())
        lines.append(f"**Languages:** {lang_str}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    summary_parts = []
    summary_parts.append(
        f"This PR modifies {metadata['total_changed_files']} files "
        f"across {len(metadata['languages'])} language{'s' if len(metadata['languages']) != 1 else ''} "
        f"with {metadata['total_additions']} additions and "
        f"{metadata['total_deletions']} deletions."
    )
    if metadata["description"]:
        desc_first_line = metadata["description"].split("\n")[0][:120]
        summary_parts.append(f"\n\n> {desc_first_line}")
    lines.append(" ".join(summary_parts))
    lines.append("")

    # Changed Files
    lines.append("## Changed Files")
    for f in metadata["changed_files"]:
        status_icon = {"added": "🆕", "modified": "📝", "removed": "🗑️", "renamed": "📄"}.get(f["status"], "📄")
        lines.append(f"- {status_icon} `{f['filename']}` (+{f['additions']}/-{f['deletions']})")
    lines.append("")

    # Secrets Found
    if findings["secrets"]:
        lines.append("## 🔴⚠️ Secrets Detected")
        for s in findings["secrets"]:
            lines.append(f"- `{s['file']}`: {s['type']}")
        lines.append("")
        lines.append("> **Action required:** Remove secrets from code. Use environment variables or a secrets manager.")
        lines.append("")

    # Security Issues
    if findings["security_issues"]:
        lines.append("## 🔴 Security Issues")
        for s in findings["security_issues"]:
            lines.append(f"- `{s['file']}`: {s['description']}")
        lines.append("")

    # Risks
    risk_items = [r for r in findings["risks"]
                  if not any(s.get("description", "") == r for s in findings["security_issues"])
                  and not any(s["type"] == r.replace("Potential ", "") for s in findings["secrets"])]
    if risk_items:
        lines.append("## 🔴 Identified Risks")
        for r in risk_items:
            lines.append(f"- {r}")
        lines.append("")

    # Improvements
    lines.append("## 🟡 Improvement Suggestions")
    if findings["improvements"]:
        for s in findings["improvements"]:
            lines.append(f"- {s}")
    else:
        lines.append("_No specific improvements suggested._")
    lines.append("")

    # Positives
    lines.append("## 🟢 Positives")
    if findings["positives"]:
        for p in findings["positives"]:
            lines.append(f"- {p}")
    else:
        lines.append("_No specific observations._")
    lines.append("")

    # Confidence
    total_risks = len(findings["risks"]) + len(findings["secrets"]) + len(findings["security_issues"])
    if total_risks >= 5:
        confidence = "Low"
        confidence_note = "Multiple risks detected — thorough manual review recommended"
    elif total_risks >= 2:
        confidence = "Medium"
        confidence_note = "Some issues found — review flagged items carefully"
    elif total_risks >= 1:
        confidence = "Medium-High"
        confidence_note = "Minor issues found — address flagged items"
    else:
        confidence = "High"
        confidence_note = "No risks detected — looks good to merge"

    lines.append("## Confidence Score")
    score_map = {"Low": "🟠", "Medium": "🟡", "Medium-High": "🟢", "High": "🟢"}
    lines.append(f"**{score_map.get(confidence, '')} {confidence}** — {confidence_note}")
    lines.append("")
    lines.append("---")
    lines.append(f"_Generated by claude-review at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append(f"_Token usage: {len(diff)} bytes diff analyzed across {metadata['total_changed_files']} files_")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR for risks, security issues, and code quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pr https://github.com/owner/repo/pull/123
  %(prog)s --pr 123 --repo owner/repo --output review.md
  %(prog)s --pr https://github.com/owner/repo/pull/123 --format json
        """
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL or number")
    parser.add_argument("--repo", "-r", help="Repository (owner/repo), required with numeric PR")
    parser.add_argument("--output", "-o", help="Write output to file")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")

    args = parser.parse_args()

    owner, repo, number = parse_pr_input(args.pr, args.repo)

    info(f"Reviewing PR #{number} from {owner}/{repo}...")
    info(f"Branch: {owner}/{repo}/pull/{number}")

    diff = get_pr_diff(owner, repo, number)
    metadata = get_pr_metadata(owner, repo, number)
    metadata["_owner"] = owner
    metadata["_repo"] = repo

    findings = analyze_diff(diff, metadata)

    if args.format == "json":
        result = {
            "metadata": {
                "owner": owner,
                "repo": repo,
                "number": number,
                "title": metadata["title"],
                "author": metadata["author"],
                "files": metadata["total_changed_files"],
                "additions": metadata["total_additions"],
                "deletions": metadata["total_deletions"],
                "languages": metadata["languages"],
            },
            "findings": {
                "risks_count": len(findings["risks"]),
                "improvements_count": len(findings["improvements"]),
                "positives_count": len(findings["positives"]),
                "secrets_count": len(findings["secrets"]),
                "security_issues_count": len(findings["security_issues"]),
            },
            "risks": findings["risks"],
            "secrets": findings["secrets"],
            "security_issues": findings["security_issues"],
            "improvements": findings["improvements"],
            "positives": findings["positives"],
        }
        output = json.dumps(result, indent=2)
    else:
        output = generate_review(metadata, diff, findings)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        info(f"Review written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
