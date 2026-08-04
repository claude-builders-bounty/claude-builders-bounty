#!/usr/bin/env python3
"""claude-review — structured PR review CLI (Opire bounty #4).

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff path/to.diff --title "feat: ..."
  python3 bounty4/claude_review.py --pr URL

Modes:
  1) Heuristic (default, zero API cost) — deterministic static analysis of the diff
  2) Optional LLM polish if ANTHROPIC_API_KEY is set (claude-sonnet)

Output: Markdown with Summary, Risks, Suggestions, Confidence.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

PR_URL_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
    re.I,
)
SHORT_RE = re.compile(r"^(?P<owner>[^/]+)/(?P<repo>[^/]+)#(?P<number>\d+)$")

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}"), "Possible hardcoded secret"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private key material in diff"),
    (re.compile(r"(?i)ghp_[A-Za-z0-9]{20,}"), "GitHub PAT-like token"),
    (re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"), "API secret-like token"),
]

RISKY_CODE = [
    (re.compile(r"\beval\s*\("), "Use of eval()"),
    (re.compile(r"\bexec\s*\("), "Use of exec()"),
    (re.compile(r"innerHTML\s*="), "innerHTML assignment (XSS risk)"),
    (re.compile(r"\bshell\s*=\s*True"), "subprocess shell=True"),
    (re.compile(r"rm\s+-rf\s+/"), "Destructive rm -rf /"),
    (re.compile(r"DROP\s+TABLE", re.I), "DROP TABLE in diff"),
    (re.compile(r"pickle\.loads"), "Unsafe pickle.loads"),
    (re.compile(r"verify\s*=\s*False"), "TLS verify disabled"),
]

TEST_HINTS = re.compile(r"(^|/)(tests?/|__tests__/|.*_test\.(py|ts|js|go)|.*\.test\.(ts|js|tsx|jsx))", re.I)
DOC_HINTS = re.compile(r"\.(md|rst|txt)$", re.I)


@dataclass
class FileDiff:
    path: str
    status: str  # added|modified|deleted|renamed
    added: int = 0
    deleted: int = 0
    plus_lines: list[str] = field(default_factory=list)


@dataclass
class Finding:
    severity: str  # high|medium|low|info
    kind: str
    message: str
    path: str | None = None


def parse_pr_ref(value: str) -> tuple[str, str, int] | None:
    value = (value or "").strip()
    m = PR_URL_RE.search(value)
    if m:
        return m.group("owner"), m.group("repo"), int(m.group("number"))
    m = SHORT_RE.match(value)
    if m:
        return m.group("owner"), m.group("repo"), int(m.group("number"))
    return None


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def fetch_pr_via_gh(owner: str, repo: str, number: int) -> tuple[str, str, str]:
    """Return (title, body, diff_text)."""
    code, out, err = _run(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "-R",
            f"{owner}/{repo}",
            "--json",
            "title,body,files",
        ]
    )
    if code != 0:
        raise RuntimeError(f"gh pr view failed: {err or out}")
    meta = json.loads(out)
    code, diff, err = _run(
        ["gh", "pr", "diff", str(number), "-R", f"{owner}/{repo}"],
        timeout=90,
    )
    if code != 0:
        raise RuntimeError(f"gh pr diff failed: {err or diff}")
    return str(meta.get("title") or ""), str(meta.get("body") or ""), diff


def fetch_pr_via_api(owner: str, repo: str, number: int, token: str | None) -> tuple[str, str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get(url: str, accept: str | None = None) -> bytes:
        h = dict(headers)
        if accept:
            h["Accept"] = accept
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()

    meta = json.loads(
        get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}").decode()
    )
    try:
        diff = get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
            accept="application/vnd.github.v3.diff",
        ).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"diff fetch failed: {exc}") from exc
    return str(meta.get("title") or ""), str(meta.get("body") or ""), diff


def parse_unified_diff(diff_text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # diff --git a/path b/path
            parts = line.split()
            path = parts[-1][2:] if len(parts) >= 4 else "unknown"
            current = FileDiff(path=path, status="modified")
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("new file mode"):
            current.status = "added"
        elif line.startswith("deleted file mode"):
            current.status = "deleted"
        elif line.startswith("rename from"):
            current.status = "renamed"
        elif line.startswith("+") and not line.startswith("+++"):
            current.added += 1
            current.plus_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deleted += 1
    return files


def analyze(title: str, body: str, files: list[FileDiff]) -> tuple[list[Finding], str, list[str], list[str], str]:
    findings: list[Finding] = []
    risks: list[str] = []
    suggestions: list[str] = []

    total_added = sum(f.added for f in files)
    total_deleted = sum(f.deleted for f in files)
    paths = [f.path for f in files]
    has_tests = any(TEST_HINTS.search(p) for p in paths)
    has_docs = any(DOC_HINTS.search(p) for p in paths)
    code_files = [f for f in files if not DOC_HINTS.search(f.path) and f.status != "deleted"]

    if not files:
        findings.append(Finding("high", "empty", "Diff is empty — nothing to review"))
        risks.append("Empty diff; no verifiable change")
        suggestions.append("Confirm the PR ref and that the branch contains commits")
        conf = "Low"
        summary = "This PR appears empty or the diff could not be loaded."
        return findings, summary, risks, suggestions, conf

    # Secrets / risky patterns on added lines
    for f in files:
        for line in f.plus_lines:
            stripped = line.strip()
            # Skip pure pattern catalogs / allowlists common in security hooks
            is_pattern_def = bool(
                re.search(r"""(r['\"].*['\"]|re\.compile\(|patterns?\s*=|BLOCK|DENY)""", stripped)
            )
            for rx, msg in SECRET_PATTERNS:
                if rx.search(line):
                    findings.append(Finding("high", "secret", msg, f.path))
                    risks.append(f"{msg} in `{f.path}`")
            for rx, msg in RISKY_CODE:
                if rx.search(line):
                    if is_pattern_def and msg in {
                        "DROP TABLE in diff",
                        "Destructive rm -rf /",
                        "Use of eval()",
                        "Use of exec()",
                    }:
                        continue
                    findings.append(Finding("medium", "risky", msg, f.path))
                    risks.append(f"{msg} in `{f.path}`")

    if code_files and not has_tests:
        findings.append(Finding("medium", "tests", "No test files in the diff"))
        risks.append("No automated tests included with code changes")
        suggestions.append("Add unit tests covering happy path and 1–2 edge cases")

    if total_added > 800:
        findings.append(Finding("medium", "size", f"Large diff (+{total_added}/-{total_deleted})"))
        risks.append("Large change set increases review and regression risk")
        suggestions.append("Split into smaller focused PRs if possible")

    if not has_docs and any(f.status == "added" and f.path.endswith((".py", ".ts", ".js", ".go")) for f in files):
        suggestions.append("Add a short README or usage note for new entrypoints")

    # Title / body hygiene
    if not title.strip():
        suggestions.append("Add a descriptive PR title")
    if body and "test" not in body.lower() and code_files:
        suggestions.append("Document how reviewers can run tests in the PR body")

    # Language-specific light checks
    for f in files:
        joined = "\n".join(f.plus_lines)
        if f.path.endswith(".py"):
            if "except:" in joined or re.search(r"except\s+Exception\s*:\s*pass", joined):
                risks.append(f"Broad exception swallowing in `{f.path}`")
                suggestions.append(f"Narrow exception handlers in `{f.path}` and log failures")
            if "TODO" in joined or "FIXME" in joined:
                suggestions.append(f"Resolve or ticket TODO/FIXME markers in `{f.path}`")
        if f.path.endswith((".ts", ".tsx", ".js")):
            if "any)" in joined or ": any" in joined:
                suggestions.append(f"Reduce `any` usage in `{f.path}` for type safety")

    # Positive signals
    if has_tests:
        findings.append(Finding("info", "tests", "Test files present"))
    if has_docs:
        findings.append(Finding("info", "docs", "Documentation updated"))

    # Dedup risks/suggestions preserve order
    def uniq(xs: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    risks = uniq(risks)
    suggestions = uniq(suggestions)

    # Default suggestions if thin
    if not suggestions:
        suggestions.append("LGTM structure — consider adding a sample output for reviewers")
    if not risks:
        risks.append("No high-severity static issues detected in added lines (heuristic only)")

    # Confidence
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    if high:
        conf = "Low"
    elif medium >= 2 or total_added > 500:
        conf = "Medium"
    elif has_tests and total_added < 400:
        conf = "High"
    else:
        conf = "Medium"

    # Summary 2–3 sentences
    file_list = ", ".join(f"`{f.path}`" for f in files[:6])
    more = f" (+{len(files)-6} more)" if len(files) > 6 else ""
    summary = (
        f"This PR touches {len(files)} file(s) with +{total_added}/-{total_deleted} lines "
        f"({file_list}{more}). "
    )
    if high:
        summary += "Static analysis found high-severity concerns that should be resolved before merge. "
    elif medium:
        summary += "A few medium-risk items were flagged; overall intent looks coherent. "
    else:
        summary += "Heuristic review found no major red flags in the added lines. "
    summary += "This is a deterministic lexical/static review, not a full semantic proof of correctness."

    return findings, summary.strip(), risks, suggestions, conf


def optional_llm_enrich(markdown: str, title: str, diff_excerpt: str) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    # Keep optional and best-effort; never fail the CLI if API is down.
    try:
        payload = {
            "model": os.environ.get("CLAUDE_REVIEW_MODEL", "claude-sonnet-4-20250514"),
            "max_tokens": 800,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Refine this PR review. Keep the same section headings exactly: "
                        "## Summary, ## Risks, ## Suggestions, ## Confidence. "
                        "Be concise and concrete. Do not invent files not in the diff.\n\n"
                        f"PR title: {title}\n\nCurrent review:\n{markdown}\n\nDiff excerpt:\n"
                        f"{diff_excerpt[:12000]}"
                    ),
                }
            ],
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        parts = data.get("content") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        return text.strip() or None
    except Exception:
        return None


