# Claude Code PR Reviewer Agent

A lightweight automated sub-agent and CLI tool that analyzes pull request diffs and generates structured Markdown code reviews with risk assessments and improvement recommendations.

## CLI Usage
Run directly from terminal by passing any GitHub Pull Request URL:
```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Or analyze a local diff file:
```bash
git diff main...HEAD > my_feature.diff
python agents/pr-reviewer/claude_review.py --diff my_feature.diff --output review.md
```

## GitHub Action Setup
Copy `agents/pr-reviewer/pr-review.yml` into your repository's `.github/workflows/` directory. The action will automatically run on every opened or synchronized pull request and post a structured review comment.

## Verification & Unit Testing
Run the comprehensive test suite verifying risk heuristics, diff parsing, and structured markdown outputs:
```bash
python agents/pr-reviewer/test_claude_review.py
```

## Sample Reviews
- [Sample 1: Review of PR #5241](samples/sample_review_1.md)
- [Sample 2: Review of PR #5242](samples/sample_review_2.md)
