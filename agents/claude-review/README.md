# Claude Code PR Review Agent

A CLI agent and GitHub Action that analyzes pull requests and produces structured, actionable reviews.

## Features

- Fetches PR diff and metadata via GitHub API
- Detects hardcoded secrets, debug logging, permission changes
- Flags large files, missing error handling, new dependencies
- Generates a structured Markdown review with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score
  - File-by-file breakdown

## Usage

### CLI

```bash
# With GitHub token in env
export GITHUB_TOKEN=ghp_xxx
./claude-review --pr https://github.com/owner/repo/pull/123

# Or pass it directly
./claude-review --pr https://github.com/owner/repo/pull/123 --gh-token ghp_xxx
```

### GitHub Action

Create `.github/workflows/pr-review.yml`:

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
      - name: Run Claude Review
        uses: ./agents/claude-review
        with:
          gh-token: ${{ secrets.GITHUB_TOKEN }}
```

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CLAUDE CODE PR REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Summary

**PR:** owner/repo #123
**Title:** Fix login validation
**Changes:** 3 files | +45 / -12 lines

## Identified Risks

- ✅ No significant risks detected

## Improvement Suggestions

- Add tests for new validation logic
- Update documentation

## Confidence Score

**HIGH** — Small, focused PR

## Files Changed

- **src/auth.ts** (modified, +30/-5)
- **src/validation.ts** (modified, +15/-7)
```

## Requirements

- Bash 4+
- curl
- python3
- A [GitHub token](https://github.com/settings/tokens) with repo scope

## License

MIT
