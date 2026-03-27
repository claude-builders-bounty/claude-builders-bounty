# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

## Added Example Tool: PR Review Agent

This repo now includes a small Claude-powered PR review tool:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

It fetches the PR diff, asks Claude to review it, and outputs structured Markdown with:
- Summary
- Risks
- Suggestions
- Confidence

See also:
- `claude_review.py`
- `examples/pr1-review.md`
- `examples/pr2-review.md`
