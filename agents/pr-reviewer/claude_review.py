#!/usr/bin/env python3
"""claude-review — generate a structured Markdown review for a GitHub PR.

Modes
-----
- ``--mode hybrid`` (default): heuristic findings + LLM-polished prose.
  Falls back to ``heuristic`` if no ``ANTHROPIC_API_KEY`` is set.
- ``--mode heuristic``: deterministic, no API calls.
- ``--mode llm``: LLM-only (skip heuristics). Requires ``ANTHROPIC_API_KEY``.

Outputs
-------
- ``stdout``: Markdown review (default).
- ``--output path.md``: write Markdown to a file.
- ``--json``: emit a structured JSON envelope (for tooling).
- ``--post``: upsert the review as a single bot comment on the PR.

Usage
-----
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr ... --mode heuristic --output review.md
    claude-review --pr ... --post                     # requires GITHUB_TOKEN
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

REVIEW_MARKER = "<!-- claude-review-bot:do-not-remove -->"
USER_AGENT = "claude-review/1.0 (+github.com/claude-builders-bounty)"
DEFAULT_MODEL = "claude-sonnet-4-6"
GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class FileChange:
    path: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    additions: int
    deletions: int
    patch: str
    added_lines: list[tuple[int, str]] = field(default_factory=list)
    removed_lines: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class Finding:
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    category: str
    message: str
    file: str | None = None
    line: int | None = None


@dataclass
class PRContext:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base_sha: str
    head_sha: str
    files: list[FileChange]

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"

    @property
    def total_additions(self) -> int:
        return sum(f.additions for f in self.files)

    @property
    def total_deletions(self) -> int:
        return sum(f.deletions for f in self.files)


# ---------------------------------------------------------------------------
# GitHub fetch
# ---------------------------------------------------------------------------

_PR_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<num>\d+)/?"
)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = _PR_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"Not a GitHub PR URL: {url!r}")
    return m["owner"], m["repo"], int(m["num"])


def _gh_request(path: str, token: str | None, accept: str = "application/vnd.github+json") -> bytes:
    url = GITHUB_API + path if path.startswith("/") else path
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_pr(owner: str, repo: str, number: int, token: str | None) -> PRContext:
    pr_json = json.loads(_gh_request(f"/repos/{owner}/{repo}/pulls/{number}", token))

    files: list[FileChange] = []
    page = 1
    while True:
        page_json = json.loads(
            _gh_request(
                f"/repos/{owner}/{repo}/pulls/{number}/files?per_page=100&page={page}",
                token,
            )
        )
        if not page_json:
            break
        for f in page_json:
            patch = f.get("patch") or ""
            added, removed = _split_patch_lines(patch)
            files.append(
                FileChange(
                    path=f["filename"],
                    status=f["status"],
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                    patch=patch,
                    added_lines=added,
                    removed_lines=removed,
                )
            )
        if len(page_json) < 100:
            break
        page += 1

    return PRContext(
        owner=owner,
        repo=repo,
        number=number,
        title=pr_json["title"],
        body=pr_json.get("body") or "",
        author=(pr_json.get("user") or {}).get("login", "unknown"),
        base_sha=pr_json["base"]["sha"],
        head_sha=pr_json["head"]["sha"],
        files=files,
    )


def _split_patch_lines(patch: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Yield (line_number_in_new_file, content) for + and - lines.

    Removed lines carry the line number they had in the *old* file.
    """
    added: list[tuple[int, str]] = []
    removed: list[tuple[int, str]] = []
    new_lineno = 0
    old_lineno = 0
    for raw in patch.splitlines():
        if raw.startswith("@@"):
            m = re.search(r"-(\d+)(?:,\d+)? \+(\d+)(?:,\d+)?", raw)
            if m:
                old_lineno = int(m.group(1)) - 1
                new_lineno = int(m.group(2)) - 1
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            new_lineno += 1
            added.append((new_lineno, raw[1:]))
        elif raw.startswith("-"):
            old_lineno += 1
            removed.append((old_lineno, raw[1:]))
        else:
            new_lineno += 1
            old_lineno += 1
    return added, removed


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    (re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}"), "potential hardcoded secret"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI-style API key literal"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub personal access token literal"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key literal"),
]

