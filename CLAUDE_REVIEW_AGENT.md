# Claude PR Review Agent

This submission adds a claude-review CLI and a Claude Code sub-agent for producing structured Markdown PR reviews.

## Setup

    npm install
    npm link

No runtime dependencies are required. The CLI uses Node 20 built-in fetch.

## Usage

Review a pull request and print Markdown:

    claude-review --pr https://github.com/owner/repo/pull/123

Write the review to a file:

    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Post the review as a GitHub comment:

    GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post

By default the CLI tries claude -p when the Claude CLI is installed. If Claude is unavailable, it falls back to a deterministic local reviewer so the command still works in CI and smoke tests. Use --no-claude to force the deterministic path.

## Output Format

The review always uses:

- Summary
- Identified Risks
- Improvement Suggestions
- Confidence

## GitHub Action

.github/workflows/claude-review.yml shows how to run the reviewer automatically on PR events and post the resulting comment with GITHUB_TOKEN.

## Smoke Test

    npm run smoke

The smoke test reviews a real public GitHub PR using --no-claude, which avoids requiring a local Claude login for validation.

## Sample Output Verification

    npm test

The test command checks CLI syntax and verifies that both included real-PR sample outputs contain the required structured Markdown sections and a Low, Medium, or High confidence score.
