# Claude Review Agent

An AI-powered GitHub PR review agent built with Claude.

## Overview

`claude-review` is a CLI tool that analyzes GitHub Pull Request diffs and generates structured Markdown review comments using Claude AI.

## Features

- 🔍 Fetches PR diff automatically from GitHub
- 🤖 AI-powered code analysis with Claude
- 📝 Structured Markdown output (Summary, Risks, Suggestions, Confidence)
- 💬 Optional auto-post to PR as comment
- 📁 Output to file or stdout

## Installation

```bash
# Clone the repository
git clone https://github.com/ZG361/claude-review-agent.git
cd claude-review-agent

# Install dependencies
npm install

# Link globally (optional)
npm link
```

## Usage

### Basic Usage

```bash
# Set required environment variables
export GH_TOKEN="your-github-token"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Run the review
claude-review --pr https://github.com/owner/repo/pull/123
```

### CLI Options

```
Usage: claude-review --pr <PR_URL> [options]

Options:
  --pr <url>       GitHub PR URL (required)
  --output <file>  Write output to file instead of stdout
  --post           Post the review as a PR comment (requires GH_TOKEN)
  --help, -h       Show this help message
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GH_TOKEN` | Yes | GitHub Personal Access Token |
| `ANTHROPIC_API_KEY` | Recommended | Anthropic API Key for Claude AI |

### Examples

```bash
# Basic review (prints to stdout)
claude-review --pr https://github.com/facebook/react/pull/12345

# Save review to file
claude-review --pr https://github.com/facebook/react/pull/12345 --output review.md

# Post review directly to PR
claude-review --pr https://github.com/facebook/react/pull/12345 --post
```

## Output Format

The review is structured as:

```markdown
## Summary
(2-3 sentences describing what the PR does)

## Risks
- Potential issue 1
- Potential issue 2

## Suggestions
- Improvement suggestion 1
- Improvement suggestion 2

## Confidence
Low / Medium / High
```

## Requirements

- Node.js 18+
- `gh` CLI (GitHub CLI) or curl
- GitHub Personal Access Token with `repo` scope
- Anthropic API Key (optional, enables full AI review)

## Sample Outputs

### Example 1: React PR Review

```markdown
## Summary
This PR introduces a new `useDeferredValue` hook that allows deferring expensive updates while showing old content. The implementation adds internal state management and scheduling logic to React's reconciliation process.

## Risks
- Memory leak potential if cleanup doesn't properly cancel scheduled updates
- Edge case with concurrent rendering may cause stale values
- Type definitions may need adjustment for strict TypeScript projects

## Suggestions
- Add comprehensive tests for cleanup scenarios
- Document the performance implications in the RFC
- Consider adding a `useDeferredValue` example to the docs

## Confidence
High
```

### Example 2: API Change PR Review

```markdown
## Summary
This PR modifies the authentication middleware to support JWT refresh tokens. It adds a new `/refresh` endpoint and updates the token validation logic to handle expired access tokens gracefully.

## Risks
- Breaking change: existing clients using only access tokens will need updates
- Security: refresh token storage needs proper encryption
- Race condition potential in concurrent refresh scenarios

## Suggestions
- Add migration guide for existing API consumers
- Implement token rotation for enhanced security
- Add integration tests for the refresh flow
- Consider rate limiting on the refresh endpoint

## Confidence
Medium
```

## GitHub Actions Integration

You can use this agent in a GitHub Action:

```yaml
name: AI PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          git clone https://github.com/ZG361/claude-review-agent.git
          cd claude-review-agent
          npm install
      
      - name: Run AI Review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd claude-review-agent
          node bin/claude-review.js --pr ${{ github.event.pull_request.html_url }} --post
```

## Development

```bash
# Run tests
npm test

# Run locally without linking
node bin/claude-review.js --pr <URL>
```

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines first.
