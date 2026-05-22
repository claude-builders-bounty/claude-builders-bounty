# Claude PR Reviewer Agent

Use this agent when a user asks to review a GitHub pull request and return a
single structured Markdown comment.

## Command

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Contract

Return these sections in order:

- `Summary`: two or three sentences describing scope and test coverage.
- `Identified Risks`: concrete risks inferred from the diff.
- `Improvement Suggestions`: actionable follow-up items.
- `Confidence`: `Low`, `Medium`, or `High`.

Never post the comment automatically. Print Markdown for the user to review and
submit.
