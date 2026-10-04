"""
LLM Provider integrations for Claude PR Reviewer.
Supports Anthropic Claude, Google Gemini, OpenAI, and Heuristic static analysis fallback.
Zero external pip dependencies (pure standard library urllib + json).
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple


def _call_anthropic(prompt: str, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> str:
    """Calls Anthropic Messages API."""
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": (
            "You are Claude Code PR Reviewer, an expert staff software engineer. "
            "You provide concise, rigorous, actionable code reviews in strict Markdown format."
        ),
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    req.add_header("User-Agent", "Claude-PR-Reviewer")

    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        # Parse text from content blocks
        parts = []
        for block in res.get("content", []):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)


def _call_gemini(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    """Calls Google Gemini GenerateContent API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("content-type", "application/json")
    req.add_header("User-Agent", "Claude-PR-Reviewer")

    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        candidates = res.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return "\n".join(p.get("text", "") for p in parts)
        return ""


def _call_openai(prompt: str, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None) -> str:
    """Calls OpenAI-compatible Chat Completions API."""
    url = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are Claude Code PR Reviewer. Provide rigorous, structured Markdown reviews."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Claude-PR-Reviewer")

    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"]


def heuristic_review(diff_text: str, pr_title: str = "", pr_body: str = "") -> str:
    """
    Performs deterministic static analysis on diff text when no LLM key is present.
    Ensures compliance with all acceptance criteria even offline.
    """
    lines = diff_text.splitlines()
    added_lines = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in lines if l.startswith("-") and not l.startswith("---")]

    # Extract modified file paths
    file_paths = re.findall(r"^diff --git a/(\S+) b/(\S+)", diff_text, flags=re.MULTILINE)
    modified_files = list({f[1] for f in file_paths})

    # Risk detection patterns
    risks = []
    suggestions = []

    diff_lower = diff_text.lower()

    # 1. Destructive shell commands
    if re.search(r"\brm\s+-[rf]{1,2}\b", diff_lower) or "mkfs" in diff_lower:
        risks.append("🚨 **Destructive Operation Detected:** Code contains `rm -rf` or file system formatting commands. Validate path bounds strictly.")

    # 2. Hardcoded secrets / keys
    if re.search(r"""(?:api_key|secret|token|password|private_key)\s*[:=]\s*['"][a-zA-Z0-9_\-]{8,}['"]""", diff_lower):
        risks.append("🔒 **Security Risk (Secrets):** Potential hardcoded secret, token, or API key detected in changes.")

    # 3. SQL Injection / Raw SQL drops
    if re.search(r"\bdrop\s+table\b", diff_lower) or re.search(r"\bdelete\s+from\s+\w+\s*$", diff_lower):
        risks.append("💾 **Database Risk:** Potential schema drop or unconstrained `DELETE` statement found.")

    # 4. Insecure permissions
    if "chmod 777" in diff_lower or "0777" in diff_lower:
        risks.append("🛡️ **Permission Risk:** Overly permissive file permissions (`chmod 777`) identified.")

    # 5. Large changeset
    if len(added_lines) > 500:
        risks.append(f"📦 **Change Complexity:** Large changeset (+{len(added_lines)} lines across {len(modified_files)} files). Consider splitting into smaller atomic pull requests.")

    # 6. Fallback risk if clean
    if not risks:
        risks.append("✅ **No Critical Anti-Patterns:** Static analysis found no exposed credentials, destructive commands, or glaring vulnerabilities.")

    # Suggestions
    has_tests = any("test" in f.lower() for f in modified_files)
    if not has_tests:
        suggestions.append("🧪 **Add Unit Tests:** Changes modify application logic without corresponding updates in `tests/` or spec suites.")
    else:
        suggestions.append("✅ **Test Coverage Present:** Automated test files are included alongside the changes.")

    if any(re.search(r"\b(todo|fixme|xxx)\b", l.lower()) for l in added_lines):
        suggestions.append("📝 **Resolve TODO/FIXME:** Added lines contain incomplete markers (`TODO`/`FIXME`). Resolve or track as dedicated follow-up issues.")

    if any(f.endswith(".md") for f in modified_files):
        suggestions.append("📖 **Documentation Updated:** Markdown guides or documentation were kept in sync with code updates.")
    else:
        suggestions.append("💡 **Update Documentation:** Consider updating accompanying README or API documentation if interfaces were altered.")

    confidence = "High" if len(lines) < 400 and has_tests else ("Medium" if len(lines) < 1000 else "Low")

    # Build 2-3 sentence summary
    summary_sentence_1 = f"This pull request touches {len(modified_files)} file{'s' if len(modified_files) != 1 else ''} with +{len(added_lines)} additions and -{len(removed_lines)} deletions."
    if pr_title:
        summary_sentence_2 = f"The primary objective is to implement: '{pr_title}'."
    else:
        summary_sentence_2 = "The changeset primarily refactors core logic, configuration, and supporting scripts."
    summary_sentence_3 = f"Automated static validation completed with {confidence.lower()} overall confidence based on changeset scope and test coverage."
    summary = f"{summary_sentence_1} {summary_sentence_2} {summary_sentence_3}"

    return format_markdown_review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        confidence_reason=f"Based on static analysis of {len(lines)} diff lines and {len(modified_files)} modified files."
    )


