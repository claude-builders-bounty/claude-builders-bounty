# PR review agent

Usage:

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

The CLI fetches the PR diff with GitHub CLI and returns a structured Markdown review comment containing summary, identified risks, improvement suggestions, and confidence score.

A GitHub Action workflow is included for automatic PR comments.
