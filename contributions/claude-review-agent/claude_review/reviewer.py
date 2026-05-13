"""Core review logic using Claude API."""

import os
from dataclasses import dataclass
from typing import Optional

import anthropic

from .github_client import PRData


@dataclass
class ReviewResult:
    """Structured review output."""
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low / Medium / High
    raw_response: str


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following pull request and provide a structured review.

## PR Information
- **Title:** {title}
- **Author:** {author}
- **Branch:** {head_branch} → {base_branch}
- **Files Changed:** {files_changed} | +{additions} / -{deletions}

## PR Description
{body}

## Diff
```diff
{diff}
```

## Instructions
Provide your review in EXACTLY this format (no deviations):

### Summary
Write 2-3 sentences summarizing what this PR does and its overall quality.

### Risks
List specific risks or potential issues. Be concrete, reference file names and line numbers where applicable. If no significant risks, say "No significant risks identified."

- Risk 1
- Risk 2

### Suggestions
List actionable improvement suggestions. Be specific and helpful.

- Suggestion 1
- Suggestion 2

### Confidence
State exactly one of: **Low** / **Medium** / **High**

Base confidence on:
- High: Clear, well-tested changes with obvious intent
- Medium: Reasonable changes but some ambiguity or missing tests
- Low: Complex changes, unclear intent, or insufficient context
"""

# Truncate very large diffs to stay within context limits
MAX_DIFF_CHARS = 80_000


class Reviewer:
    """PR reviewer powered by Claude."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        # Support custom API endpoints (proxies, relays)
        kwargs = {
            "api_key": api_key or os.environ.get("ANTHROPIC_API_KEY"),
        }
        if base_url or os.environ.get("ANTHROPIC_BASE_URL"):
            kwargs["base_url"] = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        self.client = anthropic.Anthropic(**kwargs)

    def review(self, pr: PRData) -> ReviewResult:
        """Analyze a PR and return structured review."""
        diff = pr.diff
        if len(diff) > MAX_DIFF_CHARS:
            diff = diff[:MAX_DIFF_CHARS] + "\n\n... [diff truncated for length] ..."

        prompt = REVIEW_PROMPT.format(
            title=pr.title,
            author=pr.author,
            head_branch=pr.head_branch,
            base_branch=pr.base_branch,
            files_changed=pr.files_changed,
            additions=pr.additions,
            deletions=pr.deletions,
            body=pr.body or "(No description provided)",
            diff=diff,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text
        return self._parse_response(raw)

    def _parse_response(self, text: str) -> ReviewResult:
        """Parse Claude's response into structured fields."""
        sections = {"summary": "", "risks": [], "suggestions": [], "confidence": "Medium"}

        current_section = None
        lines = text.strip().split("\n")

        for line in lines:
            lower = line.lower().strip()
            if lower.startswith("### summary"):
                current_section = "summary"
                continue
            elif lower.startswith("### risks") or lower.startswith("### risk"):
                current_section = "risks"
                continue
            elif lower.startswith("### suggestion"):
                current_section = "suggestions"
                continue
            elif lower.startswith("### confidence"):
                current_section = "confidence"
                continue

            if current_section == "summary":
                if line.strip():
                    sections["summary"] += line.strip() + " "
            elif current_section == "risks":
                if line.strip().startswith("- "):
                    sections["risks"].append(line.strip()[2:])
                elif line.strip().startswith("* "):
                    sections["risks"].append(line.strip()[2:])
            elif current_section == "suggestions":
                if line.strip().startswith("- "):
                    sections["suggestions"].append(line.strip()[2:])
                elif line.strip().startswith("* "):
                    sections["suggestions"].append(line.strip()[2:])
            elif current_section == "confidence":
                if "high" in lower:
                    sections["confidence"] = "High"
                elif "low" in lower:
                    sections["confidence"] = "Low"
                elif "medium" in lower:
                    sections["confidence"] = "Medium"

        return ReviewResult(
            summary=sections["summary"].strip(),
            risks=sections["risks"] or ["No significant risks identified."],
            suggestions=sections["suggestions"] or ["No suggestions — looks good!"],
            confidence=sections["confidence"],
            raw_response=text,
        )
