# Claude PR Review Agent

`claude-review` generates a structured Markdown review from a GitHub PR diff.

## Setup

```bash
chmod +x agents/claude-review
agents/claude-review --pr https://github.com/owner/repo/pull/123
```

## Output

The review includes:

- 2-3 sentence summary of the PR diff
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Examples

Sample outputs are in `agents/samples/`.
