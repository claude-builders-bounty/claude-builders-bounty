# Claude PR Reviewer

This submission adds a Claude Code sub-agent and CLI that review a GitHub pull request and produce a structured Markdown comment.

## Files

- `claude-review`: CLI entrypoint
- `.claude/agents/pr-reviewer.md`: project-level Claude Code sub-agent
- `tools/claude_review.py`: GitHub fetch + Claude API review generator
- `samples/`: generated review outputs for real pull requests

## Setup

1. Export credentials: `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`
2. Optionally export `ANTHROPIC_BASE_URL` if you use a compatible gateway
3. Make the CLI executable: `chmod +x ./claude-review`
4. Run it: `./claude-review --pr https://github.com/owner/repo/pull/123`
5. Optionally post the generated review back to GitHub: `./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment`

## Usage

Generate a review to stdout:

```bash
./claude-review --pr https://github.com/expressjs/express/pull/7150
```

Write the review to a file:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/919 --output samples/sample-review-claude-builders-919.md
```

Post the generated review as a pull request comment:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1028 --post-comment
```

Use the Claude Code sub-agent:

```text
Use the pr-reviewer subagent to review https://github.com/expressjs/express/pull/7150
```

## Output format

Each generated review contains:

- `Summary`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence`

## Validation

- `python3 -m unittest discover -s tests -v`
- `./claude-review --pr https://github.com/expressjs/express/pull/7150 --output samples/sample-review-express-7150.md`
- `./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/919 --output samples/sample-review-claude-builders-919.md`
- `./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1028 --post-comment`
