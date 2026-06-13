#!/usr/bin/env python3
"""
claude-review.py — PR Review Agent for Claude Code

Fetches a GitHub PR diff via the GitHub API and produces a structured
Markdown code review.  Can be used as a standalone CLI tool or as a
sub-agent invoked by Claude Code.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
    python claude-review.py --pr 123 --owner owner --repo repo

Environment:
    GITHUB_TOKEN  — GitHub personal access token (default: reads from
                    ~/.agent/credentials/github.env or ~/.github/token)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg: str) -> None:
    print(f"⚠️  {msg}", file=sys.stderr)


def read_token_from_file(path: str) -> Optional[str]:
    """Read GITHUB_TOKEN from a .env or plain-text token file."""
    p = Path(path).expanduser()
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8").strip()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
            # plain token (no key= prefix)
            if re.match(r"^gh[pousr]_", line):
                return line
        return None
    except Exception:
        return None


def resolve_token(custom_token: Optional[str] = None) -> str:
    """Resolve GitHub token from (in order): CLI arg, env var, known files."""
    if custom_token:
        return custom_token
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        return env_token
    for candidate in [
        "~/.agent/credentials/github.env",
        "~/.github/token",
        "~/.config/gh/hosts.yml",
    ]:
        t = read_token_from_file(candidate)
        if t:
            return t
    die(
        "No GitHub token found. Provide via --token, GITHUB_TOKEN env var, "
        "or ~/.agent/credentials/github.env"
    )
    return ""  # unreachable


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse owner/repo/number from a GitHub PR URL."""
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        die(f"Could not parse PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def github_api(path: str, token: str) -> dict:
    """Call GitHub REST API and return parsed JSON."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "claude-review-agent/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        die(f"GitHub API error {e.code} for {path}:\n{body[:500]}")
    except urllib.error.URLError as e:
        die(f"Network error fetching {path}: {e}")
    return {}  # unreachable


def fetch_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch PR diff (text) via GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-agent/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        die(f"GitHub API error {e.code} fetching diff:\n{body[:500]}")
    return ""


def fetch_pr_data(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata (title, body, state, etc.)."""
    return github_api(f"/repos/{owner}/{repo}/pulls/{pr_number}", token)


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    """Fetch list of files changed in the PR."""
    return github_api(f"/repos/{owner}/{repo}/pulls/{pr_number}/files", token)


def fetch_commits(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    """Fetch commits in the PR."""
    return github_api(f"/repos/{owner}/{repo}/pulls/{pr_number}/commits", token)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

@dataclass
class FileChange:
    filename: str
    status: str  # added, modified, removed, renamed
    additions: int
    deletions: int
    changes: int
    patch: str = ""
    language: str = "Unknown"


@dataclass
class ReviewReport:
    owner: str
    repo: str
    pr_number: int
    pr_title: str
    pr_body: str
    pr_state: str
    pr_author: str
    total_commits: int
    files: list[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0

    # Analysis results
    overview: str = ""
    good_parts: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "Medium"

    # Stats
    languages: Counter = field(default_factory=Counter)

    def to_markdown(self) -> str:
        lines = []

        # ---- Header ----
        lines.append(f"# PR Review: [{self.owner}/{self.repo}#{self.pr_number}](https://github.com/{self.owner}/{self.repo}/pull/{self.pr_number})")
        lines.append("")
        lines.append(f"**Title:** {self.pr_title}")
        lines.append(f"**Author:** @{self.pr_author}  •  **State:** `{self.pr_state}`  •  **Commits:** {self.total_commits}")
        lines.append("")

        # Stats badge
        lines.append(f"> 📊 **+{self.total_additions}**  **–{self.total_deletions}**  across **{len(self.files)}** file{'s' if len(self.files)!=1 else ''}")
        lines.append("")

        # ---- Overview ----
        lines.append("## 📋 Overview")
        lines.append("")
        if self.overview:
            lines.append(self.overview)
        else:
            lines.append("_Automated summary below._")
        lines.append("")

        # Changed files list
        lines.append("### Files Changed")
        lines.append("")
        lines.append("| File | Status | + | – | Lang |")
        lines.append("|------|--------|---|---|------|")
        for f in self.files:
            status_icon = {"added": "➕", "modified": "✏️", "removed": "🗑️", "renamed": "📛"}.get(f.status, "❓")
            lines.append(f"| `{f.filename}` | {status_icon} {f.status} | {f.additions} | {f.deletions} | {f.language} |")
        lines.append("")

        # Languages
        if self.languages:
            lines.append("### Languages")
            lines.append("")
            for lang, count in self.languages.most_common():
                lines.append(f"- **{lang}**: {count} file{'s' if count!=1 else ''}")
            lines.append("")

        # ---- Good Parts ----
        lines.append("## ✅ Good Parts")
        lines.append("")
        if self.good_parts:
            for i, g in enumerate(self.good_parts, 1):
                lines.append(f"{i}. {g}")
        else:
            lines.append("_Automated scan did not detect notable positives._")
        lines.append("")

        # ---- Concerns ----
        lines.append("## ⚠️ Concerns")
        lines.append("")
        if self.concerns:
            for i, c in enumerate(self.concerns, 1):
                lines.append(f"{i}. {c}")
        else:
            lines.append("_No significant concerns detected._")
        lines.append("")

        # ---- Suggestions ----
        lines.append("## 💡 Suggestions")
        lines.append("")
        if self.suggestions:
            for i, s in enumerate(self.suggestions, 1):
                lines.append(f"{i}. {s}")
        else:
            lines.append("_None from automated scan._")
        lines.append("")

        # ---- Confidence ----
        lines.append("---")
        lines.append("")
        confidence_badge = {
            "High": "🟢 **High**",
            "Medium": "🟡 **Medium**",
            "Low": "🔴 **Low**",
        }.get(self.confidence, self.confidence)
        lines.append(f"**Confidence Score:** {confidence_badge}")
        lines.append("")
        lines.append("> _This review was generated by [claude-review-agent](https://github.com/nousresearch/hermes). "
                     "Combine with Claude Code's reasoning for deeper analysis._")
        lines.append("")

        return "\n".join(lines)


def detect_language(filename: str) -> str:
    """Map file extension to language name."""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript/React", ".jsx": "JavaScript/React",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".java": "Java",
        ".kt": "Kotlin", ".swift": "Swift", ".c": "C", ".cpp": "C++",
        ".h": "C/C++ Header", ".hpp": "C++ Header", ".cs": "C#",
        ".php": "PHP", ".sh": "Shell", ".bash": "Bash",
        ".zsh": "Zsh", ".yml": "YAML", ".yaml": "YAML",
        ".json": "JSON", ".toml": "TOML", ".md": "Markdown",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".sql": "SQL", ".dockerfile": "Dockerfile",
        "Dockerfile": "Dockerfile", ".dockerignore": "Docker",
        ".gitignore": "Git", ".env": "Env",
        ".tf": "Terraform", ".proto": "Protobuf",
        ".vue": "Vue", ".svelte": "Svelte",
    }
    # Check for dotless filenames
    basename = Path(filename).name
    if basename in ext_map:
        return ext_map[basename]
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, "Unknown")


def _find_risky_patterns(patch: str) -> list[str]:
    """Check a file's patch for common code-smell patterns."""
    issues = []
    if not patch:
        return issues
    lines = patch.splitlines()

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip context lines (starting with space) and diff headers
        if stripped.startswith("print(") and "debug" not in stripped.lower():
            issues.append(f"Line {lineno}: Debug `print()` call left in code")
        if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
            issues.append(f"Line {lineno}: Contains TODO/FIXME/HACK comment")
        # Only flag if it looks like a string/var assignment, not C struct field or == comparison
        if re.search(r'(?:password|secret|api_key|token)\s*=\s*["\']', stripped, re.IGNORECASE):
            issues.append(f"Line {lineno}: Possible hardcoded secret/key")
        if "import *" in stripped:
            issues.append(f"Line {lineno}: Wildcard import (`import *`)")
        if re.search(r"except\s*:", stripped) and "Exception" not in stripped:
            issues.append(f"Line {lineno}: Bare `except:` clause (catches all exceptions)")
        if "sys.exit(" in stripped or "os._exit(" in stripped:
            issues.append(f"Line {lineno}: Direct exit call in library code")
        if re.search(r"eval\(|exec\(|compile\(", stripped):
            issues.append(f"Line {lineno}: Use of `eval()`/`exec()` — security risk")
        if re.search(r"\.append\(.*\[\s*\]\)", stripped):
            issues.append(f"Line {lineno}: Appending to list literal — possibly redundant")
        # Long lines
        if len(stripped) > 200 and not stripped.startswith("+"):
            pass  # Only flag added lines
        if stripped.startswith("+") and len(stripped) > 200:
            issues.append(f"Line {lineno}: Very long line ({len(stripped)} chars)")

    return issues


def _summary_from_pr_body(body: str) -> str:
    """Generate a brief summary from PR description."""
    if not body or body.strip() == "":
        return "No PR description provided."
    # Strip markdown formatting, take first meaningful paragraph
    clean = re.sub(r"#{1,6}\s+", "", body)       # Remove headers
    clean = re.sub(r"\*{1,2}", "", clean)          # Remove bold/italic markers
    clean = re.sub(r"~~.*?~~", "", clean)          # Remove strikethrough
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)  # Convert links to text
    clean = re.sub(r"`{1,3}[^`]*`{1,3}", "`code`", clean)
    clean = re.sub(r"^\s*[-*+]\s+", "", clean, flags=re.MULTILINE)  # Remove list markers
    clean = re.sub(r"^\s*\d+\.\s+", "", clean, flags=re.MULTILINE)  # Remove numbered list markers
    # Split into paragraphs and find the first meaningful one
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    # Skip short boilerplate lines like AI disclosure
    meaningful = [p for p in paragraphs if len(p) > 40 or ("fix" in p.lower() or "change" in p.lower())]
    if meaningful:
        summary = meaningful[0]
        if len(summary) > 600:
            summary = summary[:597] + "..."
        return summary
    # Fallback: first non-empty paragraph
    if paragraphs:
        summary = paragraphs[0]
        if len(summary) > 600:
            summary = summary[:597] + "..."
        return summary
    return "See PR description for details."


