"""Core review logic for the Claude PR Review Agent."""

import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class ReviewResult:
    """Structured result from a PR review."""

    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low, Medium, High
    raw_response: str


class ClaudeReviewer:
    """Reviews PR diffs using the Claude API."""

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

    def _build_prompt(self, diff: str) -> str:
        """Build the review prompt for Claude."""
        return f"""You are an expert code reviewer. Analyze the following PR diff and provide a structured review.

Focus on:
- Understanding the intent and impact of the changes
- Identifying potential bugs, security issues, or performance problems
- Suggesting improvements for code quality, maintainability, and best practices
- Assessing the overall risk level of the changes

Respond in the following exact format:

## Summary
[2-3 sentence summary of the changes]

## Risks
- [Risk 1]
- [Risk 2]
- [Risk 3 or "None identified"]

## Suggestions
- [Suggestion 1]
- [Suggestion 2]
- [Suggestion 3 or "None"]

## Confidence
[Low / Medium / High]

Here is the PR diff to review:

