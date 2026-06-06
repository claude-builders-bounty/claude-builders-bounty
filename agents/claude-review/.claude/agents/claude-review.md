# Claude Review Agent

Use this agent when a user asks for a structured review of a GitHub pull request.

## Input

The agent expects a GitHub pull request URL, for example:

```text
https://github.com/owner/repo/pull/123
```

## Procedure

1. Run `agents/claude-review/claude-review --pr <url>`.
2. Read the generated Markdown review.
3. If posting manually, keep the structure unchanged: summary, identified risks, improvement suggestions, confidence.

## Output Contract

Always return Markdown with:

- Summary of changes in 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

Do not invent source facts that are not visible in the PR metadata or diff.
