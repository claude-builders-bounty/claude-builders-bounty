#!/usr/bin/env python3
"""
claude-review — Claude Code PR review sub-agent (CLI).

Bounty: claude-builders-bounty/claude-builders-bounty Issue #4 — $150 (Opire)
https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    claude-review --diff-file changes.diff --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --post   # opt-in only

What it does
------------
Fetches a public pull-request diff (no token, no API key, no LLM call),
analyses it with small deterministic heuristics, and prints a structured
Markdown review:

    Summary (2-3 sentences) / Identified Risks / Improvement Suggestions /
    Confidence (Low / Medium / High) / Files changed

What it does NOT do
-------------------
* It never posts a comment unless you pass ``--post`` *and* set
  ``GITHUB_TOKEN``. By default it is read-only: it only reads the PR.
* It never writes to the repository, never runs the changed code, and
  never sends the diff anywhere except the public GitHub URLs it fetches
  it from. There is no LLM API key to leak and no secret to configure.
* It is a heuristic review, not a full semantic review. It can spot
  common risky patterns (secrets, destructive commands, ``eval``,
  untested changes, very large diffs) and it says so in its output.
  A human reviewer should still read the diff before merging.

Stdlib only — no third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "1.0.0"
USER_AGENT = "claude-review/1.0.0 (bounty #4; public PR diffs only)"

# ---------------------------------------------------------------------------
# PR URL parsing
# ---------------------------------------------------------------------------

_PR_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/"
    r"(?:pull|pulls)/(?P<number>\d+)(?:[/?#].*)?$"
)


@dataclass
class PRRef:
    owner: str
    repo: str
    number: int

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def diff_url(self) -> str:
        return self.html_url + ".diff"

    @property
    def api_url(self) -> str:
        return (
            f"https://api.github.com/repos/{self.owner}/{self.repo}"
            f"/pulls/{self.number}"
        )


def parse_pr_url(url: str) -> PRRef:
    """Parse a GitHub PR URL, or raise ValueError with a usable message."""
    match = _PR_URL_RE.match((url or "").strip())
    if not match:
        raise ValueError(
            "Expected a GitHub PR URL like "
            "https://github.com/owner/repo/pull/123, got: "
            + repr(url)
        )
    return PRRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
    )


# ---------------------------------------------------------------------------
# Fetching (public repos: no auth)
# ---------------------------------------------------------------------------

def fetch_text(url: str, timeout: int = 30, accept: str = "*/*") -> str:
    """GET a URL as UTF-8 text. Raises RuntimeError on HTTP/network failure.

    Note: the GitHub API rejects ``Accept: text/plain`` with HTTP 415,
    so the default is ``*/*`` and API calls pass the JSON media type.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": accept}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def fetch_pr_meta(ref: PRRef) -> dict:
    """Best-effort PR metadata (title, author, state). Returns {} on failure.

    Metadata is a nice-to-have: the review works from the diff alone, so
    a failed metadata fetch only lowers confidence, it never blocks a
    review. Unauthenticated GitHub API calls are rate-limited, so this
    is deliberately allowed to fail quietly.
    """
    try:
        raw = fetch_text(ref.api_url, accept="application/vnd.github+json")
        data = json.loads(raw)
        return {
            "title": data.get("title") or "",
            "author": (data.get("user") or {}).get("login") or "",
            "state": data.get("state") or "",
            "draft": bool(data.get("draft")),
            "additions": data.get("additions"),
            "deletions": data.get("deletions"),
            "changed_files": data.get("changed_files"),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Diff parsing
# ---------------------------------------------------------------------------

@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    # (new line number in the file, added line text) — for risk locations
    added_lines: list = field(default_factory=list)

    @property
    def is_test(self) -> bool:
        lower = self.path.lower()
        return (
            "test" in lower
            or lower.startswith("tests/")
            or lower.endswith("_test.py")
            or lower.endswith(".test.js")
            or lower.endswith(".test.ts")
            or "/test_" in lower
        )

    @property
    def is_docs(self) -> bool:
        return self.path.lower().endswith((".md", ".rst", ".txt"))

    @property
    def is_lockfile(self) -> bool:
        name = self.path.rsplit("/", 1)[-1].lower()
        return name in {
            "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            "poetry.lock", "pipfile.lock", "gemfile.lock", "cargo.lock",
        }

    @property
    def language(self) -> str:
        ext = self.path.rsplit(".", 1)[-1].lower() if "." in self.path else ""
        return {
            "py": "Python", "js": "JavaScript", "ts": "TypeScript",
            "tsx": "TypeScript", "jsx": "JavaScript", "go": "Go",
            "rs": "Rust", "rb": "Ruby", "php": "PHP", "java": "Java",
            "sh": "Shell", "yml": "YAML", "yaml": "YAML",
            "json": "JSON", "md": "Markdown",
        }.get(ext, ext.upper() or "unknown")


_DIFF_FILE_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_NEW_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")


def parse_diff(diff_text: str) -> list:
    """Parse a unified diff into a list of FileChange objects."""
    files: list = []
    current: FileChange | None = None
    new_line_no = 0
    for raw_line in diff_text.splitlines():
        line = raw_line.rstrip("\n")
        file_match = _DIFF_FILE_RE.match(line)
        if file_match:
            current = FileChange(path=file_match.group(2))
            files.append(current)
            new_line_no = 0
            continue
        if line.startswith("+++ ") and current is not None and current.path == "":
            current.path = line[6:]
            continue
        if line.startswith("@@ "):
            # @@ -a,b +c,d @@ — new-file line number is the +c part.
            match = re.search(r"\+(\d+)", line)
            new_line_no = int(match.group(1)) if match else 0
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append((new_line_no, line[1:]))
            new_line_no += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
        elif line.startswith(" ") or line == "":
            new_line_no += 1
    # Drop the empty header-only entries a bare diff can produce.
    return [f for f in files if f.path]


# ---------------------------------------------------------------------------
# Heuristic risk checks
# ---------------------------------------------------------------------------
# Checks only look at *added* lines, so pre-existing code is never
# blamed on this PR. Two tiers, because a pattern *mentioned* in a
# README, a docstring or a test string is not the same as a pattern
# *executed* in code — flagging every mention produced dozens of false
# "High" risks on real PRs (e.g. a hook whose whole job is to block
# `rm -rf`, and whose tests quite rightly contain that string).
#
# 1. Secrets are checked on the raw line, in every file: a leaked key
#    is a leak even in a doc example, and a reviewer can dismiss it.
#    Silently missing a real key would be worse.
# 2. Everything else is checked only on executable code lines: code
#    files only (never docs, tests, logs or lockfiles), never inside a
#    Python docstring or a comment, and with quoted strings stripped —
#    so `return "git push --force is blocked"` (an error message) is
#    not flagged, while a real `rm -rf` command is. The call itself
#    (``os.system(``, ``eval(``) is still checked on the raw line, so
#    ``os.system("rm -rf /")`` is still caught as an os.system risk.

_SECRET_PATTERNS = [
    ("High", re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*\S+"),
     "Possible AWS credential in added lines — rotate it and move it to a secret store."),
    ("High", re.compile(r"(?i)(api[_-]?key|api[_-]?token|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
     "Possible API key / token hard-coded in added lines."),
    ("High", re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
     "Possible hard-coded password in added lines."),
    ("High", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
     "Private key material added to the repo."),
    ("High", re.compile(r"(?i)\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
     "Possible GitHub token in added lines — revoke it immediately if real."),
]

_CODE_PATTERNS = [
    ("High", re.compile(r"\brm\s+(?:-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r|--recursive\s+--force)\b"),
     "Destructive `rm -rf` in added code — a wrong path here is unrecoverable."),
    ("High", re.compile(r"(?i)\bdrop\s+table\b"),
     "`DROP TABLE` in added code — drops a whole table, data is not recoverable."),
    ("High", re.compile(r"(?i)\bdelete\s+from\b(?![\s\S]*\bwhere\b)"),
     "`DELETE FROM` in added code — check it has a WHERE clause before merging."),
    ("High", re.compile(r"(?i)\bgit\s+push\b[^\n]*--force(?!-with-lease)"),
     "`git push --force` in added code — prefer `--force-with-lease`."),
    ("High", re.compile(r"\beval\s*\("),
     "`eval()` in added code — executes arbitrary code; use a safe parser instead."),
    ("High", re.compile(r"(?i)\bexec\s*\(\s*['\"]"),
     "`exec()` on a string in added code — executes arbitrary code."),
    ("Medium", re.compile(r"os\.system\s*\("),
     "`os.system()` in added code — prefer `subprocess.run()` without `shell=True`."),
    ("Medium", re.compile(r"subprocess\.(?:run|Popen|call)\s*\([^)]*shell\s*=\s*True"),
     "`subprocess` with `shell=True` in added code — shell-injection risk."),
    ("Medium", re.compile(r"(?i)pickle\.loads?\s*\("),
     "`pickle.load(s)` on untrusted data can execute arbitrary code."),
    ("Medium", re.compile(r"(?i)\bexcept\s*:"),
     "Bare `except:` in added code — it also swallows KeyboardInterrupt/SystemExit."),
    ("Medium", re.compile(r"(?i)\bprint\s*\(.*(?:password|token|secret|api[_-]?key)"),
     "Added code prints something that looks like a credential — check the logs."),
    ("Medium", re.compile(r"console\.log\s*\("),
     "Added `console.log` debug output — remove it before merging if it was only for debugging."),
    ("Medium", re.compile(r"(?i)\bTODO\b|\bFIXME\b|\bXXX\b"),
     "Added TODO / FIXME — fine to merge, but check it is tracked, not forgotten."),
]

_QUOTED_RE = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`""")
_TRIPLE_QUOTE_RE = re.compile(r'"""|\'\'\'')


def _clean_code_line(text: str, language: str) -> str:
    """Strip quoted strings (and #-comments in Python/Shell) from a line.

    What is left is the code that would actually execute.
    """
    cleaned = _QUOTED_RE.sub("", text)
    if language in ("Python", "Shell", "Ruby"):
        cleaned = cleaned.split("#", 1)[0]
    return cleaned


def find_risks(files: list) -> list:
    """Return a list of (severity, file, line_no, message) risk findings."""
    risks = []
    for f in files:
        in_docstring = False
        for line_no, text in f.added_lines:
            # Secrets: raw line, every file.
            for severity, pattern, message in _SECRET_PATTERNS:
                if pattern.search(text):
                    risks.append((severity, f.path, line_no, message))
                    break
            else:
                # Code patterns: code files only, never docs/tests/logs.
                if f.is_docs or f.is_test or f.is_lockfile:
                    continue
                if f.path.lower().endswith((".log", ".json", ".lock")):
                    continue
                # Track Python triple-quoted docstrings across lines.
                if f.language == "Python":
                    if _TRIPLE_QUOTE_RE.search(text):
                        if len(_TRIPLE_QUOTE_RE.findall(text)) % 2 == 1:
                            in_docstring = not in_docstring
                        if in_docstring:
                            continue
                    elif in_docstring:
                        continue
                stripped = text.strip()
                if not stripped or stripped.startswith(("#", "*", "|", ">")):
                    continue
                cleaned = _clean_code_line(text, f.language)
                if not cleaned.strip():
                    continue
                for severity, pattern, message in _CODE_PATTERNS:
                    # eval/exec/os.system are about the call itself, so
                    # check them on the raw line; the rest on the cleaned
                    # line so string literals are not mistaken for code.
                    haystack = text if pattern.pattern.startswith(
                        (r"\beval", r"(?i)\bexec", r"os\.system")
                    ) else cleaned
                    if pattern.search(haystack):
                        risks.append((severity, f.path, line_no, message))
                        break
    return risks


def find_suggestions(files: list, risks: list) -> list:
    """Actionable suggestions, derived from the diff — not generic filler."""
    suggestions = []
    total_added = sum(f.additions for f in files)
    total_files = len(files)
    has_tests = any(f.is_test for f in files)
    code_files = [f for f in files if not f.is_docs and not f.is_test]
    has_docs = any(f.is_docs for f in files)

    if risks:
        high = sum(1 for r in risks if r[0] == "High")
        if high:
            suggestions.append(
                f"Resolve the {high} high-severity risk(s) above before merging — "
                "at minimum confirm each flagged line is a false positive."
            )
    if code_files and not has_tests:
        suggestions.append(
            "Add a test for the new behaviour — this PR changes code but adds "
            "no test files, so a regression would only be caught by hand."
        )
    if total_added > 500:
        suggestions.append(
            f"Consider splitting this PR ({total_added} added lines across "
            f"{total_files} files) — smaller PRs are faster and safer to review."
        )
    if total_files > 10:
        suggestions.append(
            "This PR touches many files — check that every file is needed for "
            "this change and not an unrelated drive-by."
        )
    if any(f.is_lockfile for f in files):
        suggestions.append(
            "Lockfile changes are included — verify they come from the declared "
            "dependency change and not an unrelated `install` run."
        )
    # Docs largely in a language other than English (e.g. Chinese README
    # in an English-language repo) — worth translating for the maintainer.
    for f in files:
        if not f.is_docs:
            continue
        cjk = sum(
            1 for _, text in f.added_lines
            for ch in text if "\u4e00" <= ch <= "\u9fff"
            or "\u3040" <= ch <= "\u30ff" or "\uac00" <= ch <= "\ud7a3"
        )
        if cjk > 50:
            suggestions.append(
                f"`{f.path}` is largely written in a non-English language — "
                "consider an English version, as this repo's maintainers and "
                "bounty board work in English."
            )
            break
    if code_files and not has_docs:
        suggestions.append(
            "Add a short README / doc note for the new behaviour if a user or "
            "another contributor needs to discover it."
        )
    if not suggestions:
        suggestions.append(
            "No blocking issues found — a quick manual read of the diff for "
            "naming and edge cases is still worth doing before merging."
        )
    return suggestions


def confidence_for(files: list, risks: list, meta_ok: bool) -> str:
    """Confidence in *this review*, not in the PR. Calibrated, documented.

    High: small, test-covered diff, no high risks, metadata available.
    Medium: moderate size, or no tests, or medium risks, or no metadata.
    Low: large diff, high risks, no tests, or the diff could not be
    fully parsed / metadata was unavailable.
    """
    total_added = sum(f.additions for f in files)
    total_files = len(files)
    has_tests = any(f.is_test for f in files)
    high_risks = sum(1 for r in risks if r[0] == "High")

    if not files or total_added == 0:
        return "Low"
    if high_risks or total_added > 1000 or (total_added > 500 and not has_tests):
        return "Low"
    if total_added > 500 or total_files > 10 or not has_tests or not meta_ok:
        return "Medium"
    return "High"


def build_summary(ref: PRRef, meta: dict, files: list) -> str:
    """2-3 sentence summary, generated from the diff — never invented."""
    total_added = sum(f.additions for f in files)
    total_deleted = sum(f.deletions for f in files)
    languages = sorted({f.language for f in files if f.language != "unknown"})
    test_count = sum(1 for f in files if f.is_test)
    title = (meta.get("title") or "").strip()
    author = (meta.get("author") or "").strip()

    first = (
        f"This PR changes {len(files)} file(s) "
        f"(+{total_added}/-{total_deleted} lines)"
    )
    if title:
        first += f" — “{title}”"
    if author:
        first += f", by @{author}"
    first += "."
    second_parts = []
    if languages:
        second_parts.append("mainly " + ", ".join(languages))
    if test_count:
        second_parts.append(f"including {test_count} test file(s)")
    else:
        second_parts.append("with no test files changed")
    second = "The change touches " + "; ".join(second_parts) + "."
    main_files = ", ".join(f.path for f in files[:3])
    third = f"Key files: {main_files}."
    if len(files) > 3:
        third += f" (and {len(files) - 3} more)"
    return f"{first} {second} {third}"


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(ref: PRRef, meta: dict, files: list, risks: list,
                    suggestions: list, confidence: str, summary: str) -> str:
    lines = []
    lines.append("## 🤖 Claude Code Review")
    lines.append("")
    lines.append(f"> **PR**: [{ref.html_url}]({ref.html_url})")
    if meta.get("title"):
        lines.append(f"> **Title**: {meta['title']}")
    if meta.get("author"):
        lines.append(f"> **Author**: @{meta['author']}")
    lines.append("")
    lines.append("### 📋 Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append("### ⚠️ Identified Risks")
    lines.append("")
    if risks:
        for severity, path, line_no, message in risks:
            where = f"`{path}:{line_no}`" if line_no else f"`{path}`"
            lines.append(f"- **{severity}** — {where}: {message}")
    else:
        lines.append("- No high- or medium-severity risks found by the heuristic checks.")
    lines.append("")
    lines.append("### 💡 Improvement Suggestions")
    lines.append("")
    for suggestion in suggestions:
        lines.append(f"- {suggestion}")
    lines.append("")
    lines.append(f"### ✅ Confidence: {confidence}")
    lines.append("")
    lines.append(
        "Confidence is in *this review*, not in the PR: High means the diff "
        "was small, test-covered and fully readable; Medium / Low mean the "
        "diff was large, untested, or partly unreadable, so a human should "
        "read it more carefully."
    )
    lines.append("")
    lines.append("### 📁 Files changed")
    lines.append("")
    lines.append("| File | + | - |")
    lines.append("| --- | ---: | ---: |")
    for f in files:
        lines.append(f"| `{f.path}` | {f.additions} | {f.deletions} |")
    lines.append("")
    lines.append(
        "_Heuristic review only — no LLM was called, no token was used, and "
        "no comment was posted by this tool unless `--post` was given. "
        "Please read the diff yourself before merging._"
    )
    lines.append("")
    return "\n".join(lines)


def render_json(ref: PRRef, meta: dict, files: list, risks: list,
                suggestions: list, confidence: str, summary: str) -> str:
    return json.dumps({
        "pr": ref.html_url,
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "summary": summary,
        "risks": [
            {"severity": s, "file": p, "line": n, "message": m}
            for s, p, n, m in risks
        ],
        "suggestions": suggestions,
        "confidence": confidence,
        "files": [
            {"path": f.path, "additions": f.additions, "deletions": f.deletions}
            for f in files
        ],
    }, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Review pipeline
# ---------------------------------------------------------------------------

@dataclass
class Review:
    ref: PRRef
    meta: dict
    files: list
    risks: list
    suggestions: list
    confidence: str
    summary: str
    markdown: str


def review_diff(ref: PRRef, diff_text: str, meta: dict | None = None) -> Review:
    meta = meta or {}
    files = parse_diff(diff_text)
    risks = find_risks(files)
    suggestions = find_suggestions(files, risks)
    confidence = confidence_for(files, risks, bool(meta))
    summary = build_summary(ref, meta, files)
    markdown = render_markdown(
        ref, meta, files, risks, suggestions, confidence, summary
    )
    return Review(ref, meta, files, risks, suggestions, confidence, summary, markdown)


def post_comment(ref: PRRef, body: str) -> str:
    """Post the review as a PR comment. Explicit opt-in only.

    Requires GITHUB_TOKEN in the environment. Refuses without one, and
    never falls back to any other credential.
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "--post needs GITHUB_TOKEN set in the environment. "
            "It is not set, so nothing was posted."
        )
    url = (
        f"https://api.github.com/repos/{ref.owner}/{ref.repo}"
        f"/issues/{ref.number}/comments"
    )
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("html_url", "")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"GitHub returned HTTP {exc.code} when posting the comment"
        ) from exc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub PR and print a structured Markdown review.",
    )
    parser.add_argument("--pr", required=True,
                        help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", default=None,
                        help="Use a local unified-diff file instead of fetching it")
    parser.add_argument("--output", "-o", default=None,
                        help="Write the Markdown review to this file (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--post", action="store_true",
                        help="Also post the review as a PR comment (needs GITHUB_TOKEN)")
    parser.add_argument("--version", action="version", version=f"claude-review {VERSION}")
    return parser


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ref = parse_pr_url(args.pr)
    except ValueError as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2

    if args.diff_file:
        try:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"claude-review: cannot read diff file: {exc}", file=sys.stderr)
            return 2
        meta = {}
    else:
        try:
            diff_text = fetch_text(ref.diff_url)
        except RuntimeError as exc:
            print(f"claude-review: {exc}", file=sys.stderr)
            return 1
        meta = fetch_pr_meta(ref)

    if not diff_text.strip():
        print("claude-review: empty diff — is this PR open with changes?",
              file=sys.stderr)
        return 1

    review = review_diff(ref, diff_text, meta)
    output = (
        review.markdown if args.format == "markdown"
        else render_json(ref, meta, review.files, review.risks,
                         review.suggestions, review.confidence, review.summary)
    )

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote review to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output)

    if args.post:
        try:
            comment_url = post_comment(ref, review.markdown)
        except RuntimeError as exc:
            print(f"claude-review: {exc}", file=sys.stderr)
            return 1
        print(f"Posted review comment: {comment_url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
