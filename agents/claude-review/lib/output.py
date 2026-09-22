"""LLM refine + markdown render + local diff loader."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from typing import List, Optional

from .github_io import FileChange, Review


def refine_with_claude(review: Review, files: List[FileChange]) -> Review:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return review

    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    patches = []
    for f in files[:20]:
        patches.append(f"### {f.path} ({f.status} +{f.additions}/-{f.deletions})\n```\n{f.patch[:4000]}\n```")
    prompt = (
        "You are a senior code reviewer. Given this PR metadata and diffs, "
        "return ONLY valid JSON with keys: summary (string, 2-3 sentences), "
        "risks (array of strings), suggestions (array of strings), "
        "confidence (one of Low, Medium, High).\n\n"
        f"Title: {review.title}\nURL: {review.url}\n"
        f"Heuristic draft summary: {review.summary}\n\n"
        + "\n".join(patches)
    )
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "claude-review/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return review
        parsed = json.loads(m.group(0))
        review.summary = str(parsed.get("summary") or review.summary)
        if isinstance(parsed.get("risks"), list) and parsed["risks"]:
            review.risks = [str(x) for x in parsed["risks"]][:8]
        if isinstance(parsed.get("suggestions"), list) and parsed["suggestions"]:
            review.suggestions = [str(x) for x in parsed["suggestions"]][:8]
        conf = str(parsed.get("confidence") or review.confidence).title()
        if conf in ("Low", "Medium", "High"):
            review.confidence = conf
        review.mode = "llm"
    except Exception as e:
        sys.stderr.write(f"[claude-review] LLM refine skipped: {e}\n")
    return review


def render_markdown(review: Review) -> str:
    lines = [
        f"# PR Review: {review.title}",
        "",
        f"**PR:** {review.url}  ",
        f"**Mode:** {review.mode}  ",
        f"**Confidence:** {review.confidence}",
        "",
        "## Summary of changes",
        "",
        review.summary,
        "",
        "## Identified risks",
        "",
    ]
    for r in review.risks:
        lines.append(f"- {r}")
    lines += ["", "## Improvement suggestions", ""]
    for s in review.suggestions:
        lines.append(f"- {s}")
    lines += [
        "",
        "## Files touched",
        "",
        "| File | Status | +/- |",
        "|------|--------|-----|",
    ]
    for f in review.files[:40]:
        lines.append(f"| `{f.path}` | {f.status} | +{f.additions}/-{f.deletions} |")
    if len(review.files) > 40:
        lines.append(f"| … | {len(review.files) - 40} more | |")
    lines.append("")
    return "\n".join(lines)


def load_diff_file(path: str) -> List[FileChange]:
    text = open(path, encoding="utf-8", errors="replace").read()
    files: List[FileChange] = []
    current: Optional[FileChange] = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            parts = line.split()
            name = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith("b/") else parts[-1]
            current = FileChange(path=name, status="modified", additions=0, deletions=0, patch="")
        elif current is not None:
            current.patch += line + "\n"
            if line.startswith("+") and not line.startswith("+++"):
                current.additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                current.deletions += 1
    if current:
        files.append(current)
    return files
