"""
Main Review Orchestrator for Claude Review Agent.
Coordinates fetching diffs, invoking reviewers, and returning or posting reviews.
"""

import sys
import os
from typing import Optional, Dict, Any, Tuple
try:
    from .github_client import parse_pr_url, fetch_pr_diff, fetch_pr_metadata, post_pr_comment
    from .llm_providers import generate_llm_review
except (ImportError, ValueError):
    from github_client import parse_pr_url, fetch_pr_diff, fetch_pr_metadata, post_pr_comment
    from llm_providers import generate_llm_review


class ClaudeReviewer:
    """Orchestrates pull request analysis and comment generation."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        provider: str = "auto",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.provider = provider
        self.api_key = api_key
        self.model = model

    def review_pr(self, pr_url_or_ref: str, post_comment: bool = False) -> Tuple[str, Optional[str]]:
        """
        Reviews a pull request by URL or reference.
        Returns: (markdown_review, comment_url_or_none)
        """
        owner, repo, pr_number = parse_pr_url(pr_url_or_ref)
        diff_text = fetch_pr_diff(owner, repo, pr_number, token=self.github_token)

        meta = fetch_pr_metadata(owner, repo, pr_number, token=self.github_token)
        pr_title = meta.get("title", "")
        pr_body = meta.get("body", "")

        review_markdown = generate_llm_review(
            diff_text=diff_text,
            pr_title=pr_title,
            pr_body=pr_body,
            provider=self.provider,
            api_key=self.api_key,
            model=self.model
        )

        comment_url = None
        if post_comment:
            comment_url = post_pr_comment(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                comment_body=review_markdown,
                token=self.github_token
            )

        return review_markdown, comment_url

    def review_diff_text(self, diff_text: str, title: str = "Local Changeset") -> str:
        """Reviews raw diff content directly from file or stdin."""
        return generate_llm_review(
            diff_text=diff_text,
            pr_title=title,
            pr_body="",
            provider=self.provider,
            api_key=self.api_key,
            model=self.model
        )
