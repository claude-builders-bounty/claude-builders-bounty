# Claude Code PR Review Agent

Use this agent when asked to review a GitHub pull request and produce a structured comment.

Run:

```bash
python agents/claude-pr-review/claude-review.py --pr <pull-request-url>
```

The agent fetches PR metadata and changed files, then returns Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

It is intentionally read-only and does not post comments unless a human copies the output or wires it into a separate GitHub Action.
