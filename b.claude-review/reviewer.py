#!/usr/bin/env python3
"""Claude Code PR Review Agent - Core Reviewer Module."""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class ReviewResult:
    """Structured PR review result."""
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low, Medium, High
    raw_response: str


class ClaudeReviewer:
    """Claude Code PR Review Agent."""

    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
    MAX_DIFF_LENGTH = 150000  # ~150KB max diff

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var."
            )

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        response = requests.post(
            self.CLAUDE_API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    def _extract_pr_info(self, pr_url: str) -> tuple[str, str, int]:
        """Extract owner, repo, and PR number from URL."""
        match = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
            pr_url,
        )
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        return match.group(1), match.group(2), int(match.group(3))

    def _fetch_pr_diff(self, pr_url: str) -> str:
        """Fetch PR diff from GitHub API."""
        owner, repo, pr_number = self._extract_pr_info(pr_url)

        # Try GitHub CLI first
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--repo", f"{owner}/{repo}", "--json", "diff"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            data = json.loads(result.stdout)
            if "diff" in data and data["diff"]:
                return data["diff"]
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback to GitHub API
        token = os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github.v3.diff",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text

    def _build_prompt(self, diff: str, pr_url: str) -> str:
        """Build the prompt for Claude."""
        # Truncate diff if too long
        if len(diff) > self.MAX_DIFF_LENGTH:
            diff = diff[:self.MAX_DIFF_LENGTH] + "\n\n[... diff truncated due to length ...]"

        return f"""You are an expert code reviewer. Analyze the following pull request diff and provide a structured review.

PR URL: {pr_url}

## Diff

