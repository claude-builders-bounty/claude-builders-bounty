"""Claude Review Agent - A tool for analyzing GitHub PRs."""

__version__ = "1.0.0"
__author__ = "Claude Review Agent"

from .agent import PRReviewer, PRData, ReviewResult
from .formatter import format_review, format_review_compact

__all__ = [
    'PRReviewer',
    'PRData', 
    'ReviewResult',
    'format_review',
    'format_review_compact'
]
