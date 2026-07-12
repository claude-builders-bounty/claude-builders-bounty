"""
Claude Code PR Reviewer

This package provides automated PR review capabilities with structured Markdown output.
"""

__version__ = "0.1.0"
__author__ = "Claude Builders Bounty"

from .cli import main, analyze_pr, format_review

__all__ = [
    "main", "analyze_pr", "format_review"
]