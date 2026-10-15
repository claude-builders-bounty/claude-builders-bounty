# claude-review — AI-Powered PR Review Agent

A Claude Code agent that reviews pull requests and posts structured Markdown comments.

## Setup

1. Install [GitHub CLI](https://cli.github.com/)
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/cli)
3. Make `claude-review` executable: `chmod +x scripts/claude-review`
4. Add to PATH or use directly

## Usage

```bash
./scripts/claude-review --pr https://github.com/owner/repo/pull/123
```

## Requirements

- `gh` CLI (authenticated)
- `claude` CLI (authenticated)
- `jq`

## Output Format

Each review includes:
- **Summary**: 2-3 sentence overview
- **Identified Risks**: Potential issues
- **Improvement Suggestions**: Actionable recommendations
- **Confidence Score**: Low / Medium / High

## Bounty

This implementation is for [Bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — $150 reward.
