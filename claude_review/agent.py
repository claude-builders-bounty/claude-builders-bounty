#!/usr/bin/env python3
"""Claude Code PR Review Agent.

Analyzes a PR diff using Claude and produces a structured Markdown review comment.
Can be run via CLI or as a GitHub Action.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

import anthropic


@dataclass
class ReviewResult:
    """Structured PR review result."""
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low, Medium, High
    raw_response: str


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following PR diff and provide a structured review.

PR URL: {pr_url}

DIFF:
