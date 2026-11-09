#!/usr/bin/env python3
"""claude-review: structured Pull Request review agent.

Fetches a GitHub PR diff (public API, no token required for public repos),
runs a deterministic static review, and prints a structured Markdown review
comment with the sections a maintainer actually reads:

    - Summary of changes (2-3 sentences)
    - Identified risks (list)
    - Improvement suggestions (list)
    - Confidence score: Low / Medium / High

Usage:
    python3 claude_review.py --pr https://github.com/owner/repo/pull/123
    python3 claude_review.py --diff pr.diff [--title "..."] [--url "..."]
    cat pr.diff | python3 claude_review.py

Set GITHUB_TOKEN to raise the API rate limit or to read private repos you
have access to. Standard library only; no dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------


@dataclass
class FileChange:
    path: str
    old_path: str | None = None
    added: int = 0
    removed: int = 0
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    is_binary: bool = False


@dataclass
class Finding:
    severity: str  # "high" | "medium" | "low"
    message: str


# --------------------------------------------------------------------------
# Diff parsing
# --------------------------------------------------------------------------

_DIFF_GIT = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_diff(diff_text: str) -> list[FileChange]:
    """Parse a unified diff into per-file changes."""
    files: list[FileChange] = []
    current: FileChange | None = None
    for line in diff_text.splitlines():
        m = _DIFF_GIT.match(line)
        if m:
            current = FileChange(path=m.group(2), old_path=m.group(1))
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("Binary files") or line.startswith("GIT binary patch"):
            current.is_binary = True
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            current.added += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-"):
            current.removed += 1
            current.removed_lines.append(line[1:])
    return files


# --------------------------------------------------------------------------
# File classification
# --------------------------------------------------------------------------

TEST_HINTS = ("test", "spec", "__tests__", "conftest", "fixtures")
DOC_EXTS = (".md", ".rst", ".txt", ".adoc")
DEP_FILES = {
    "requirements.txt", "requirements-dev.txt", "pipfile", "pipfile.lock",
    "pyproject.toml", "setup.py", "setup.cfg", "package.json",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.mod", "go.sum",
    "cargo.toml", "cargo.lock", "gemfile", "gemfile.lock", "composer.json",
    "composer.lock", "pom.xml", "build.gradle",
}
CI_HINTS = (".github/workflows/", ".gitlab-ci", "jenkinsfile", ".circleci/")
MIGRATION_HINTS = ("migration", "migrations/", "alembic", "db/migrate")
AUTH_HINTS = ("auth", "session", "token", "permission", "rbac", "acl",
              "login", "oauth", "jwt", "password")


def classify(path: str) -> str:
    p = path.lower()
    base = p.rsplit("/", 1)[-1]
    if any(h in p for h in CI_HINTS):
        return "ci"
    if any(h in p for h in MIGRATION_HINTS):
        return "migration"
    if base in DEP_FILES:
        return "dependency"
    if any(h in p for h in TEST_HINTS) or base.startswith("test_"):
        return "test"
    if p.endswith(DOC_EXTS):
        return "docs"
    if p.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg", ".env.example")):
        return "config"
    return "code"


# --------------------------------------------------------------------------
# Risk detectors (run over added lines, per file)
# --------------------------------------------------------------------------

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
     "possible hard-coded credential"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "possible AWS access key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
     "private key material"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "possible GitHub personal access token"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "possible API secret key"),
]

CODE_RISK_PATTERNS = [
    (re.compile(r"\beval\s*\("), "use of eval()"),
    (re.compile(r"\bexec\s*\("), "use of exec()"),
    (re.compile(r"shell\s*=\s*True"), "subprocess with shell=True"),
    (re.compile(r"\bos\.system\s*\("), "use of os.system()"),
    (re.compile(r"\bpickle\.loads?\s*\("), "pickle deserialization of data"),
    (re.compile(r"(?i)verify\s*=\s*False"), "TLS certificate verification disabled"),
    (re.compile(r"(?i)md5\s*\(|sha1\s*\("), "weak hash function (MD5/SHA1)"),
    (re.compile(r"0\.0\.0\.0"), "binding to 0.0.0.0 (all interfaces)"),
    (re.compile(r"(?i)disable.*csrf|csrf.*disable|@csrf_exempt"),
     "CSRF protection disabled/exempted"),
    (re.compile(r"(?i)allow_origins\s*=\s*\[?\s*['\"]\*['\"]"),
     "permissive CORS (wildcard origin)"),
]

SQL_PATTERNS = [
    (re.compile(r"(?i)(execute|query|raw)\s*\(.*(%s|\+|\.format\(|f['\"])"),
     "possible SQL string building (injection risk)"),
    (re.compile(r"(?i)\bDROP\s+TABLE\b"), "DROP TABLE statement"),
    (re.compile(r"(?i)\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)"),
     "DELETE FROM without an obvious WHERE clause"),
    (re.compile(r"(?i)\bTRUNCATE\b"), "TRUNCATE statement"),
]

DEBUG_PATTERNS = [
    (re.compile(r"\bconsole\.log\s*\("), "console.log"),
    (re.compile(r"\bprint\s*\("), "print statement"),
    (re.compile(r"\bbreakpoint\s*\(|\bdebugger\b"), "debugger/breakpoint"),
    (re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK)\b"), "TODO/FIXME marker"),
]


def scan_lines(files: list[FileChange]) -> list[Finding]:
    findings: list[Finding] = []
    pattern_def_noted: set[str] = set()
    for f in files:
        kind = classify(f.path)
        for line in f.added_lines:
            for pat, label in SECRET_PATTERNS:
                if pat.search(line):
                    findings.append(Finding(
                        "high", f"`{f.path}`: {label} added "
                                f"(`{line.strip()[:60]}...`)"))
            if kind != "code":
                continue
            for pat, label in CODE_RISK_PATTERNS:
                if pat.search(line):
                    findings.append(Finding(
                        "high", f"`{f.path}`: {label} "
                                f"(`{line.strip()[:60]}`)"))
            for pat, label in SQL_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                prefix = line[:m.start()]
                in_string = (prefix.count('"') % 2 == 1
                             or prefix.count("'") % 2 == 1)
                stripped = line.strip()
                in_comment = stripped.startswith(
                    ("#", "//", "*", "-", '"""', "'''"))
                if in_comment:
                    findings.append(Finding(
                        "low", f"`{f.path}`: SQL keywords mentioned in a "
                               f"comment/doc line ({label}); documentation "
                               "text, not executed SQL"))
                elif "re.compile" in line or "regex" in line.lower():
                    # The line *defines* a detection pattern (guard /
                    # linter code), it does not execute SQL.
                    if f.path not in pattern_def_noted:
                        pattern_def_noted.add(f.path)
                        findings.append(Finding(
                            "low", f"`{f.path}`: SQL detection-pattern "
                                   "definitions present (guard/linter "
                                   "code; not executed SQL)"))
                elif in_string:
                    findings.append(Finding(
                        "low", f"`{f.path}`: SQL keywords inside a string "
                               f"literal ({label}); verify the string is "
                               "documentation/pattern text, not executed SQL"))
                else:
                    findings.append(Finding(
                        "high", f"`{f.path}`: {label} "
                                f"(`{line.strip()[:60]}`)"))
            for pat, label in DEBUG_PATTERNS:
                if pat.search(line):
                    findings.append(Finding(
                        "low", f"`{f.path}`: debug leftover / {label} "
                               f"(`{line.strip()[:60]}`)"))
    return findings


