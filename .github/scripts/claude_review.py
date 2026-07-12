#!/usr/bin/env python3
"""
Claude Code PR Review Agent

Analyzes a PR diff using Claude and posts a structured Markdown review comment.
Can be used via CLI or GitHub Actions.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional

import requests

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class ReviewResult:
    summary: str
    risks: List[str]
    suggestions: List[str]
    confidence: str


class ClaudeReviewer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_diff(self, diff_content: str, pr_url: str) -> ReviewResult:
        """Send the diff to Claude and get structured review."""
        prompt = self._build_prompt(diff_content, pr_url)
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return self._parse_response(response.content[0].text)

    def _build_prompt(self, diff_content: str, pr_url: str) -> str:
        return f"""You are an expert code reviewer. Analyze the following PR diff and provide a structured review.

PR URL: {pr_url}

Diff:
