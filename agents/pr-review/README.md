# PR Review Sub-Agent

A Claude Code sub-agent that reviews GitHub PRs and produces structured Markdown reviews.

## Features

- **CLI mode:** `node claude-review.mjs --pr <pr-url>`
- **Local mode:** `node claude-review.mjs --diff <file>`
- **GitHub Action mode:** Auto-reviews via included workflow
- **Structured output:** Summary, risks, suggestions, confidence score
- **Optional auto-posting as PR comment**

## Requirements

- Node.js v18+
- Claude Code CLI (`npm install -g @anthropic/claude-code`)
- GitHub token with `repo` scope

## Usage

```bash
export GITHUB_TOKEN=ghp_xxx
node claude-review.mjs --pr https://github.com/owner/repo/pull/123
node claude-review.mjs --diff /tmp/pr.diff
node claude-review.mjs --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Sample Output

### Summary of Changes
This PR adds a new user profile page with avatar upload support.

### Identified Risks
- File upload only checks extension, not MIME type
- No file size limit

### Improvement Suggestions
1. Add MIME type validation on server side
2. Set max file size (5MB)

### Confidence Score
**Medium**