def structural_findings(files: list[FileChange]) -> list[Finding]:
    findings: list[Finding] = []
    total_add = sum(f.added for f in files)
    total_del = sum(f.removed for f in files)
    kinds = {classify(f.path) for f in files}

    if "migration" in kinds:
        mig = [f.path for f in files if classify(f.path) == "migration"]
        findings.append(Finding(
            "medium", f"Database migration changes in {', '.join(mig[:3])}: "
                      "verify rollback and backfill safety."))
    if "dependency" in kinds:
        deps = [f.path for f in files if classify(f.path) == "dependency"]
        findings.append(Finding(
            "medium", f"Dependency manifest/lockfile changes in "
                      f"{', '.join(deps[:3])}: review new or bumped packages "
                      "for supply-chain risk and changelogs."))
    if "ci" in kinds:
        ci = [f.path for f in files if classify(f.path) == "ci"]
        findings.append(Finding(
            "medium", f"CI/workflow changes in {', '.join(ci[:3])}: check "
                      "action versions are pinned and permissions are minimal."))
    auth_files = [f.path for f in files
                  if any(h in f.path.lower() for h in AUTH_HINTS)]
    if auth_files:
        findings.append(Finding(
            "medium", f"Auth/session-sensitive files touched "
                      f"({', '.join(auth_files[:3])}): review access-control "
                      "impact carefully."))
    if len(files) >= 20 or total_add + total_del >= 1500:
        findings.append(Finding(
            "medium", f"Large PR: {len(files)} files, "
                      f"+{total_add}/-{total_del}. Hard to review atomically; "
                      "a regression can hide in the bulk."))
    if total_add + total_del > 0 and total_del > total_add * 3 and total_del > 100:
        findings.append(Finding(
            "medium", f"Deletion-heavy change (+{total_add}/-{total_del}): "
                      "confirm removed code/config is truly dead."))
    return findings


