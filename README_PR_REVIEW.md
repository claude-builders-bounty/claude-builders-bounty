# PR Review Agent

A Claude Code agent that takes a GitHub PR diff, analyzes it, and returns a structured Markdown review comment.

## Acceptance Criteria

- CLI: `python pr_review_agent.py --pr <owner/repo/number|PR URL>`
- GitHub Action included: `.github/workflows/pr-review.yml` triggered by `/opire try` comment
- Structured Markdown output with summary, risks, improvements, and confidence score

## Usage

```
# CLI
python pr_review_agent.py --pr moorcheh-ai/memanto/791

# GitHub Action
# Comment "/opire try" on the issue; the workflow will post the structured review.
```

## Output Format

- Summary of changes (2-3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High
