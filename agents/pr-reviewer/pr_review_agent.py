#!/usr/bin/env python3
"""
Claude Code PR review sub-agent.

Inspects git diff outputs and drafts an intelligent PR review summary
using an LLM API (Gemini or Groq). Outputs a structured PR_REVIEW.md file.

Usage:
    python3 pr_review_agent.py [--pr URL] [--base BRANCH] [--output FILE]
    python3 pr_review_agent.py --base main --output PR_REVIEW.md
    python3 pr_review_agent.py --pr https://github.com/owner/repo/pull/123

The agent:
1. Captures staged + unstaged git diffs
2. Slices diffs into logical chunks (per-file) to respect API token limits
3. Sends each chunk to an LLM API for structured code review
4. Aggregates findings into a professional PR_REVIEW.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ──────────────────────────────────────────────────────────────────── #
# Constants
# ──────────────────────────────────────────────────────────────────── #

# Maximum characters per diff chunk sent to the LLM API
# (keeps each request under ~4K tokens for the diff payload)
MAX_CHUNK_CHARS = 8000

# Maximum total diff characters before truncation kicks in
MAX_TOTAL_DIFF_CHARS = 50000

# LLM API endpoints
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

REVIEW_PROMPT = """You are a senior code reviewer. Analyze the following git diff and provide a structured code review.

For each file, identify:
1. **Critical issues** — bugs, security vulnerabilities, or breaking changes
2. **Suggestions** — improvements to readability, performance, or maintainability
3. **Positive notes** — well-implemented patterns or good practices

Be concise. Use bullet points. Focus on actionable feedback.

Git diff:
```diff
{diff_chunk}
```

Respond in this exact format:
### File: {filename}
**Critical Issues:**
- (list or "None found")

**Suggestions:**
- (list or "None")

**Positive Notes:**
- (list or "None")
"""


# ──────────────────────────────────────────────────────────────────── #
# Data classes
# ──────────────────────────────────────────────────────────────────── #

@dataclass
class DiffChunk:
    """A single file's diff, sliced to fit API token limits."""
    filename: str
    content: str
    is_truncated: bool = False


@dataclass
class ReviewResult:
    """The review result for a single file."""
    filename: str
    review_text: str
    error: str | None = None


# ──────────────────────────────────────────────────────────────────── #
# Git diff capture
# ──────────────────────────────────────────────────────────────────── #

def get_git_diff(repo_path: str = ".", base_branch: str | None = None) -> str:
    """Capture git diff (staged + unstaged, or against a base branch).

    Args:
        repo_path: Path to the git repository.
        base_branch: If provided, diff against this branch (e.g., "main").
                     If None, captures staged + unstaged changes.

    Returns:
        Raw git diff output as a string.
    """
    if base_branch:
        cmd = ["git", "-C", repo_path, "diff", f"{base_branch}...HEAD"]
    else:
        cmd = ["git", "-C", repo_path, "diff", "HEAD"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        result.check_returncode()
        return result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"Error getting git diff: {exc}", file=sys.stderr)
        return ""


def parse_diff_into_chunks(diff_output: str, max_chunk_chars: int = MAX_CHUNK_CHARS) -> list[DiffChunk]:
    """Parse a git diff into per-file chunks, truncating if needed.

    Args:
        diff_output: Raw git diff output.
        max_chunk_chars: Maximum characters per chunk.

    Returns:
        List of DiffChunk objects, one per file (or per file slice for large diffs).
    """
    if not diff_output.strip():
        return []

    chunks: list[DiffChunk] = []
    # Split by "diff --git" to separate files
    file_diffs = diff_output.split("diff --git a/")
    for file_diff in file_diffs:
        if not file_diff.strip():
            continue

        # Extract filename from the first line: "path/to/file b/path/to/file"
        first_line = file_diff.split("\n")[0]
        # Parse: "path/to/file b/path/to/file\n..."
        parts = first_line.split(" b/")
        filename = parts[0].strip() if parts else "unknown"

        content = "diff --git a/" + file_diff

        # Truncate if too large
        is_truncated = False
        if len(content) > max_chunk_chars:
            content = content[:max_chunk_chars] + "\n... [truncated for API token limit] ...\n"
            is_truncated = True

        chunks.append(DiffChunk(filename=filename, content=content, is_truncated=is_truncated))

    return chunks


# ──────────────────────────────────────────────────────────────────── #
# LLM API integration
# ──────────────────────────────────────────────────────────────────── #

def call_gemini_api(diff_chunk: str, filename: str, api_key: str) -> str:
    """Call Gemini API for code review.

    Args:
        diff_chunk: The git diff content for this file.
        filename: The filename being reviewed.
        api_key: Gemini API key.

    Returns:
        The review text from the LLM.
    """
    import urllib.request

    prompt = REVIEW_PROMPT.format(diff_chunk=diff_chunk, filename=filename)
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
    }).encode()

    url = f"{GEMINI_URL}?key={api_key}"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return "Error: No response from Gemini API."
    except Exception as exc:
        return f"Error calling Gemini API: {exc}"