def summarize(files: list[FileChange], title: str | None) -> str:
    total_add = sum(f.added for f in files)
    total_del = sum(f.removed for f in files)
    by_kind: dict[str, int] = {}
    for f in files:
        by_kind[classify(f.path)] = by_kind.get(classify(f.path), 0) + 1
    kind_txt = ", ".join(f"{n} {k}" for k, n in
                         sorted(by_kind.items(), key=lambda kv: -kv[1]))
    headline = f"\"{title}\" " if title else "This PR "
    s1 = (f"{headline}touches {len(files)} file(s) ({kind_txt}) with "
          f"+{total_add}/-{total_del} lines.")
    touched = [f.path for f in
               sorted(files, key=lambda f: -(f.added + f.removed))[:3]]
    if touched:
        s1 += (f" The biggest changes are in "
               f"{', '.join('`' + t + '`' for t in touched)}.")
    code = by_kind.get("code", 0)
    tests = by_kind.get("test", 0)
    if code and tests:
        s2 = "Source changes come with test changes, so behavior is at least partly pinned down."
    elif code:
        s2 = "Source code changes land without accompanying test changes."
    elif by_kind.get("docs"):
        s2 = "The change is documentation-led and carries little runtime risk."
    else:
        s2 = "No application source files are modified."
    return f"{s1} {s2}"


def suggestions(files: list[FileChange],
                findings: list[Finding]) -> list[str]:
    out: list[str] = []
    kinds = {classify(f.path) for f in files}
    if "code" in kinds and "test" not in kinds:
        out.append("Add or update tests covering the changed code paths; "
                   "right now nothing pins the new behavior.")
    if any("CI/workflow" in f.message for f in findings):
        out.append("Pin third-party GitHub Actions to full-length commit "
                   "SHAs and keep `permissions:` at least privilege.")
    if any("migration" in f.message.lower() for f in findings):
        out.append("Include the migration's rollback path (down migration "
                   "or restore plan) in the PR description.")
    if any("credential" in f.message or "access key" in f.message
           or "PRIVATE KEY" in f.message or "secret key" in f.message
           for f in findings):
        out.append("Remove any real secret from the diff, rotate it if it "
                   "was ever live, and load it from the environment or a "
                   "secret manager instead.")
    if any("dependency" in f.message.lower() for f in findings):
        out.append("Call out dependency changes explicitly in the PR "
                   "description (what changed and why) to speed up review.")
    total = sum(f.added + f.removed for f in files)
    if len(files) >= 20 or total >= 1500:
        out.append("Consider splitting this PR into smaller, independently "
                   "reviewable pieces (prep/refactor first, behavior second).")
    if any(f.severity == "low" and "debug leftover" in f.message
           for f in findings):
        out.append("Strip debug output and resolve TODO/FIXME markers "
                   "before merge, or convert them into tracked issues.")
    if not out:
        out.append("No structural improvements needed; a normal maintainer "
                   "read-through of the diff should be sufficient.")
    return out


def confidence(files: list[FileChange], findings: list[Finding],
               truncated: bool) -> str:
    if truncated or not files:
        return "Low"
    highs = sum(1 for f in findings if f.severity == "high")
    total = sum(f.added + f.removed for f in files)
    if total <= 400 and highs == 0:
        return "High"
    if total <= 1500:
        return "Medium"
    return "Low"


