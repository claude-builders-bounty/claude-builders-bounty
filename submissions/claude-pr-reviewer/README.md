# claude-review 🤖

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown reviews.

## Features

- **PR Analysis**: Fetches and analyzes diffs from any public GitHub PR
- **Risk Detection**: Identifies console statements, TODOs, potential secret leaks, large changes
- **Code Quality**: Flags missing error handling, magic numbers, type safety issues
- **Structured Output**: Summary, risks, suggestions, and confidence score
- **CI/CD Ready**: CLI tool + GitHub Action included

## Quick Start

```bash
# Install
npm install -g claude-review

# Review a PR
export GITHUB_TOKEN=ghp_...
claude-review --pr https://github.com/owner/repo/pull/123
```

## CLI Usage

```bash
claude-review --pr <pr-url>      # Review a GitHub PR
claude-review --diff <file>      # Review a local diff file
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token (required for --pr) |

## GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Run claude-review
        run: npx claude-review --pr "${{ github.event.pull_request.html_url }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Example Output

```
## 🔍 PR Review

### Summary

This review covers **3** file(s) changed · **+142** / **-38** lines · **2** risk(s) identified · **4** improvement suggestion(s).

### Files Changed

| File | Language | Changes |
|------|----------|--------:|
| `src/api/users.ts` | TypeScript | +67/-12 |
| `src/components/Header.tsx` | TypeScript React | +45/-20 |
| `src/utils/helpers.ts` | TypeScript | +30/-6 |

### ⚠️ Identified Risks

- Console statement found — remove or replace with proper logging before merge
- Unresolved TODO markers present

### 💡 Improvement Suggestions

- Prefer textContent over innerHTML to avoid XSS
- Consider testing the new API handlers
- Extract magic numbers (4 found) into named constants

### ✅ Confidence Score

**82%** — High
```

## How It Works

1. **Fetch**: Gets the PR diff from GitHub API
2. **Parse**: Splits into individual file changes
3. **Analyze**: Scans each file for patterns indicating risks or quality issues
4. **Report**: Generates structured Markdown with findings

## Development

```bash
git clone https://github.com/promptpolish-ai/claude-review
cd claude-review
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

## Testing on Real PRs

The tool has been tested on:
- [xevrion-v2/agent-playground #873](https://github.com/xevrion-v2/agent-playground/pull/873) — Adding JSDoc to route handlers
- [xevrion-v2/agent-playground #874](https://github.com/xevrion-v2/agent-playground/pull/874) — Fixing README typos

## License

MIT
