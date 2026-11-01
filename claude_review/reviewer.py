"""Core review logic: fetch a PR, analyze it, render a structured Markdown review."""

from __future__ import annotations

import os
import re
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Any

GITHUB_API = "https://api.github.com"


@dataclass
class FileChange:
    filename: str
    status: str  # added/modified/removed/renamed
    additions: int
    deletions: int
    patch: str = ""


@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base: str
    head: str
    files: list[FileChange] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"not a GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _gh(path: str, token: str | None = None) -> Any:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{GITHUB_API}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _gh_text(path: str, token: str | None = None, accept: str = "application/vnd.github.v3.diff") -> str:
    headers = {"Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{GITHUB_API}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def fetch_pr(url: str, token: str | None = None) -> PRInfo:
    owner, repo, number = parse_pr_url(url)
    meta = _gh(f"/repos/{owner}/{repo}/pulls/{number}", token)
    files_raw = _gh(f"/repos/{owner}/{repo}/pulls/{number}/files?per_page=100", token)
    files = [
        FileChange(
            filename=f["filename"],
            status=f.get("status", "modified"),
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
            patch=f.get("patch", ""),
        )
        for f in files_raw
    ]
    return PRInfo(
        owner=owner,
        repo=repo,
        number=number,
        title=meta.get("title", ""),
        body=meta.get("body") or "",
        author=(meta.get("user") or {}).get("login", ""),
        base=(meta.get("base") or {}).get("ref", ""),
        head=(meta.get("head") or {}).get("ref", ""),
        files=files,
        additions=meta.get("additions", 0),
        deletions=meta.get("deletions", 0),
        changed_files=meta.get("changed_files", 0),
    )


# ---------- heuristic analysis ----------

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "possible AWS access key"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "possible GitHub PAT"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "possible API secret key"),
    (re.compile(r"password\s*=\s*['\"][^'\"]{4,}['\"]", re.I), "hardcoded password"),
]

RISKY_PATHS = ("auth", "security", "crypto", "payment", "billing", "migration", "schema")


def _heuristic_review(pr: PRInfo) -> str:
    risks: list[str] = []
    suggestions: list[str] = []

    # Size
    if pr.changed_files > 20:
        risks.append(f"Large PR ({pr.changed_files} files, +{pr.additions}/-{pr.deletions}): review in smaller chunks.")
    if pr.deletions > pr.additions * 3 and pr.deletions > 50:
        risks.append("Heavy deletion relative to additions — confirm nothing critical was removed.")

    # Sensitive paths
    sensitive = [f.filename for f in pr.files if any(p in f.filename.lower() for p in RISKY_PATHS)]
    if sensitive:
        risks.append("Touches sensitive areas: " + ", ".join(f"`{p}`" for p in sensitive[:5]))

    # Tests
    has_tests = any("test" in f.filename.lower() or f.filename.startswith("tests/") for f in pr.files)
    has_code = any(not f.filename.endswith((".md", ".json", ".yml", ".yaml", ".txt", ".lock")) for f in pr.files)
    if has_code and not has_tests:
        suggestions.append("No test files in this PR — consider adding coverage for the changed logic.")

    # Secrets scan on patches
    for f in pr.files:
        for pat, label in SECRET_PATTERNS:
            if pat.search(f.patch or ""):
                risks.append(f"Possible secret in `{f.filename}`: {label}.")

    # Large single file
    for f in pr.files:
        if f.additions > 300:
            suggestions.append(f"`{f.filename}` has {f.additions} additions — consider splitting.")

    # Renames without content (noise)
    renames = [f for f in pr.files if f.status == "renamed"]
    if renames:
        suggestions.append(f"{len(renames)} file(s) renamed — verify imports/paths updated.")

    if not risks:
        risks.append("No obvious risks detected by heuristic scan.")
    if not suggestions:
        suggestions.append("No specific suggestions — looks clean.")

    # Confidence
    if pr.changed_files <= 5 and has_tests:
        confidence = "High"
    elif pr.changed_files <= 15:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Summary
    summary = (
        f"This PR by @{pr.author} modifies {pr.changed_files} file(s) "
        f"(+{pr.additions}/-{pr.deletions}) on `{pr.base}`. "
        f"Title: \"{pr.title}\"."
    )

    lines = [
        "## PR Review",
        "",
        f"**PR:** {pr.owner}/{pr.repo}#{pr.number}",
        f"**Author:** @{pr.author}",
        f"**Branch:** `{pr.head}` → `{pr.base}`",
        "",
        "### Summary",
        summary,
        "",
        "### Identified risks",
    ]
    for r in risks:
        lines.append(f"- {r}")
    lines += ["", "### Improvement suggestions"]
    for s in suggestions:
        lines.append(f"- {s}")
    lines += ["", f"### Confidence score: **{confidence}**", ""]
    lines.append("_Generated by claude-review (heuristic mode). Set OPENAI_API_KEY or ANTHROPIC_API_KEY for an LLM-enhanced review._")
    return "\n".join(lines)


def _llm_review(pr: PRInfo, provider: str) -> str | None:
    """Optional LLM-enhanced review. Returns None if unavailable."""
    try:
        import os as _os
        if provider == "openai":
            key = _os.environ.get("OPENAI_API_KEY")
            if not key:
                return None
            import urllib.request as _u
            # build prompt
            diff = "\n".join(f"### {f.filename}\n{f.patch[:1500]}" for f in pr.files[:10])
            prompt = (
                "You are a senior code reviewer. Review this PR and respond in Markdown with sections: "
                "Summary (2-3 sentences), Identified risks (list), Improvement suggestions (list), "
                "Confidence score (Low/Medium/High).\n\n"
                f"PR title: {pr.title}\nAuthor: {pr.author}\n"
                f"Files changed: {pr.changed_files} (+{pr.additions}/-{pr.deletions})\n\n"
                f"Diff (truncated):\n{diff}"
            )
            payload = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            )
            with _u.urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
            text = d["choices"][0]["message"]["content"]
            return text
        return None
    except Exception:
        return None


def review(pr: PRInfo, use_llm: bool = False) -> str:
    if use_llm:
        for prov in ("openai",):
            out = _llm_review(pr, prov)
            if out:
                header = (
                    f"## PR Review\n\n**PR:** {pr.owner}/{pr.repo}#{pr.number}\n"
                    f"**Author:** @{pr.author}\n\n"
                )
                return header + out
    return _heuristic_review(pr)