def render_markdown(files: list[FileChange], title: str | None,
                    url: str | None, findings: list[Finding],
                    truncated: bool) -> str:
    total_add = sum(f.added for f in files)
    total_del = sum(f.removed for f in files)
    lines = ["## PR Review (claude-review)", ""]
    if url:
        lines.append(f"**Pull request:** {url}")
    if title:
        lines.append(f"**Title:** {title}")
    lines.append(f"**Files changed:** {len(files)} "
                 f"(+{total_add} / -{total_del})")
    lines.append("")
    lines.append("### Summary")
    lines.append(summarize(files, title))
    lines.append("")
    lines.append("### Identified risks")
    ordered = sorted(findings,
                     key=lambda f: {"high": 0, "medium": 1, "low": 2}[f.severity])
    if ordered:
        for f in ordered:
            lines.append(f"- **[{f.severity.upper()}]** {f.message}")
    else:
        lines.append("- No high-signal risks detected by static review. "
                     "This does not replace a human read of logic and tests.")
    if truncated:
        lines.append("- **[LOW]** The diff was truncated by the API; "
                     "the review may be incomplete.")
    lines.append("")
    lines.append("### Improvement suggestions")
    for s in suggestions(files, findings):
        lines.append(f"- {s}")
    lines.append("")
    lines.append("### Confidence score")
    lines.append(f"**{confidence(files, findings, truncated)}** "
                 "(deterministic static review of the diff: file mix, size, "
                 "and pattern signals; not a substitute for running the "
                 "test suite)")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# GitHub access
# --------------------------------------------------------------------------

PR_URL_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = PR_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"Not a GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _gh_get(url: str, accept: str) -> tuple[str, dict]:
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "claude-review-agent")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", "replace")
        return body, dict(resp.headers.items())


def fetch_pr(owner: str, repo: str, number: int) -> tuple[str, str, bool]:
    """Return (diff_text, title, truncated)."""
    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    meta_raw, _ = _gh_get(base, "application/vnd.github+json")
    title = json.loads(meta_raw).get("title", "")
    diff, _ = _gh_get(base, "application/vnd.github.diff")
    return diff, title, False


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def collapse(findings: list[Finding]) -> list[Finding]:
    """Merge repeated findings that differ only in the quoted snippet."""
    counts: dict[tuple[str, str], int] = {}
    exemplars: dict[tuple[str, str], str] = {}
    order: list[tuple[str, str]] = []
    for f in findings:
        head = f.message.split(" (`")[0]
        key = (f.severity, head)
        if key not in counts:
            counts[key] = 0
            order.append(key)
            exemplars[key] = f.message
        counts[key] += 1
    out: list[Finding] = []
    for key in order:
        msg = exemplars[key]
        if counts[key] > 1 and " (`" in msg:
            head, _, rest = msg.partition(" (`")
            snippet = rest[:60].rstrip("`)").rstrip("`")
            msg = f"{head} (x{counts[key]} occurrences; first: `{snippet}`)"
        elif counts[key] > 1:
            msg = f"{msg} (x{counts[key]} occurrences)"
        out.append(Finding(key[0], msg))
    return out


def review_diff(diff_text: str, title: str | None = None,
                url: str | None = None, truncated: bool = False) -> str:
    files = parse_diff(diff_text)
    findings = collapse(scan_lines(files) + structural_findings(files))
    return render_markdown(files, title, url, findings, truncated)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="claude-review",
        description="Structured PR review: summary, risks, suggestions, "
                    "confidence.")
    ap.add_argument("--pr", help="GitHub PR URL to review")
    ap.add_argument("--diff", help="Path to a .diff/.patch file to review")
    ap.add_argument("--title", help="PR title (with --diff)")
    ap.add_argument("--url", help="PR URL to cite (with --diff)")
    ap.add_argument("--output", help="Write the review to this file "
                                     "instead of stdout")
    args = ap.parse_args(argv)

    if args.pr:
        owner, repo, number = parse_pr_url(args.pr)
        diff, title, truncated = fetch_pr(owner, repo, number)
        out = review_diff(diff, title=title, url=args.pr,
                          truncated=truncated)
    elif args.diff:
        with open(args.diff, encoding="utf-8", errors="replace") as fh:
            out = review_diff(fh.read(), title=args.title, url=args.url)
    elif not sys.stdin.isatty():
        out = review_diff(sys.stdin.read(), title=args.title, url=args.url)
    else:
        ap.print_help()
        return 2

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
