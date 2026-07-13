"""Core review engine using Claude API."""

import json
from typing import Optional
from anthropic import Anthropic
from .github_client import PRInfo


SYSTEM_PROMPT = """You are an expert code reviewer. You analyze pull request diffs and provide structured, actionable reviews.

Your reviews must be thorough but concise. Focus on:
1. Understanding the overall intent and impact of the changes
2. Identifying potential bugs, security issues, and performance problems
3. Suggesting improvements to code quality, readability, and maintainability
4. Assessing the confidence level of your review

Output your review in the EXACT format specified by the user. Do not deviate from the structure."""


def build_review_prompt(pr: PRInfo, focus: Optional[str] = None) -> str:
    """Build the review prompt for Claude."""

    # Truncate diff if too large (keep it under ~100k chars for context window)
    diff = pr.diff
    truncated = False
    if len(diff) > 100_000:
        diff = diff[:100_000]
        truncated = True

    focus_instruction = ""
    if focus:
        focus_map = {
            "security": "Pay special attention to security vulnerabilities: injection attacks, auth issues, data exposure, insecure defaults, etc.",
            "performance": "Pay special attention to performance issues: N+1 queries, unnecessary allocations, algorithmic complexity, caching opportunities, etc.",
            "style": "Pay special attention to code style: naming conventions, consistency, readability, documentation, best practices for the language, etc.",
            "bugs": "Pay special attention to potential bugs: edge cases, null/undefined handling, race conditions, error handling, etc.",
            "architecture": "Pay special attention to architectural concerns: coupling, cohesion, separation of concerns, extensibility, design patterns, etc.",
        }
        focus_instruction = f"\n\n**Review Focus**: {focus_map.get(focus, focus)}"

    prompt = f"""Review this GitHub Pull Request and provide a structured analysis.

## PR Information
- **Title**: {pr.title}
- **Author**: {pr.author}
- **Repository**: {pr.owner}/{pr.repo}
- **Branch**: {pr.head_branch} → {pr.base_branch}
- **Stats**: +{pr.additions} / -{pr.deletions} across {pr.changed_files} file(s)
- **PR Description**:
{pr.body or "(No description provided)"}

## Changed Files
{_format_file_list(pr.files)}

## Diff
```diff
{diff}
```
{"(Note: Diff was truncated due to size)" if truncated else ""}
{focus_instruction}

## Required Output Format

Produce your review in this EXACT structure:

### 📋 Summary
(2-3 sentences describing what this PR does and its overall quality)

### ⚠️ Identified Risks
(Bulleted list of potential risks, bugs, or concerns. If none found, say "No significant risks identified.")

### 💡 Improvement Suggestions
(Bulleted list of actionable suggestions. If the code is already good, suggest minor polish or say "No major improvements needed.")

### 📊 Confidence Score
(One of: **Low** / **Medium** / **High** — with a brief explanation)

Confidence meanings:
- **High**: Clear, well-scoped changes that are easy to reason about
- **Medium**: Some complexity or areas that need careful testing
- **Low**: Large/complex changes, unclear intent, or areas outside typical review scope

### 📁 File-by-File Notes
(Brief notes on key files changed, if applicable. Skip trivial changes.)"""

    return prompt


def _format_file_list(files: list) -> str:
    """Format the file list for the prompt."""
    if not files:
        return "(No files)"
    lines = []
    for f in files:
        status_emoji = {
            "added": "🆕",
            "modified": "📝",
            "removed": "🗑️",
            "renamed": "📛",
        }.get(f["status"], "📄")
        lines.append(
            f"- {status_emoji} `{f['filename']}` ({f['status']}: +{f['additions']}/-{f['deletions']})"
        )
    return "\n".join(lines)


class Reviewer:
    """Claude-powered PR reviewer."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def review(
        self,
        pr: PRInfo,
        focus: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """Generate a structured review for the given PR.

        Returns the review as a Markdown string.
        """
        prompt = build_review_prompt(pr, focus=focus)

        if verbose:
            import sys
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"🔍 Sending {len(prompt):,} chars to Claude ({self.model})...", file=sys.stderr)
            print(f"   PR: {pr.owner}/{pr.repo}#{pr.number}", file=sys.stderr)
            print(f"   Files: {pr.changed_files}, +{pr.additions}/-{pr.deletions}", file=sys.stderr)
            if focus:
                print(f"   Focus: {focus}", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        review_text = message.content[0].text

        if verbose:
            print(f"\n✅ Review generated ({message.usage.input_tokens} input, {message.usage.output_tokens} output tokens)", file=sys.stderr)

        return review_text

    def review_to_json(self, pr: PRInfo, review_md: str) -> dict:
        """Convert a Markdown review to structured JSON."""
        import re

        result = {
            "pr": {
                "url": pr.url or f"https://github.com/{pr.owner}/{pr.repo}/pull/{pr.number}",
                "title": pr.title,
                "author": pr.author,
                "repository": f"{pr.owner}/{pr.repo}",
                "branch": f"{pr.head_branch} → {pr.base_branch}",
                "stats": {
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                },
            },
            "review": {
                "summary": "",
                "risks": [],
                "suggestions": [],
                "confidence": "",
                "file_notes": [],
            },
            "metadata": {
                "model": self.model,
                "version": "1.0.0",
            },
        }

        # Parse sections from markdown
        sections = re.split(r"###\s+", review_md)
        for section in sections:
            section = section.strip()
            lower = section.lower()

            if lower.startswith("📋") or lower.startswith("summary"):
                result["review"]["summary"] = _extract_section_body(section)

            elif lower.startswith("⚠️") or lower.startswith("identified risks") or "risk" in lower[:30]:
                result["review"]["risks"] = _extract_bullet_items(section)

            elif lower.startswith("💡") or lower.startswith("improvement") or "suggestion" in lower[:30]:
                result["review"]["suggestions"] = _extract_bullet_items(section)

            elif lower.startswith("📊") or lower.startswith("confidence") or "confidence" in lower[:30]:
                body = _extract_section_body(section)
                result["review"]["confidence"] = body

            elif lower.startswith("📁") or lower.startswith("file") or "file-by-file" in lower[:30]:
                result["review"]["file_notes"] = _extract_bullet_items(section)

        return result


def _extract_section_body(section: str) -> str:
    """Extract body text after the section header line."""
    lines = section.split("\n", 1)
    if len(lines) > 1:
        return lines[1].strip()
    return ""


def _extract_bullet_items(section: str) -> list[str]:
    """Extract bullet list items from a section."""
    import re
    items = []
    for line in section.split("\n"):
        line = line.strip()
        if re.match(r"^[-*•]\s+", line):
            items.append(re.sub(r"^[-*•]\s+", "", line))
    return items