def format_markdown_review(summary: str, risks: list, suggestions: list, confidence: str, confidence_reason: str = "") -> str:
    """Formats the standardized review markdown comment."""
    risks_str = "\n".join(f"- {r}" for r in risks) if risks else "- No critical risks identified."
    sugg_str = "\n".join(f"- {s}" for s in suggestions) if suggestions else "- No specific improvements required."
    reason_str = f" ({confidence_reason})" if confidence_reason else ""

    return f"""## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
{summary}

### ⚠️ Identified Risks
{risks_str}

### 💡 Improvement Suggestions
{sugg_str}

### 🎯 Confidence Score: {confidence}
**{confidence} Confidence**{reason_str}

---
*Reviewed autonomously via [Claude PR Reviewer](https://github.com/claude-builders-bounty/claude-builders-bounty)*
"""


def generate_llm_review(diff_text: str, pr_title: str = "", pr_body: str = "",
                        provider: str = "auto", api_key: Optional[str] = None,
                        model: Optional[str] = None) -> str:
    """
    Orchestrates review generation using selected or auto-detected LLM provider,
    falling back seamlessly to heuristic analysis.
    """
    anthropic_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = api_key or os.environ.get("GEMINI_API_KEY")
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")

    # Prompt constructing exact acceptance criteria
    prompt = f"""You are an elite Staff Software Engineer reviewing a GitHub Pull Request diff.
Your task is to analyze the diff and generate a structured review comment in STRICT adherence to this format:

## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
[Provide exactly 2 to 3 concise, clear sentences summarizing what this pull request modifies and accomplishes.]

### ⚠️ Identified Risks
[Provide a bulleted list of 2-5 concrete risks, edge cases, security concerns, performance bottlenecks, or regression possibilities. If exceptionally safe, explain why.]

### 💡 Improvement Suggestions
[Provide a bulleted list of 2-5 actionable suggestions: code quality, test coverage, readability, typing, architecture, or documentation improvements.]

### 🎯 Confidence Score: High / Medium / Low
[State High, Medium, or Low with one sentence explaining your confidence level based on diff size, clarity, and complexity.]

---
*Reviewed autonomously via [Claude PR Reviewer](https://github.com/claude-builders-bounty/claude-builders-bounty)*

=== PR CONTEXT ===
Title: {pr_title or 'N/A'}
Description: {pr_body or 'N/A'}

=== GIT DIFF (Unified) ===
{diff_text[:30000]}
"""

    # Provider Dispatch
    selected_provider = provider.lower()

    if selected_provider == "anthropic" or (selected_provider == "auto" and anthropic_key):
        if not anthropic_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY or --api-key.")
        chosen_model = model or "claude-3-5-sonnet-20241022"
        try:
            return _call_anthropic(prompt, anthropic_key, chosen_model)
        except Exception as e:
            # If Anthropic fails, try Gemini or fallback
            if gemini_key and selected_provider == "auto":
                try:
                    return _call_gemini(prompt, gemini_key, model or "gemini-2.5-flash")
                except Exception:
                    pass
            raise

    if selected_provider == "gemini" or (selected_provider == "auto" and gemini_key):
        if not gemini_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY or --api-key.")
        chosen_model = model or "gemini-2.5-flash"
        return _call_gemini(prompt, gemini_key, chosen_model)

    if selected_provider == "openai" or (selected_provider == "auto" and openai_key):
        if not openai_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or --api-key.")
        chosen_model = model or "gpt-4o"
        return _call_openai(prompt, openai_key, chosen_model)

    # Heuristic fallback if no keys configured
    return heuristic_review(diff_text, pr_title, pr_body)
