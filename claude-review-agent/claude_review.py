#!/usr/bin/env python3
"""claude-review-agent: heuristic PR reviewer that posts structured comments.

Fetches a GitHub pull request (via the ``gh`` CLI when available, otherwise
the public GitHub REST API -- no API keys required for public PRs), runs a
deterministic heuristic review over the diff (risky shell/SQL patterns,
secrets, insecure crypto, structural signals like size and missing tests),
and renders a structured Markdown comment with Summary / Risks / Suggestions
/ Confidence sections.

Stdlib only, no third-party dependencies. Works on Windows, Linux, macOS.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --post
    python claude_review.py --diff-file changes.patch --output review.md
    python claude_review.py --pr <url> --format json

Exit codes: 0 ok, 2 usage/fetch error, 3 rate-limited (retry later / set token).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone

VERSION = "1.0.0"
TOOL_NAME = "claude-review-agent"
GITHUB_API = "https://api.github.com"
USER_AGENT = f"{TOOL_NAME}/{VERSION}"
REQUEST_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class FetchError(Exception):
    """PR data could not be fetched (bad URL, 404, network failure, ...)."""


class RateLimitError(FetchError):
    """GitHub API rate limit exhausted -- retry later or set GITHUB_TOKEN."""


# ---------------------------------------------------------------------------
# PR URL parsing
# ---------------------------------------------------------------------------

_RE_PR_URL = re.compile(
    r"https?://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)", re.IGNORECASE
)
_RE_PR_SHORTHAND = re.compile(r"^([^/\s]+)/([^/\s]+)(?:#|/pull/)(\d+)$")


def parse_pr_url(text):
    """Parse a PR URL/shorthand -> (owner, repo, number).

    Accepts:
      https://github.com/owner/repo/pull/123 (trailing /, /files, ?query ok)
      owner/repo#123
      owner/repo/pull/123
    """
    text = (text or "").strip()
    m = _RE_PR_URL.search(text)
    if m:
        owner, repo, number = m.group(1), m.group(2), int(m.group(3))
    else:
        m = _RE_PR_SHORTHAND.match(text)
        if not m:
            raise FetchError(
                f"Could not parse PR reference {text!r}. Expected "
                "https://github.com/owner/repo/pull/123 or owner/repo#123."
            )
        owner, repo, number = m.group(1), m.group(2), int(m.group(3))
    repo = repo.removesuffix(".git")
    return owner, repo, number


# ---------------------------------------------------------------------------
# Fetching: gh CLI (preferred when present) else public API (no keys needed)
# ---------------------------------------------------------------------------


def _gh_available():
    return shutil.which("gh") is not None


def fetch_via_gh(pr_url, timeout=REQUEST_TIMEOUT):
    """Fetch PR metadata + patch via the gh CLI. Returns pr dict or None."""
    if not _gh_available():
        return None
    meta_cmd = [
        "gh", "pr", "view", pr_url, "--json",
        "title,body,author,url,state,baseRefName,headRefName,"
        "additions,deletions,changedFiles,files",
    ]
    try:
        meta_raw = subprocess.run(
            meta_cmd, capture_output=True, text=True, timeout=timeout
        )
        if meta_raw.returncode != 0:
            return None
        meta = json.loads(meta_raw.stdout or "{}")
        diff_raw = subprocess.run(
            ["gh", "pr", "diff", pr_url, "--patch"],
            capture_output=True, text=True, timeout=timeout,
        )
        patch_by_path = _split_patch_by_file(diff_raw.stdout or "")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None
    files = []
    for f in meta.get("files") or []:
        path = f.get("path", "")
        files.append(
            {
                "path": path,
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "status": "modified",
                "patch": patch_by_path.get(path, ""),
                "truncated": path not in patch_by_path,
            }
        )
    author = meta.get("author") or {}
    _fill_missing_patches(files)
    return {
        "owner": "", "repo": "", "number": 0,
        "url": meta.get("url", pr_url),
        "title": meta.get("title", ""),
        "author": author.get("login", "unknown"),
        "body": meta.get("body") or "",
        "state": meta.get("state", ""),
        "base": meta.get("baseRefName", ""),
        "head": meta.get("headRefName", ""),
        "additions": meta.get("additions", 0),
        "deletions": meta.get("deletions", 0),
        "changed_files": meta.get("changedFiles", len(files)),
        "files": files,
        "fetch_mode": "gh",
        "warnings": [],
    }


def _split_patch_by_file(patch_text):
    """Split a unified diff into {new_path: per-file patch}."""
    result = {}
    current_path = None
    buf = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git"):
            if current_path is not None:
                result[current_path] = "\n".join(buf)
            parts = line.split(" b/", 1)
            current_path = parts[1] if len(parts) == 2 else None
            buf = [line]
        elif current_path is not None:
            buf.append(line)
        elif line.startswith("+++ b/"):
            current_path = line[len("+++ b/"):]
            buf = [line]
    if current_path is not None and buf:
        result[current_path] = "\n".join(buf)
    return result


def _fill_missing_patches(files):
    # gh --patch omits binary/empty files; patch="" already set by caller.
    return files


def _api_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _rate_limit_reset_msg(headers):
    try:
        reset = int(headers.get("X-RateLimit-Reset", "0"))
        when = datetime.fromtimestamp(reset, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        return f" Rate limit resets at {when}."
    except (ValueError, TypeError):
        return ""


def api_get_json(url, timeout=REQUEST_TIMEOUT):
    """GET JSON from the GitHub API. Raises FetchError / RateLimitError."""
    req = urllib.request.Request(url, headers=_api_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = dict(resp.headers.items())
            return json.loads(resp.read().decode("utf-8")), headers
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read().decode("utf-8", "replace")
            message = (json.loads(payload).get("message", "") if payload else "")
        except (ValueError, AttributeError):
            message = ""
        headers = dict(exc.headers.items()) if exc.headers else {}
        remaining = headers.get("X-RateLimit-Remaining")
        limited = (
            exc.code == 429
            or (exc.code == 403 and (remaining == "0" or "rate limit" in message.lower()))
        )
        if limited:
            raise RateLimitError(
                "GitHub API rate limit exhausted (unauthenticated requests get "
                "60/hour per IP)." + _rate_limit_reset_msg(headers) + " Retry later, "
                "or set GITHUB_TOKEN (5000/hour) and re-run. No paid key needed."
            ) from exc
        if exc.code == 404:
            raise FetchError(
                f"PR not found at {url}. Check the URL (public repos need no key; "
                "private repos need GITHUB_TOKEN)."
            ) from exc
        raise FetchError(f"GitHub API error {exc.code}: {message or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Network error reaching GitHub API: {exc.reason}") from exc
    except (ValueError, OSError) as exc:
        raise FetchError(f"Failed to read GitHub API response: {exc}") from exc


def fetch_via_api(owner, repo, number, timeout=REQUEST_TIMEOUT):
    """Fetch PR metadata + per-file patches via the public REST API."""
    base = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    meta, _ = api_get_json(base, timeout=timeout)
    files, page, warnings = [], 1, []
    while True:
        batch, _ = api_get_json(f"{base}/files?per_page=100&page={page}", timeout=timeout)
        if not isinstance(batch, list) or not batch:
            break
        for f in batch:
            files.append(
                {
                    "path": f.get("filename", ""),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "status": f.get("status", "modified"),
                    "patch": f.get("patch", "") or "",
                    "truncated": "patch" not in f,
                }
            )
        if len(batch) < 100 or page >= 10:
            if page >= 10:
                warnings.append("File list truncated at 1000 files; review is partial.")
            break
        page += 1
    missing = [f["path"] for f in files if f["truncated"]]
    if missing:
        warnings.append(
            "No patch for %d file(s) (binary or too large to render): %s. "
            "Those files were NOT analyzed."
            % (len(missing), ", ".join(missing[:10]))
        )
    token_used = bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    return {
        "owner": owner, "repo": repo, "number": number,
        "url": meta.get("html_url", f"https://github.com/{owner}/{repo}/pull/{number}"),
        "title": meta.get("title", ""),
        "author": (meta.get("user") or {}).get("login", "unknown"),
        "body": meta.get("body") or "",
        "state": meta.get("state", ""),
        "base": (meta.get("base") or {}).get("ref", ""),
        "head": (meta.get("head") or {}).get("ref", ""),
        "additions": meta.get("additions", 0),
        "deletions": meta.get("deletions", 0),
        "changed_files": meta.get("changed_files", len(files)),
        "files": files,
        "fetch_mode": "api+token" if token_used else "api",
        "warnings": warnings,
    }


def fetch_pr(pr_ref, timeout=REQUEST_TIMEOUT, no_gh=False):
    """Fetch PR data. gh CLI first (if present), else unauthenticated API."""
    owner, repo, number = parse_pr_url(pr_ref)
    canonical = f"https://github.com/{owner}/{repo}/pull/{number}"
    if not no_gh:
        via_gh = fetch_via_gh(canonical, timeout=timeout)
        if via_gh is not None:
            via_gh.update({"owner": owner, "repo": repo, "number": number})
            return via_gh
    return fetch_via_api(owner, repo, number, timeout=timeout)


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------

_RE_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

_DOC_SUFFIXES = {".md", ".rst", ".txt", ".adoc", ".mdx"}
_DOC_PREFIXES = ("docs/", "doc/", "documentation/", ".github/ISSUE_TEMPLATE/")


def is_docs(path):
    p = (path or "").lower()
    return p.split("/")[-1].rpartition(".")[2] in {s.lstrip(".") for s in _DOC_SUFFIXES} or p.startswith(_DOC_PREFIXES)


def categorize_file(path):
    """Bucket a path: docs / test / config / workflow / source / lockfile / other."""
    p = (path or "").lower()
    name = p.split("/")[-1]
    if is_docs(p):
        return "docs"
    if (
        "test" in name or name.startswith("test_") or name.endswith("_test.py")
        or "/tests/" in p or "/test/" in p or "/__tests__/" in p
        or name.endswith((".test.js", ".test.ts", ".spec.js", ".spec.ts"))
    ):
        return "test"
    if p.startswith(".github/workflows/"):
        return "workflow"
    if name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                "poetry.lock", "pdm.lock", "cargo.lock", "gemfile.lock",
                "composer.lock", "go.sum"):
        return "lockfile"
    if (name in ("package.json", "pyproject.toml", "setup.py", "setup.cfg",
                 "requirements.txt", "dockerfile", "docker-compose.yml",
                 "makefile", "cmakelists.txt", ".gitignore", ".gitattributes")
            or p.startswith(".github/") or name.endswith((".toml", ".ini", ".cfg"))):
        return "config"
    if name.rpartition(".")[2] in (
        "py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "rb",
        "php", "c", "h", "cpp", "hpp", "cs", "swift", "kt", "scala",
        "sh", "ps1", "sql", "tf", "yaml", "yml",
    ):
        return "source"
    return "other"


def iter_added_lines(patch):
    """Yield (new_lineno|None, text) for added lines in a unified patch."""
    lineno = None
    for line in (patch or "").splitlines():
        m = _RE_HUNK.match(line)
        if m:
            lineno = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield lineno, line[1:]
            if lineno is not None:
                lineno += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        elif line.startswith(" ") or line.startswith("\\"):
            if lineno is not None and not line.startswith("\\"):
                lineno += 1
        elif line.startswith("@@"):
            continue


# ---------------------------------------------------------------------------
# Heuristic risk rules (no LLM / API key required)
# ---------------------------------------------------------------------------
# Each rule: (id, base_severity, compiled_regex, message_template)

RISK_RULES = [
    ("rm_recursive", "HIGH", re.compile(
        r"(?:^|[\s;&|(`'\"$])(?:sudo(?:\s+[-\w=]+)*\s+)?"
        r"(?:(?:/|usr/|usr/local/|bin/)bin/)?rm\s+[^\n]*?(?:-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)"),
     "Recursive `rm` in added lines can irreversibly delete directory trees."),
    ("drop_table", "HIGH", re.compile(r"\bDROP\s+(TEMPORARY\s+)?TABLE\b", re.IGNORECASE),
     "`DROP TABLE` irreversibly deletes a whole table and its data."),
    ("truncate", "HIGH", re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
     "`TRUNCATE` instantly wipes every row of a table."),
    ("delete_no_where", "HIGH", re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
     "`DELETE FROM` here has no `WHERE` on the same statement -- it would delete every row."),
    ("git_push_force", "MEDIUM", re.compile(
        r"\bgit\b[^\n]*\bpush\b[^\n]*?(?:--force(?![-\w])|(?:^|\s)-[a-zA-Z]*f[a-zA-Z]*|\+[^\s\"']+)",
        re.IGNORECASE),
     "Force-push (`--force`/`-f`/`+refspec`) rewrites shared history."),
    ("pipe_to_shell", "HIGH", re.compile(
        r"\b(?:curl|wget)\b[^\n]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", re.IGNORECASE),
     "Piping `curl`/`wget` output straight into a shell runs unreviewed remote code."),
    ("hardcoded_secret", "HIGH", re.compile(
        r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|xox[bpas]-[A-Za-z0-9-]+"
        r"|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"
        r"|\baws_secret_access_key\b|(?i:\b(?:password|passwd|api[_-]?key|secret[_-]?key|client[_-]?secret)\b)\s*[:=]\s*['\"][^'\"]{3,}['\"]"
        r"|(?i:\btoken\b)\s*[:=]\s*['\"][A-Za-z0-9_\-.~+/=]{8,}['\"])"),
     "Possible hardcoded credential/secret committed to the repo."),
    ("shell_exec", "MEDIUM", re.compile(
        r"(\beval\s*\(|\bexec\s*\(|os\.system\s*\(|shell\s*=\s*True"
        r"|dangerouslySetInnerHTML|\.innerHTML\s*=|\bFunction\s*\(|child_process)"),
     "Dynamic code/shell execution (`eval`, `shell=True`, `innerHTML`, ...) is an injection risk."),
    ("sql_injection", "MEDIUM", re.compile(
        r"(f['\"].*\b(SELECT|INSERT|UPDATE|DELETE)\b"
        r"|\b(SELECT|INSERT|UPDATE|DELETE)\b[^\n]*\+[^\n]*(request|input|params|args|form|user))",
        re.IGNORECASE),
     "SQL built via string interpolation/concatenation risks injection; use parameters."),
    ("insecure_crypto", "MEDIUM", re.compile(
        r"(verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0"
        r"|ssl\._create_unverified_context|hashlib\.(md5|sha1)\s*\(|MODE_ECB"
        r"|chmod\s+[0-7]*777|\b0\.0\.0\.0\b)"),
     "Insecure default (TLS verification off, weak hash, ECB, open perms/bind)."),
    ("remote_install", "MEDIUM", re.compile(
        r"\bpip\s+install\b[^\n]*https?://|\bnpm\s+(i(nstall)?|add)\b[^\n]*(git\+|https?://)",
        re.IGNORECASE),
     "Installing dependencies straight from a URL bypasses registry pinning."),
]

_RE_TOKEN = re.compile(
    r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|xox[bpas]-[A-Za-z0-9-]+)"
)


def _redact(text):
    """Mask secret-looking tokens so the review itself never echoes them."""
    return _RE_TOKEN.sub("[REDACTED]", text)


def _shorten(text, limit=200):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ---------------------------------------------------------------------------
# Review engine
# ---------------------------------------------------------------------------


def analyze_pr(pr):
    """Run heuristic analysis. Returns findings + stats + warnings."""
    findings, warnings = [], list(pr.get("warnings") or [])
    cat_counts = {}
    reviewed_lines = 0
    for f in pr.get("files") or []:
        cat = categorize_file(f.get("path", ""))
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        patch = f.get("patch") or ""
        if f.get("truncated"):
            continue
        for lineno, text in iter_added_lines(patch):
            if not text.strip():
                continue
            reviewed_lines += 1
            loc = f"{f['path']}:{lineno}" if lineno is not None else f["path"]
            for rule_id, severity, rx, message in RISK_RULES:
                if rule_id == "delete_no_where" and re.search(
                    r"\bWHERE\b", text, re.IGNORECASE
                ):
                    continue
                if rx.search(text):
                    sev = severity
                    note = ""
                    if is_docs(f.get("path", "")) and rule_id != "hardcoded_secret":
                        # Docs often *mention* risky constructs illustratively.
                        sev = "MEDIUM" if severity == "HIGH" else severity
                        note = " (in documentation -- likely illustrative; confirm no copy-paste risk)"
                    findings.append(
                        {
                            "rule": rule_id,
                            "severity": sev,
                            "location": loc,
                            "message": message + note,
                            "snippet": _shorten(_redact(text)),
                        }
                    )
    total = (pr.get("additions") or 0) + (pr.get("deletions") or 0)
    stats = {
        "files": pr.get("changed_files") or len(pr.get("files") or []),
        "additions": pr.get("additions") or 0,
        "deletions": pr.get("deletions") or 0,
        "total": total,
        "categories": cat_counts,
        "reviewed_added_lines": reviewed_lines,
    }
    # Structural (non-line) findings -> suggestions + confidence input.
    structural = []
    if total > 500:
        structural.append(
            "Large diff (%d changed lines). Consider splitting into smaller, "
            "independently reviewable PRs." % total
        )
    if stats["files"] > 20:
        structural.append(
            "Many files touched (%d). Confirm the scope is intentional and "
            "nothing unrelated slipped in." % stats["files"]
        )
    if cat_counts.get("source") and not cat_counts.get("test"):
        structural.append(
            "Source files changed but no test files were touched. "
            "Add or update regression tests."
        )
    if cat_counts.get("workflow"):
        structural.append(
            "CI workflow files changed -- these affect every PR. Double-check "
            "permissions, triggers (`pull_request_target` is risky), and secrets use."
        )
    if cat_counts.get("lockfile"):
        structural.append(
            "Lockfile changed. Confirm the dependency bump is intentional and "
            "review the manifest diff alongside it."
        )
    if any("migrat" in (f.get("path") or "").lower() for f in pr.get("files") or []):
        structural.append(
            "Migration files touched. Verify the migration is reversible and "
            "safe against existing production data."
        )
    return findings, stats, structural, warnings


def _severity_rank(sev):
    return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(sev, 3)


def decide_confidence(pr, stats, warnings):
    """Confidence in the *review's completeness* (not the code's safety)."""
    reasons = []
    level = "High"
    if warnings:
        level = "Low"
        reasons.append("part of the diff was unavailable for analysis")
    if stats["total"] > 1000 or stats["files"] > 20:
        level = "Low"
        reasons.append(
            f"large scope ({stats['files']} files, {stats['total']} changed lines) "
            "exceeds reliable heuristic review size"
        )
    elif stats["total"] > 300 or stats["files"] > 10:
        if level != "Low":
            level = "Medium"
        reasons.append(
            f"moderate scope ({stats['files']} files, {stats['total']} changed lines)"
        )
    if not reasons:
        if stats["categories"].get("docs") and not stats["categories"].get("source"):
            reasons.append("small docs-only change with the full diff analyzed")
        else:
            reasons.append("focused diff with the full patch analyzed")
    return {"level": level, "reason": "; ".join(reasons)}


def build_summary(pr, stats, findings):
    """Deterministic 3-sentence summary of the PR."""
    n_files = stats["files"]
    cats = stats["categories"]
    if cats.get("docs") and not cats.get("source") and not cats.get("test"):
        scope = "documentation only"
    elif cats.get("test") and not cats.get("source"):
        scope = "tests"
    elif cats:
        top = sorted(cats.items(), key=lambda kv: (-kv[1], kv[0]))
        scope = ", ".join(f"{c} ({n})" for c, n in top[:3])
    else:
        scope = "no file changes reported"
    s1 = (
        f"PR '{pr.get('title', 'untitled')}' by @{pr.get('author', 'unknown')} "
        f"changes {n_files} file(s) (+{stats['additions']}/-{stats['deletions']})."
    )
    s2 = f"Scope covers {scope}; target branch is `{pr.get('base', '?')}` from `{pr.get('head', '?')}`."
    highs = sum(1 for f in findings if f["severity"] == "HIGH")
    meds = sum(1 for f in findings if f["severity"] == "MEDIUM")
    if highs or meds:
        s3 = (
            f"Heuristic scan flagged {highs} high- and {meds} medium-severity "
            f"pattern(s) below that a reviewer should verify before merging."
        )
    else:
        s3 = "Heuristic scan found no high-risk patterns, so this looks routine pending normal human review."
    return " ".join([s1, s2, s3])


_FIX_HINTS = {
    "rm_recursive": "Remove the recursive delete or restrict it to an explicit sandbox path.",
    "drop_table": "Confirm the table drop is intended, backed up, and migration-gated.",
    "truncate": "Confirm the wipe is intended; prefer a batched delete behind a migration.",
    "delete_no_where": "Add a restrictive WHERE clause or confirm the full-table wipe.",
    "git_push_force": "If this documents a runbook, recommend --force-with-lease instead.",
    "pipe_to_shell": "Vendor/pin the script and verify its checksum instead of piping to shell.",
    "hardcoded_secret": "Rotate the exposed credential and move it to a secret manager/env var.",
    "shell_exec": "Validate/sanitize inputs or use a safe API (no shell=True/eval).",
    "sql_injection": "Use parameterized queries instead of string-built SQL.",
    "insecure_crypto": "Restore secure defaults (verify TLS, strong hash, least-privilege perms).",
    "remote_install": "Pin the dependency to a registry version with a hash.",
}


def build_suggestions(findings, structural, stats):
    """Actionable suggestions; always returns at least 2 items."""
    suggestions, seen = [], set()
    for f in sorted(findings, key=lambda x: (_severity_rank(x["severity"]), x["rule"])):
        hint = _FIX_HINTS.get(f["rule"], "Review and address this finding.")
        key = ("fix", f["rule"])
        if key not in seen:
            seen.add(key)
            suggestions.append(f"[{f['severity']}] {hint} (see `{f['location']}`)")
        if len(suggestions) >= 6:
            break
    for item in structural:
        if item not in seen:
            seen.add(item)
            suggestions.append(item)
    if not stats["categories"].get("test") and stats["categories"].get("source"):
        item = "Add regression tests covering the changed behavior."
        if item not in seen:
            suggestions.append(item)
    if len(suggestions) < 2:
        suggestions += [
            "No code changes requested by the heuristic scan; proceed with normal human review.",
            "Consider updating docs/changelog if user-facing behavior changed.",
        ]
    return suggestions[:8]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def short_pr_ref(pr):
    if pr.get("owner") and pr.get("repo") and pr.get("number"):
        return f"{pr['owner']}/{pr['repo']}#{pr['number']}"
    return pr.get("url", "local diff")


def render_markdown(pr, summary, findings, suggestions, confidence, stats, warnings):
    """Structured Markdown comment: Summary / Risks / Suggestions / Confidence."""
    lines = [
        f"## Code Review — {short_pr_ref(pr)}",
        "",
        f"**Title:** {pr.get('title', 'untitled')}  ",
        f"**Author:** @{pr.get('author', 'unknown')}  ",
        f"**Files changed:** {stats['files']} (+{stats['additions']}/-{stats['deletions']})  ",
        f"**Confidence:** {confidence['level']} — {confidence['reason']}",
        "",
        "### Summary",
        "",
        summary,
        "",
        "### Risks",
        "",
    ]
    if findings:
        grouped = {}
        for f in sorted(findings, key=lambda x: (_severity_rank(x["severity"]), x["rule"], x["location"])):
            grouped.setdefault(
                (f["severity"], f["rule"], f["message"]), []
            ).append(f)
        for (sev, _rule, msg), items in grouped.items():
            locs = ", ".join(f"`{x['location']}`" for x in items[:3])
            extra = f" (+{len(items) - 3} more)" if len(items) > 3 else ""
            n = len(items)
            lines.append(
                f"- [{sev}] {msg} — {n} occurrence(s) at {locs}{extra}  \n"
                f"  e.g. `{items[0]['snippet']}`"
            )
    else:
        lines.append("- No high-risk patterns detected in the analyzed diff.")
    lines += ["", "### Suggestions", ""]
    for s in suggestions:
        lines.append(f"- {s}")
    if warnings:
        lines += ["", "### Review limitations", ""]
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
    lines += [
        "",
        "---",
        f"<sub>Generated by {TOOL_NAME} v{VERSION} (deterministic heuristics, no LLM). "
        f"Fetched via `{pr.get('fetch_mode', 'local')}`. "
        "Claude API integration is optional — see README. "
        "Unauthenticated GitHub API use (60 req/hour); set GITHUB_TOKEN for 5000/hour.</sub>",
    ]
    return "\n".join(lines) + "\n"


def render_json(pr, summary, findings, suggestions, confidence, stats, warnings):
    return json.dumps(
        {
            "tool": TOOL_NAME,
            "version": VERSION,
            "pr": {
                "ref": short_pr_ref(pr),
                "url": pr.get("url"),
                "title": pr.get("title"),
                "author": pr.get("author"),
                "state": pr.get("state"),
                "base": pr.get("base"),
                "head": pr.get("head"),
                "fetch_mode": pr.get("fetch_mode"),
            },
            "summary": summary,
            "risks": findings,
            "suggestions": suggestions,
            "confidence": confidence,
            "stats": stats,
            "warnings": warnings,
        },
        indent=2,
    ) + "\n"


def review_pr_data(pr):
    """Full pipeline on fetched PR data -> dict with summary/risks/etc."""
    findings, stats, structural, warnings = analyze_pr(pr)
    confidence = decide_confidence(pr, stats, warnings)
    summary = build_summary(pr, stats, findings)
    suggestions = build_suggestions(findings, structural, stats)
    return {
        "summary": summary,
        "risks": findings,
        "suggestions": suggestions,
        "confidence": confidence,
        "stats": stats,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Local diff-file mode (offline review, also used by tests)
# ---------------------------------------------------------------------------


def pr_from_diff_file(path, title=None):
    """Build a pr-like dict from a local unified diff file."""
    text = open(path, encoding="utf-8", errors="replace").read()
    by_file = _split_patch_by_file(text)
    if not by_file:
        # Fall back: treat the whole file as one patch (e.g. gh --patch w/o
        # diff --git headers still yields hunks we can scan).
        by_file = {"CHANGES.patch": text}
    files = []
    additions = deletions = 0
    for fpath, patch in by_file.items():
        adds = sum(
            1 for ln in patch.splitlines()
            if ln.startswith("+") and not ln.startswith("+++")
        )
        dels = sum(
            1 for ln in patch.splitlines()
            if ln.startswith("-") and not ln.startswith("---")
        )
        additions += adds
        deletions += dels
        files.append(
            {
                "path": fpath, "additions": adds, "deletions": dels,
                "status": "modified", "patch": patch, "truncated": False,
            }
        )
    name = title or f"local diff ({os.path.basename(path)})"
    return {
        "owner": "", "repo": "", "number": 0,
        "url": path, "title": name, "author": "local",
        "body": "", "state": "", "base": "?", "head": "?",
        "additions": additions, "deletions": deletions,
        "changed_files": len(files), "files": files,
        "fetch_mode": "local", "warnings": [],
    }


# ---------------------------------------------------------------------------
# Posting (opt-in; uses gh CLI so no token plumbing needed)
# ---------------------------------------------------------------------------


def post_comment(pr_url, markdown):
    """Post the review as a PR comment via gh. Returns True on success."""
    if not _gh_available():
        raise FetchError("Cannot --post: the `gh` CLI is not installed or not on PATH.")
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(markdown)
        body_file = fh.name
    try:
        proc = subprocess.run(
            ["gh", "pr", "comment", pr_url, "--body-file", body_file],
            capture_output=True, text=True, timeout=60,
        )
    finally:
        try:
            os.unlink(body_file)
        except OSError:
            pass
    if proc.returncode != 0:
        raise FetchError(
            f"`gh pr comment` failed (is `gh` authenticated? run `gh auth status`). "
            f"Details: {(proc.stderr or proc.stdout or '').strip()[:500]}"
        )
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser():
    p = argparse.ArgumentParser(
        prog="claude-review",
        description="Heuristic PR reviewer: structured Summary/Risks/Suggestions/Confidence "
        "comment. Works on public PRs with no API keys.",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--pr", metavar="URL",
                     help="PR URL, e.g. https://github.com/owner/repo/pull/123 (or owner/repo#123)")
    src.add_argument("--diff-file", metavar="PATH",
                     help="Review a local unified diff file instead of fetching (offline).")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown",
                   help="Output format (default: markdown).")
    p.add_argument("--output", metavar="PATH", help="Write output to file (default: stdout).")
    p.add_argument("--post", action="store_true",
                   help="Post the Markdown review as a PR comment via `gh` (needs auth; off by default).")
    p.add_argument("--no-gh", action="store_true",
                   help="Skip the `gh` CLI and use the public GitHub API directly.")
    p.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT,
                   help="Network timeout in seconds (default: 30).")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.post and args.diff_file:
        print("error: --post requires --pr (a diff file has no PR to comment on).",
              file=sys.stderr)
        return 2
    if args.post and args.format != "markdown":
        print("error: --post requires Markdown output (drop --format json).", file=sys.stderr)
        return 2
    try:
        if args.diff_file:
            if not os.path.isfile(args.diff_file):
                print(f"error: diff file not found: {args.diff_file}", file=sys.stderr)
                return 2
            pr = pr_from_diff_file(args.diff_file)
            pr_ref = None
        else:
            try:
                pr = fetch_pr(args.pr, timeout=args.timeout, no_gh=args.no_gh)
            except RateLimitError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 3
            pr_ref = f"https://github.com/{pr['owner']}/{pr['repo']}/pull/{pr['number']}"
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = review_pr_data(pr)
    if args.format == "json":
        output = render_json(pr, result["summary"], result["risks"],
                             result["suggestions"], result["confidence"],
                             result["stats"], result["warnings"])
    else:
        output = render_markdown(pr, result["summary"], result["risks"],
                                 result["suggestions"], result["confidence"],
                                 result["stats"], result["warnings"])
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output)
            print(f"Wrote {args.format} review to {args.output}")
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(output)
    if args.post:
        try:
            post_comment(pr_ref, output)
            print(f"Posted review comment to {pr_ref}")
        except FetchError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
