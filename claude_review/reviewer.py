#!/usr/bin/env python3
"""Claude Code PR Review Agent.

Takes a PR diff as input, analyzes it with Claude, and returns a structured
Markdown review comment.
"""

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
    """Structured review result."""
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str


class PRReviewer:
    """Claude Code PR Review Agent."""

    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

    def _extract_pr_info(self, pr_url: str) -> tuple[str, str, int]:
        """Extract owner, repo, and PR number from URL."""
        match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid PR URL: {pr_url}")
        return match.group(1), match.group(2), int(match.group(3))

    def _fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR diff from GitHub API."""
        token = os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review/0.1.0",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _fetch_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch PR files from GitHub API."""
        token = os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-review/0.1.0",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _analyze_with_claude(self, diff: str, files: list[dict]) -> ReviewResult:
        """Send diff to Claude API for analysis."""
        files_summary = "\n".join([
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in files[:20]  # Limit to first 20 files
        ])

        # Truncate diff if too large
        max_diff_length = 15000
        if len(diff) > max_diff_length:
            diff = diff[:max_diff_length] + "\n\n... (diff truncated for length)"

        prompt = f"""You are an expert code reviewer. Analyze the following PR diff and provide a structured review.

## Files Changed
{files_summary}

## Diff