def analyze(owner: str, repo: str, pr_number: int, token: str) -> ReviewReport:
    """Fetch PR data, run analysis, return a ReviewReport."""
    # Fetch data
    pr_data = fetch_pr_data(owner, repo, pr_number, token)
    diff_text = fetch_diff(owner, repo, pr_number, token)
    files_data = fetch_pr_files(owner, repo, pr_number, token)
    commits_data = fetch_commits(owner, repo, pr_number, token)

    # Build report
    report = ReviewReport(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        pr_title=pr_data.get("title", "(no title)"),
        pr_body=pr_data.get("body") or "",
        pr_state=pr_data.get("state", "unknown"),
        pr_author=pr_data.get("user", {}).get("login", "unknown"),
        total_commits=len(commits_data),
    )

    # Parse files
    all_concerns: list[str] = []
    all_good: list[str] = []
    risky_file_count = 0

    for f in files_data:
        fc = FileChange(
            filename=f["filename"],
            status=f.get("status", "modified"),
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
            changes=f.get("changes", 0),
            patch=f.get("patch", ""),
            language=detect_language(f["filename"]),
        )
        report.files.append(fc)
        report.total_additions += fc.additions
        report.total_deletions += fc.deletions
        report.languages[fc.language] += 1

        # Risky patterns
        if fc.patch:
            issues = _find_risky_patterns(fc.patch)
            for issue in issues:
                all_concerns.append(f"`{fc.filename}`: {issue}")
            if issues:
                risky_file_count += 1

        # Check for very large files
        if fc.changes > 300:
            all_concerns.append(
                f"`{fc.filename}`: Very large change ({fc.changes} lines). "
                "Consider splitting into smaller PRs."
            )

        # File-specific good parts
        if fc.status == "added" and fc.changes < 50:
            all_good.append(f"`{fc.filename}`: Small, focused new file added.")
        if fc.additions > 0 and fc.deletions == 0:
            pass  # Could note pure additions

    # Overview from PR body
    report.overview = _summary_from_pr_body(pr_data.get("body") or "")

    # --- Generate structured insights ---

    # General observations
    if len(report.files) <= 3:
        all_good.append(
            f"Small, focused PR with only {len(report.files)} file{'s' if len(report.files)!=1 else ''} changed — easy to review."
        )
    elif len(report.files) > 20:
        all_concerns.append(
            f"Large PR touching {len(report.files)} files. Consider breaking into smaller PRs for easier review."
        )

    if report.total_additions > report.total_deletions * 3 and report.total_deletions > 0:
        all_good.append("More additions than deletions — net growth in functionality.")
    elif report.total_deletions > report.total_additions * 2:
        all_good.append("Strong net deletion of code — good sign of cleanup/refactoring.")

    if risky_file_count == 0 and len(report.files) > 0:
        all_good.append("No code-smell patterns detected in the diff.")

    # Language diversity
    if len(report.languages) == 1:
        lang_name = list(report.languages.keys())[0]
        all_good.append(f"Single-language PR ({lang_name}) — consistent with repo conventions.")
    elif len(report.languages) > 3:
        all_concerns.append(
            f"PR spans {len(report.languages)} languages. "
            "Verify cross-language changes are intentional."
        )

    # Check if there's a description
    if not pr_data.get("body") or not pr_data["body"].strip():
        all_concerns.append(
            "PR description is empty. Adding context helps reviewers understand the motivation."
        )

    # Commit count
    if report.total_commits == 1 and len(report.files) > 5:
        all_concerns.append(
            f"Single commit with {len(report.files)} files changed. "
            "Consider splitting into multiple logical commits."
        )
    elif report.total_commits > 10:
        all_concerns.append(
            f"Many commits ({report.total_commits}) for this PR. "
            "Consider squashing related commits for a cleaner history."
        )

    # Check for config/secrets files
    config_files = [f.filename for f in report.files if ".env" in f.filename or "secret" in f.filename.lower()]
    if config_files:
        all_concerns.append(
            f"Changes to config/secret files: {', '.join(config_files[:3])}. "
            "Ensure no secrets are committed."
        )

    # File naming analysis
    temp_files = [f.filename for f in report.files if "temp" in f.filename.lower() or "tmp" in f.filename.lower()]
    if temp_files:
        all_concerns.append(
            f"Temporary/scratch files detected: {', '.join(temp_files)}. Consider cleaning up before merge."
        )

    # --- Generate suggestions ---
    suggestions = []

    # Suggest tests if none exist
    test_files = [f.filename for f in report.files if "test" in f.filename.lower() or "spec" in f.filename.lower()]
    if not test_files and any(f.language in ("Python", "JavaScript", "TypeScript", "Go", "Rust", "Java") for f in report.files):
        suggestions.append(
            "Add tests for the changes. No test/spec files were modified in this PR."
        )

    if len(report.files) > 10:
        suggestions.append(
            "Consider splitting this PR into smaller, more focused changes for faster review."
        )

    if not pr_data.get("body") or not pr_data["body"].strip():
        suggestions.append(
            "Add a PR description explaining the motivation, approach, and any breaking changes."
        )

    if risky_file_count > 0:
        suggestions.append(
            "Address the code-smell patterns flagged above (debug prints, bare excepts, etc.)."
        )

    if not suggestions:
        suggestions.append("No automated suggestions — PR looks clean from a structural standpoint.")

    # --- Determine confidence ---
    if risky_file_count == 0 and len(report.files) <= 10 and report.total_additions < 500:
        confidence = "High"
    elif risky_file_count > 5 or report.total_additions > 2000 or len(report.files) > 30:
        confidence = "Low"
    else:
        confidence = "Medium"

    # Deduplicate
    report.good_parts = list(dict.fromkeys(all_good))
    report.concerns = list(dict.fromkeys(all_concerns))
    report.suggestions = suggestions
    report.confidence = confidence

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="claude-review — PR Review Agent for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python claude-review.py --pr https://github.com/owner/repo/pull/123\n"
            "  python claude-review.py --pr 123 --owner owner --repo repo\n"
            "  python claude-review.py --pr https://github.com/owner/repo/pull/123 --format json\n"
            "\n"
            "Environment: GITHUB_TOKEN must be set, or use --token.\n"
        ),
    )
    parser.add_argument("--pr", help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--owner", help="Repository owner (if not using --pr URL)")
    parser.add_argument("--repo", help="Repository name (if not using --pr URL)")
    parser.add_argument("--pr-number", type=int, help="PR number (if not using --pr URL)")
    parser.add_argument("--token", help="GitHub personal access token (default: $GITHUB_TOKEN)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")

    args = parser.parse_args()

    # Resolve owner/repo/number
    if args.pr:
        owner, repo, number = parse_pr_url(args.pr)
    elif args.owner and args.repo and args.pr_number:
        owner, repo, number = args.owner, args.repo, args.pr_number
    else:
        parser.print_help()
        die("Provide --pr URL or --owner/--repo/--pr-number combo.")

    token = resolve_token(args.token)
    report = analyze(owner, repo, number, token)

    if args.format == "json":
        import dataclasses
        def asdict(obj):
            if isinstance(obj, list):
                return [asdict(i) for i in obj]
            if isinstance(obj, Counter):
                return dict(obj)
            if hasattr(obj, "__dataclass_fields__"):
                return {f.name: asdict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
            return obj
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        print(report.to_markdown())

    # Exit code: 0 = clean, 1 = errors, 2 = concerns found
    if report.concerns:
        sys.exit(2)


if __name__ == "__main__":
    main()