def render_markdown(
    title: str,
    pr_ref: str | None,
    summary: str,
    risks: list[str],
    suggestions: list[str],
    confidence: str,
    mode: str,
) -> str:
    lines = ["# PR Review", ""]
    if pr_ref:
        lines.append(f"**PR:** {pr_ref}")
    if title:
        lines.append(f"**Title:** {title}")
    lines.append(f"**Reviewer mode:** {mode}")
    lines.extend(["", "## Summary", summary, "", "## Risks"])
    for r in risks:
        lines.append(f"- {r}")
    lines.extend(["", "## Suggestions"])
    for s in suggestions:
        lines.append(f"- {s}")
    lines.extend(["", "## Confidence", confidence, ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="claude-review", description="Structured PR review CLI")
    parser.add_argument("--pr", help="GitHub PR URL or owner/repo#number")
    parser.add_argument("--diff", help="Path to unified diff file")
    parser.add_argument("--title", default="", help="PR title when using --diff")
    parser.add_argument("--body", default="", help="PR body when using --diff")
    parser.add_argument("-o", "--output", help="Write markdown to file")
    parser.add_argument("--json", action="store_true", help="Also emit machine-readable JSON to stderr")
    parser.add_argument("--no-llm", action="store_true", help="Disable optional Anthropic enrichment")
    args = parser.parse_args(argv)

    pr_ref = None
    title = args.title or ""
    body = args.body or ""
    diff_text = ""

    if args.pr:
        parsed = parse_pr_ref(args.pr)
        if not parsed:
            print("error: could not parse --pr (expected https://github.com/o/r/pull/N)", file=sys.stderr)
            return 2
        owner, repo, number = parsed
        pr_ref = f"https://github.com/{owner}/{repo}/pull/{number}"
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        try:
            title, body, diff_text = fetch_pr_via_gh(owner, repo, number)
        except Exception:
            try:
                title, body, diff_text = fetch_pr_via_api(owner, repo, number, token)
            except Exception as exc:
                print(f"error: failed to fetch PR: {exc}", file=sys.stderr)
                return 1
    elif args.diff:
        path = Path(args.diff)
        if not path.exists():
            print(f"error: diff not found: {path}", file=sys.stderr)
            return 2
        diff_text = path.read_text(encoding="utf-8", errors="replace")
        pr_ref = str(path)
    else:
        parser.print_help()
        return 2

    files = parse_unified_diff(diff_text)
    findings, summary, risks, suggestions, conf = analyze(title, body, files)
    mode = "heuristic"
    md = render_markdown(title, pr_ref, summary, risks, suggestions, conf, mode)

    if not args.no_llm:
        enriched = optional_llm_enrich(md, title, diff_text)
        if enriched and "## Summary" in enriched and "## Confidence" in enriched:
            md = enriched
            mode = "heuristic+llm"
            # ensure mode line if model dropped it
            if "Reviewer mode" not in md:
                md = md.replace("# PR Review", f"# PR Review\n\n**Reviewer mode:** {mode}", 1)

    if args.output:
        Path(args.output).write_text(md if md.endswith("\n") else md + "\n", encoding="utf-8")
    sys.stdout.write(md if md.endswith("\n") else md + "\n")

    if args.json:
        payload = {
            "pr": pr_ref,
            "title": title,
            "confidence": conf,
            "mode": mode,
            "risks": risks,
            "suggestions": suggestions,
            "findings": [f.__dict__ for f in findings],
            "files": [{"path": f.path, "status": f.status, "added": f.added, "deleted": f.deleted} for f in files],
        }
        sys.stderr.write(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