_DEBUG_PATTERNS = [
    (re.compile(r"\bconsole\.log\b"), "debug `console.log` left in code"),
    (re.compile(r"^\s*print\("), "debug `print(` left in code"),
    (re.compile(r"\bdebugger\b"), "`debugger` statement left in code"),
    (re.compile(r"\bbinding\.pry\b"), "`binding.pry` left in code"),
]

_DANGER_PATTERNS = [
    (re.compile(r"\beval\s*\("), "`eval(` is unsafe — review carefully"),
    (re.compile(r"\bexec\s*\("), "`exec(` is unsafe — review carefully"),
    (re.compile(r"\bdangerouslySetInnerHTML\b"), "`dangerouslySetInnerHTML` — XSS risk if input is not sanitized"),
    (re.compile(r"\bos\.system\s*\("), "`os.system(` — prefer `subprocess` with arg list"),
    (re.compile(r"\bsubprocess\.\w+\s*\([^)]*shell\s*=\s*True"), "`shell=True` — command-injection risk"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "SQL `DROP TABLE` — verify migration is reversible"),
    (re.compile(r"\bTRUNCATE\b", re.I), "SQL `TRUNCATE` — verify intent"),
    (re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;).)*(?:;|$)", re.I | re.S), "`DELETE FROM` without `WHERE`"),
]

