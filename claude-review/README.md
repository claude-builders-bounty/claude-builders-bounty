# claude-review

A Claude Code sub-agent that reviews GitHub pull requests and produces structured Markdown feedback.

## Features

- Analyzes PR diffs using Claude Code's AI capabilities
- Outputs structured reviews with: Summary, Risks, Suggestions, and Confidence score
- Works as a CLI tool or GitHub Action
- Optionally posts the review directly as a PR comment

## Prerequisites

- Node.js >= 18
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- GitHub token (for private repos or posting comments)

## Setup

```bash
# Clone and install
cd claude-review
npm link

# Or use directly without installing
node bin/claude-review.js --pr <url>
```

## CLI Usage

```bash
# Basic review (prints to stdout)
claude-review --pr https://github.com/owner/repo/pull/123

# Post review as a PR comment
GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post

# URL can also be passed as a positional argument
claude-review https://github.com/owner/repo/pull/123
```

### Options

| Flag | Description |
|------|-------------|
| `--pr <url>` | GitHub PR URL to review |
| `--post` | Post the review as a comment on the PR |
| `-h, --help` | Show help |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token. Required for private repos and `--post` |

## GitHub Action Usage

Add this workflow to your repository at `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Run Claude Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd claude-review
          node bin/claude-review.js --pr "${{ github.event.pull_request.html_url }}" --post
```

Required secrets:
- `ANTHROPIC_API_KEY` — your Anthropic API key for Claude Code

## Output Format

The review follows a consistent structure:

```markdown
# 🤖 Claude Code Review

> Automated review of PR #123 — *PR title here*

## Summary
(2-3 sentences describing the changes)

## Risks
- Risk item 1
- Risk item 2

## Suggestions
- Suggestion 1
- Suggestion 2

## Confidence
**High**
```

Confidence levels:
- **High** — Clear, well-scoped changes that are straightforward to evaluate
- **Medium** — Moderate complexity or some missing context
- **Low** — Large diffs, unfamiliar domain, or insufficient context to fully assess

## Running Tests

```bash
npm test
```

## Sample Outputs

See the `sample-outputs/` directory for example reviews generated from real GitHub PRs:
- [react-pr-31827.md](sample-outputs/react-pr-31827.md) — React useId hydration fix
- [next-js-pr-58432.md](sample-outputs/next-js-pr-58432.md) — Next.js parallel route loading states

## License

MIT