def call_groq_api(diff_chunk: str, filename: str, api_key: str) -> str:
    """Call Groq API for code review.

    Args:
        diff_chunk: The git diff content for this file.
        filename: The filename being reviewed.
        api_key: Groq API key.

    Returns:
        The review text from the LLM.
    """
    import urllib.request

    prompt = REVIEW_PROMPT.format(diff_chunk=diff_chunk, filename=filename)
    payload = json.dumps({
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a senior code reviewer providing structured PR feedback."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }).encode()

    req = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return "Error: No response from Groq API."
    except Exception as exc:
        return f"Error calling Groq API: {exc}"


def review_chunk(chunk: DiffChunk) -> ReviewResult:
    """Review a single diff chunk using the best available LLM API.

    Falls back gracefully: Gemini → Groq → static analysis.

    Args:
        chunk: The DiffChunk to review.

    Returns:
        ReviewResult with the review text or error.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if gemini_key:
        review_text = call_gemini_api(chunk.content, chunk.filename, gemini_key)
        return ReviewResult(filename=chunk.filename, review_text=review_text)

    if groq_key:
        review_text = call_groq_api(chunk.content, chunk.filename, groq_key)
        return ReviewResult(filename=chunk.filename, review_text=review_text)

    # No API keys — fall back to static analysis
    return ReviewResult(
        filename=chunk.filename,
        review_text=static_review(chunk),
    )


def static_review(chunk: DiffChunk) -> str:
    """Perform a basic static review without an LLM.

    Checks for common patterns: TODO/FIXME, hardcoded secrets, large additions.
    """
    lines = chunk.content.split("\n")
    added_lines = [line for line in lines if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line for line in lines if line.startswith("-") and not line.startswith("---")]

    findings: list[str] = []

    # Check for TODO/FIXME
    todos = [line for line in added_lines if "TODO" in line.upper() or "FIXME" in line.upper()]
    if todos:
        findings.append(f"- ⚠️ {len(todos)} TODO/FIXME comment(s) added")

    # Check for potential secrets
    secret_patterns = ["password", "secret", "api_key", "token", "private_key"]
    for pattern in secret_patterns:
        matches = [line for line in added_lines if pattern in line.lower() and "=" in line]
        if matches:
            findings.append(f"- 🔒 Potential hardcoded {pattern} detected")

    # Check for console/print statements
    prints = [line for line in added_lines if "console.log" in line or "print(" in line]
    if prints:
        findings.append(f"- 💡 {len(prints)} debug print/console.log statement(s) added")

    # Summary
    result = f"### File: {chunk.filename}\n"
    result += f"**Changes:** +{len(added_lines)} -{len(removed_lines)} lines\n\n"
    if findings:
        result += "**Automated Findings:**\n"
        result += "\n".join(findings)
    else:
        result += "**Automated Findings:**\n- No issues detected by static analysis"
    result += "\n\n**Note:** No LLM API key configured. Set GEMINI_API_KEY or GROQ_API_KEY for AI-powered review."

    if chunk.is_truncated:
        result += "\n\n⚠️ This diff was truncated due to size limits."

    return result


# ──────────────────────────────────────────────────────────────────── #
# Report generation
# ──────────────────────────────────────────────────────────────────── #

def generate_review_report(results: list[ReviewResult], pr_url: str | None = None) -> str:
    """Generate the final PR_REVIEW.md from individual file reviews."""
    lines: list[str] = [
        "# 📋 Pull Request Review",
        "",
        f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if pr_url:
        lines.append(f"**PR:** {pr_url}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Summary",
        "",
        f"- **Files reviewed:** {len(results)}",
        f"- **Files with errors:** {sum(1 for r in results if r.error)}",
        "",
        "---",
        "",
        "## Detailed Review",
        "",
    ])

    for result in results:
        lines.append(result.review_text)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────── #
# Main
# ──────────────────────────────────────────────────────────────────── #

def run_review(
    repo_path: str = ".",
    base_branch: str | None = None,
    pr_url: str | None = None,
    output_file: str = "PR_REVIEW.md",
) -> str:
    """Run the full PR review pipeline.

    Args:
        repo_path: Path to the git repository.
        base_branch: Base branch to diff against (e.g., "main").
        pr_url: Optional PR URL for the report header.
        output_file: Output file path for the review report.

    Returns:
        The generated review report content.
    """
    # 1. Capture git diff
    diff = get_git_diff(repo_path, base_branch)

    # 2. Truncate if too large
    if len(diff) > MAX_TOTAL_DIFF_CHARS:
        print(f"⚠️ Diff is {len(diff)} chars, truncating to {MAX_TOTAL_DIFF_CHARS}", file=sys.stderr)
        diff = diff[:MAX_TOTAL_DIFF_CHARS] + "\n... [diff truncated for token safety] ...\n"

    if not diff.strip():
        report = "# 📋 Pull Request Review\n\n*No changes detected.*\n"
        Path(output_file).write_text(report, encoding="utf-8")
        return report

    # 3. Parse into chunks
    chunks = parse_diff_into_chunks(diff)
    if not chunks:
        report = "# 📋 Pull Request Review\n\n*No file changes detected.*\n"
        Path(output_file).write_text(report, encoding="utf-8")
        return report

    # 4. Review each chunk
    results: list[ReviewResult] = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Reviewing {i}/{len(chunks)}: {chunk.filename}...", file=sys.stderr)
        result = review_chunk(chunk)
        results.append(result)

    # 5. Generate report
    report = generate_review_report(results, pr_url)

    # 6. Write output
    Path(output_file).write_text(report, encoding="utf-8")
    print(f"✅ PR_REVIEW.md generated ({len(report)} bytes)", file=sys.stderr)

    return report


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code PR review sub-agent. Analyzes git diffs and generates a structured review."
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository (default: current directory)")
    parser.add_argument("--base", default=None, help="Base branch to diff against (e.g., 'main')")
    parser.add_argument("--pr", default=None, help="PR URL for the report header")
    parser.add_argument("--output", default="PR_REVIEW.md", help="Output file (default: PR_REVIEW.md)")

    args = parser.parse_args()

    report = run_review(
        repo_path=args.repo,
        base_branch=args.base,
        pr_url=args.pr,
        output_file=args.output,
    )

    # Also print to stdout for CLI usage
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
