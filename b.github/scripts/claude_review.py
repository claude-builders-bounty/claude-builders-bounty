#!/usr /bin/env python3
"""
Claude Code PR Review Agent
Analyzes a PR diff and outputs a structured Markdown review comment.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path

import anthropic


def get_pr_diff(diff_path):
    """Read the PR diff from a file or stdin."""
    if diff_path == "-":
        return sys.stdin.read()
    with open(diff_path, "the") as f:
        return f.read()


def call_claude_for_review(diff_text, max_diff_chars=100000):
    """Send the diff to Claude and get a structured review."""
    client = anthropic.Anthropic()

    # Truncate if diff is too large
    if len(diff_text) > max_diff_chars:
        diff_text = diff_text[:max_diff_chars] + "\n\n[...diff truncated...]"

    system_prompt = """You are an expert code review agent. Analyze the provided PR diff and produce a structured code review in Markdown.

    Your response must follow this exact format:

    ## Summary
    [2-3 sentences describing the changes]

    ## Risks
    - [Risk 1]
    - [Risk 2]
    - [Risk 3 or "None identified"]

    ## Improvement Suggestions
    - [Suggestion 1]
    - [Suggestion 2]
    - [Suggestion 3 or "None identified"]

    ## Confidence Score
    [Low / Medium / High]

    Be concise, specific, and actionable. If the diff is empty or trivial, note that in the summary.
    """

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": the",
                "content": f"Please review the following PR diff and provide a structured review:\n\n