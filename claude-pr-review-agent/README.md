# Claude PR Review Agent

A dependency-free Node.js CLI that reads a GitHub pull request and prints a structured Markdown review comment.

## Setup

```bash
chmod +x bin/claude-review.mjs
```

Optional, but recommended for higher GitHub API limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Usage

```bash
node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
node bin/claude-review.mjs --pr owner/repo#123 --out review.md
```

## Output Format

The CLI returns Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score
- Review metadata

## Example

```bash
node bin/claude-review.mjs --pr https://github.com/rtCamp/nginx-helper/pull/500 --out examples/nginx-helper-500.md
```

Second real PR example:

```bash
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2644 --out examples/claude-builders-bounty-2644.md
```

## Validation

The included examples were generated with:

```bash
node --check bin/claude-review.mjs
node bin/claude-review.mjs --help
node bin/claude-review.mjs --pr https://github.com/rtCamp/nginx-helper/pull/500 --out examples/nginx-helper-500.md
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2644 --out examples/claude-builders-bounty-2644.md
```

## Notes

This implementation uses GitHub's REST API and lightweight heuristic analysis so it can run without external packages. It can be extended later with a Claude API call, but the current version is intentionally portable and works as a CLI baseline.
