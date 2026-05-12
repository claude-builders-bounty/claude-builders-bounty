---
name: pr-reviewer
description: Expert PR reviewer that analyzes GitHub PR diffs and provides a structured Markdown review. Use when a user provides a GitHub PR URL and needs a detailed review of changes, risks, and improvement suggestions.
---

# PR Reviewer Skill

This skill allows Gemini CLI to act as a senior software engineer reviewing a pull request. It fetches the diff from a provided GitHub PR URL, analyzes the changes, and returns a structured review comment.

## Quick Start

1. Provide the GitHub PR URL:
   `Review this PR: https://github.com/owner/repo/pull/123`

2. The skill will fetch the diff and generate a review.

## Review Structure

The review must follow this exact Markdown structure:

### Summary of Changes
- A 2–3 sentence high-level overview of what the PR accomplishes.

### Identified Risks
- **[Severity] Risk Title**: Description of the risk (e.g., performance impact, security vulnerability, regression potential).

### Improvement Suggestions
- **Suggestion Title**: Clear, actionable advice on how to improve the code (e.g., refactoring, naming, better error handling).

### Confidence Score
- **Score**: Low / Medium / High
- **Rationale**: Briefly explain why this score was given.

## Implementation Details

The skill uses a helper script to fetch the diff:
- `scripts/fetch_pr_diff.cjs <PR_URL>`

## Workflow

1.  **Fetch Diff**: Run `node scripts/fetch_pr_diff.cjs <PR_URL>` to get the raw diff.
2.  **Analyze**:
    - Identify logic changes.
    - Check for adherence to coding standards.
    - Look for potential bugs or edge cases.
    - Evaluate test coverage (if tests are included in the diff).
3.  **Generate Output**: Produce the structured Markdown report described above.