_TODO_PATTERNS = [
    (re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b"), "TODO/FIXME marker introduced"),
]

# Line endings that hint at debug or dev-only output
_DEV_FILE_HINTS = {"node_modules", ".env.local", ".vscode", "__pycache__", ".idea"}

# Where tests live by language convention
_TEST_DIRS = ("tests/", "test/", "spec/", "__tests__/", "_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", ".test.js")
_SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".php", ".cs"}
_CONFIG_FILES = {"package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "composer.json", "Gemfile"}


def _is_test_path(path: str) -> bool:
    p = path.lower()
    return any(p.startswith(d) or p.endswith(d) or f"/{d}" in p for d in _TEST_DIRS)


def _is_source_path(path: str) -> bool:
    if _is_test_path(path):
        return False
    return any(path.endswith(ext) for ext in _SOURCE_EXTS)


def run_heuristics(ctx: PRContext) -> list[Finding]:
    findings: list[Finding] = []
    source_files_changed = 0
    test_files_changed = 0
    config_changed: list[str] = []
    binary_or_huge: list[str] = []

    for fc in ctx.files:
        if _is_test_path(fc.path):
            test_files_changed += 1
        elif _is_source_path(fc.path):
            source_files_changed += 1
        if fc.path.split("/")[-1] in _CONFIG_FILES:
            config_changed.append(fc.path)

        if any(hint in fc.path for hint in _DEV_FILE_HINTS):
            findings.append(
                Finding(
                    severity="medium",
                    category="hygiene",
                    message=f"`{fc.path}` looks like dev-only output committed by accident",
                    file=fc.path,
                )
            )

        if fc.additions + fc.deletions > 1000:
            binary_or_huge.append(fc.path)

        # Per-line scans on added lines only
        for lineno, content in fc.added_lines:
            for pat, msg in _SECRET_PATTERNS:
                if pat.search(content):
                    findings.append(
                        Finding(
                            severity="critical",
                            category="security",
                            message=msg,
                            file=fc.path,
                            line=lineno,
                        )
                    )
            for pat, msg in _DANGER_PATTERNS:
                if pat.search(content):
                    findings.append(
                        Finding(
                            severity="high",
                            category="risk",
                            message=msg,
                            file=fc.path,
                            line=lineno,
                        )
                    )
            for pat, msg in _DEBUG_PATTERNS:
                if pat.search(content):
                    findings.append(
                        Finding(
                            severity="low",
                            category="hygiene",
                            message=msg,
                            file=fc.path,
                            line=lineno,
                        )
                    )
            for pat, msg in _TODO_PATTERNS:
                if pat.search(content):
                    findings.append(
                        Finding(
                            severity="info",
                            category="hygiene",
                            message=msg,
                            file=fc.path,
                            line=lineno,
                        )
                    )

    if source_files_changed > 0 and test_files_changed == 0 and ctx.total_additions > 30:
        findings.append(
            Finding(
                severity="medium",
                category="testing",
                message=(
                    f"{source_files_changed} source file(s) changed but no test files touched. "
                    "Consider adding or updating tests."
                ),
            )
        )

    if config_changed:
        findings.append(
            Finding(
                severity="info",
                category="dependencies",
                message=(
                    "Dependency / config files changed: "
                    + ", ".join(f"`{p}`" for p in config_changed)
                    + ". Verify lockfiles are up to date and CI matrix still passes."
                ),
            )
        )

    if binary_or_huge:
        findings.append(
            Finding(
                severity="medium",
                category="size",
                message=(
                    "Very large files in this PR (>1000 line delta): "
                    + ", ".join(f"`{p}`" for p in binary_or_huge)
                    + ". Consider whether they belong (vendored bundles, generated code) or could ship separately."
                ),
            )
        )

    if ctx.total_additions + ctx.total_deletions > 800:
        findings.append(
            Finding(
                severity="medium",
                category="size",
                message=(
                    f"Large diff ({ctx.total_additions}+ / {ctx.total_deletions}- across {len(ctx.files)} files). "
                    "Splitting into smaller PRs makes review faster and rollback safer."
                ),
            )
        )

    if not ctx.body.strip():
        findings.append(
            Finding(
                severity="low",
                category="docs",
                message="PR description is empty. Add context (motivation, screenshots, test plan) to speed up review.",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def confidence_score(ctx: PRContext, findings: list[Finding]) -> tuple[float, str]:
    """Return (numeric 0..1, label High/Medium/Low).

    Principled formula: start at 0.9, deduct for size, risk density, missing
    context. Bounded to [0.05, 0.95].
    """
    score = 0.9

    # Size penalty
    delta = ctx.total_additions + ctx.total_deletions
    if delta > 1500:
        score -= 0.45
    elif delta > 500:
        score -= 0.25
    elif delta > 150:
        score -= 0.1

    # Risk density
    crit = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    score -= 0.25 * min(crit, 3)
    score -= 0.1 * min(high, 4)

    # Context
    if not ctx.body.strip():
        score -= 0.1

    score = max(0.05, min(0.95, score))

    if score >= 0.7:
        label = "High"
    elif score >= 0.4:
        label = "Medium"
    else:
        label = "Low"
    return score, label


# ---------------------------------------------------------------------------
# LLM (optional)
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are a senior code reviewer producing a Markdown review for a GitHub
    pull request. Your job is to write a tight, useful review that a busy
    maintainer can act on. Avoid praise theater; be specific and concrete.

    Output format (Markdown), in this order, no preamble:

    1. **Summary** — 2-3 sentences on what changed and the apparent intent.
    2. **Risks** — bullet list. Each bullet: one risk, max 1-2 lines, cite
       file:line where applicable.
    3. **Suggestions** — bullet list of concrete, copy-pasteable improvements.
       Cite file:line where applicable.
    4. **Confidence** — one line. State the level (High/Medium/Low) and the
       single biggest reason driving it.

    Rules:
    - Never invent code that isn't in the diff.
    - Never claim something is "looking good" without specifics.
    - If a heuristic finding is wrong on this diff, say so explicitly.
    - Keep total length under 400 words. Tight beats thorough.
    """
).strip()


def llm_review(ctx: PRContext, findings: list[Finding], api_key: str, model: str = DEFAULT_MODEL) -> str:
    """Call Anthropic API; return Markdown review body or raise on failure.

    Uses prompt caching on the system prompt so repeated reviews share the
    cache. Stdlib HTTP client to keep this script dependency-free.
    """
    diff_text = _compact_diff(ctx, max_chars=80_000)
    findings_block = "\n".join(
        f"- [{f.severity}] {f.category}: {f.message}"
        + (f" ({f.file}{':' + str(f.line) if f.line else ''})" if f.file else "")
        for f in findings
    ) or "(no heuristic findings)"

    user_prompt = textwrap.dedent(
        f"""\
        PR: {ctx.url}
        Title: {ctx.title}
        Author: @{ctx.author}
        Files changed: {len(ctx.files)}  Additions: +{ctx.total_additions}  Deletions: -{ctx.total_deletions}

        PR description:
        {ctx.body or '(empty)'}

        Heuristic findings (you may use, refine, or dismiss these):
        {findings_block}

        Unified diff (truncated to fit context):
        ```diff
        {diff_text}
        ```
        """
    ).strip()

    body = {
        "model": model,
        "max_tokens": 1500,
        "system": [
            {"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": [{"role": "user", "content": user_prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    return text.strip()


def _compact_diff(ctx: PRContext, max_chars: int) -> str:
    chunks = []
    for fc in ctx.files:
        header = f"diff --git a/{fc.path} b/{fc.path}\nstatus: {fc.status}  +{fc.additions}/-{fc.deletions}\n"
        chunks.append(header + fc.patch)
    full = "\n".join(chunks)
    if len(full) <= max_chars:
        return full
    return full[: max_chars - 80] + "\n\n[…diff truncated to fit context…]"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


_SEVERITY_EMOJI = {
    "critical": "🚨",
    "high": "⚠️",
    "medium": "🟡",
    "low": "🔵",
    "info": "ℹ️",
}


def render_markdown(
    ctx: PRContext,
    findings: list[Finding],
    confidence_label: str,
    confidence_score_value: float,
    llm_body: str | None,
    mode: str,
) -> str:
    lines: list[str] = []
    lines.append(REVIEW_MARKER)
    lines.append(f"## Claude Review — {ctx.title}")
    lines.append("")
    lines.append(
        f"**PR:** [#{ctx.number}]({ctx.url}) by @{ctx.author} · "
        f"**Files:** {len(ctx.files)} · **Diff:** +{ctx.total_additions} / -{ctx.total_deletions} · "
        f"**Mode:** `{mode}`"
    )
    lines.append("")

    if llm_body:
        lines.append(llm_body.strip())
        lines.append("")
    else:
        lines.append("### Summary")
        lines.append(_render_summary(ctx, findings))
        lines.append("")
        lines.append("### Risks")
        risks = [f for f in findings if f.severity in ("critical", "high", "medium")]
        if risks:
            for f in risks:
                lines.append(_render_finding(f))
        else:
            lines.append("_No high-severity heuristic findings._")
        lines.append("")
        lines.append("### Suggestions")
        suggestions = [f for f in findings if f.severity in ("low", "info")]
        if suggestions:
            for f in suggestions:
                lines.append(_render_finding(f))
        else:
            lines.append("_No housekeeping suggestions from heuristics._")
        lines.append("")
        lines.append(
            f"### Confidence: **{confidence_label}** ({confidence_score_value:.0%})"
        )
        lines.append(_render_confidence_reason(ctx, findings))

    lines.append("")
    lines.append(
        f"---\n_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by "
        f"[claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)._"
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_finding(f: Finding) -> str:
    emoji = _SEVERITY_EMOJI.get(f.severity, "•")
    cite = ""
    if f.file:
        cite = f" — `{f.file}`" + (f":{f.line}" if f.line else "")
    return f"- {emoji} **{f.category}** — {f.message}{cite}"


def _render_summary(ctx: PRContext, findings: list[Finding]) -> str:
    crit = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    delta = ctx.total_additions + ctx.total_deletions
    pieces = [f"Changes {len(ctx.files)} file(s) with a {delta}-line delta."]
    if crit:
        pieces.append(f"⚠️  {crit} critical finding(s) — block-merge worthy.")
    elif high:
        pieces.append(f"{high} high-severity finding(s) to address.")
    if ctx.body.strip():
        first_line = ctx.body.strip().splitlines()[0][:140]
        pieces.append(f"PR description leads with: _{first_line}_")
    return " ".join(pieces)


def _render_confidence_reason(ctx: PRContext, findings: list[Finding]) -> str:
    delta = ctx.total_additions + ctx.total_deletions
    if delta > 1500:
        return "Large diff is the dominant uncertainty driver."
    crit = sum(1 for f in findings if f.severity == "critical")
    if crit:
        return f"{crit} critical heuristic finding(s) raise the bar before merge."
    if not ctx.body.strip():
        return "Missing PR description reduces context for review."
    return "Diff is well-scoped and no critical patterns detected."


# ---------------------------------------------------------------------------
# Post / upsert PR comment
# ---------------------------------------------------------------------------


def upsert_review_comment(ctx: PRContext, body: str, token: str) -> dict:
    """Find the existing claude-review comment (by hidden marker) and edit it
    in place; otherwise create a new comment. Returns the GitHub comment JSON."""
    existing_id = _find_existing_comment(ctx, token)
    payload = json.dumps({"body": body}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if existing_id is not None:
        url = f"{GITHUB_API}/repos/{ctx.owner}/{ctx.repo}/issues/comments/{existing_id}"
        method = "PATCH"
    else:
        url = f"{GITHUB_API}/repos/{ctx.owner}/{ctx.repo}/issues/{ctx.number}/comments"
        method = "POST"
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _find_existing_comment(ctx: PRContext, token: str) -> int | None:
    page = 1
    while True:
        data = json.loads(
            _gh_request(
                f"/repos/{ctx.owner}/{ctx.repo}/issues/{ctx.number}/comments?per_page=100&page={page}",
                token,
            )
        )
        if not data:
            return None
        for c in data:
            if REVIEW_MARKER in (c.get("body") or ""):
                return c["id"]
        if len(data) < 100:
            return None
        page += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_github_token(arg: str | None) -> str | None:
    if arg:
        return arg
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    # Fall back to gh CLI if installed
    try:
        out = subprocess.check_output(["gh", "auth", "token"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip() or None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="claude-review", description=__doc__.split("\n\n")[0])
    p.add_argument("--pr", required=True, help="Full GitHub PR URL")
    p.add_argument("--mode", choices=("hybrid", "heuristic", "llm"), default="hybrid")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model id (LLM modes only)")
    p.add_argument("--output", help="Write Markdown to this path (also still prints unless --quiet)")
    p.add_argument("--json", action="store_true", help="Emit a JSON envelope instead of Markdown")
    p.add_argument("--post", action="store_true", help="Upsert the review as a PR comment")
    p.add_argument("--quiet", action="store_true", help="Suppress stdout when --output is set")
    p.add_argument("--github-token", help="GitHub API token (else env GITHUB_TOKEN / gh CLI)")
    p.add_argument("--anthropic-key", help="Anthropic API key (else env ANTHROPIC_API_KEY)")
    args = p.parse_args(list(argv) if argv is not None else None)

    owner, repo, number = parse_pr_url(args.pr)
    gh_token = _resolve_github_token(args.github_token)
    anthropic_key = args.anthropic_key or os.environ.get("ANTHROPIC_API_KEY")

    ctx = fetch_pr(owner, repo, number, gh_token)
    findings = run_heuristics(ctx) if args.mode != "llm" else []
    score, label = confidence_score(ctx, findings)

    llm_body: str | None = None
    effective_mode = args.mode
    if args.mode in ("llm", "hybrid"):
        if not anthropic_key:
            if args.mode == "llm":
                sys.stderr.write(
                    "error: --mode llm requires ANTHROPIC_API_KEY (or --anthropic-key)\n"
                )
                return 2
            effective_mode = "heuristic"  # graceful fallback
        else:
            try:
                llm_body = llm_review(ctx, findings, anthropic_key, args.model)
            except urllib.error.HTTPError as exc:
                sys.stderr.write(
                    f"warning: Anthropic call failed ({exc.code}); falling back to heuristic mode\n"
                )
                effective_mode = "heuristic"
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(
                    f"warning: LLM error ({exc!r}); falling back to heuristic mode\n"
                )
                effective_mode = "heuristic"

    review_md = render_markdown(ctx, findings, label, score, llm_body, effective_mode)

    if args.json:
        envelope = {
            "pr": ctx.url,
            "title": ctx.title,
            "author": ctx.author,
            "stats": {
                "files": len(ctx.files),
                "additions": ctx.total_additions,
                "deletions": ctx.total_deletions,
            },
            "mode": effective_mode,
            "confidence": {"score": round(score, 2), "label": label},
            "findings": [f.__dict__ for f in findings],
            "markdown": review_md,
        }
        sys.stdout.write(json.dumps(envelope, indent=2))
    elif not (args.output and args.quiet):
        sys.stdout.write(review_md)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(review_md)

    if args.post:
        if not gh_token:
            sys.stderr.write(
                "error: --post requires a GitHub token (env GITHUB_TOKEN, --github-token, or `gh auth login`)\n"
            )
            return 2
        result = upsert_review_comment(ctx, review_md, gh_token)
        sys.stderr.write(f"posted: {result.get('html_url')}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
