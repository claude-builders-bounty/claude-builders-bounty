# Claude Code Agent: PR Reviewer

Use this agent when asked to review a GitHub pull request and produce a
structured Markdown comment.

## Input

The user provides a PR URL:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Workflow

1. Run `python bin/claude-review --pr <PR URL>` from this repository.
2. Read the generated Markdown.
3. If the user asks to post it, paste the Markdown as the PR comment.
4. If posting is not requested, return the Markdown directly.

## Review Contract

The output must include:

- `Summary`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence: Low`, `Confidence: Medium`, or `Confidence: High`

Do not approve code automatically. This agent surfaces risks and suggestions;
the human reviewer still decides whether to merge.
