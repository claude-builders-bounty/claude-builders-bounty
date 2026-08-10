"""claude-review: LLM-powered GitHub PR reviewer.

Fetches a PR diff, sends it to a chat LLM (OpenAI-compatible API, e.g. DeepSeek),
and produces a structured Markdown review with:
  - Summary of changes (2-3 sentences)
  - Identified risks (list, with severity)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReviewResult:
    """Structured review output."""

    summary: str = ""
    risks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "Medium"
    raw: str = ""
    error: str = ""

    def to_markdown(self, pr_url: str = "", pr_title: str = "") -> str:
        lines = ["## 🤖 claude-review\n"]
        if pr_url:
            lines.append(f"**PR:** {pr_url}")
        if pr_title:
            lines.append(f"**Title:** {pr_title}")
        lines.append("")
        if self.error:
            lines.append(f"> ⚠️ Review failed: {self.error}\n")
            return "\n".join(lines)
        lines.append(f"### Summary\n{self.summary}\n")
        lines.append("### Identified Risks\n")
        if self.risks:
            for r in self.risks:
                lines.append(f"- {r}")
        else:
            lines.append("- None identified")
        lines.append("\n### Improvement Suggestions\n")
        if self.suggestions:
            for s in self.suggestions:
                lines.append(f"- {s}")
        else:
            lines.append("- None")
        lines.append(f"\n**Confidence:** {self.confidence}\n")
        return "\n".join(lines)


_SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review of a GitHub Pull Request diff.

Analyze the diff and return a JSON object with EXACTLY these keys (no markdown, no prose outside the JSON):
{
  "summary": "2-3 sentences summarizing what the PR changes and why",
  "risks": ["list of concrete risks with severity prefix, e.g. [HIGH] X / [MED] Y / [LOW] Z; focus on real bugs, security issues, performance problems, logic errors — not style"],
  "suggestions": ["list of actionable improvement suggestions tied to specific code"],
  "confidence": "Low" | "Medium" | "High"
}

Rules:
- Only report risks you can actually see in the diff. Do not invent issues.
- Distinguish [HIGH] (bug/security/data loss), [MED] (edge case/error handling), [LOW] (style/refactor).
- If the diff is trivial (docs, config), say so honestly in summary and use few or no risks.
- Never mention that you are an AI or that this is automated."""


def _llm_call(diff_text: str, base_url: str | None, api_key: str | None,
              model: str | None, timeout: int = 120) -> dict[str, Any]:
    """Call an OpenAI-compatible chat API. Falls back to env vars."""
    base_url = base_url or os.environ.get("CLAUDE_REVIEW_BASE_URL", "https://api.deepseek.com/v1")
    api_key = api_key or os.environ.get("CLAUDE_REVIEW_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    model = model or os.environ.get("CLAUDE_REVIEW_MODEL", "deepseek-chat")
    if not api_key:
        raise RuntimeError(
            "No API key. Set DEEPSEEK_API_KEY / CLAUDE_REVIEW_API_KEY, "
            "or pass --api-key. The LLM backend is required for semantic review."
        )

    # cap diff size to protect token budget (≈ 12k tokens)
    diff_for_llm = diff_text[:40000]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this PR diff:\n\n```diff\n{diff_for_llm}\n```"},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    import json as _json
    import urllib.request

    body = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    # no-proxy: local/CN API endpoints must not go through system proxy
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        data = _json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return _parse_json(content)


def _parse_json(content: str) -> dict[str, Any]:
    """Tolerantly parse LLM JSON output (strip markdown fences if present)."""
    content = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.S)
    if fence:
        content = fence.group(1)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # try extracting first {...} block
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def review_diff(diff_text: str, base_url: str | None = None, api_key: str | None = None,
                model: str | None = None) -> ReviewResult:
    """Analyze a PR diff and return a structured ReviewResult."""
    try:
        data = _llm_call(diff_text, base_url, api_key, model)
    except Exception as e:  # noqa: BLE001
        return ReviewResult(error=f"{type(e).__name__}: {e}")
    risks = data.get("risks") or []
    suggestions = data.get("suggestions") or []
    return ReviewResult(
        summary=str(data.get("summary", "")).strip(),
        risks=[str(x) for x in risks],
        suggestions=[str(x) for x in suggestions],
        confidence=str(data.get("confidence", "Medium")),
        raw=json.dumps(data, ensure_ascii=False),
    )
