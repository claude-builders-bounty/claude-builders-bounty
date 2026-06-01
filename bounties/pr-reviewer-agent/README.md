# Claude PR Review Agent

A CLI tool and GitHub Action that reviews pull requests using Claude and outputs structured markdown comments.

## Features

- Fetches PR diff and metadata from GitHub
- Analyzes changes with Claude (claude-sonnet-4-20250514)
- Outputs structured review with:
  - Summary (2-3 sentences)
  - Identified risks
  - Improvement suggestions
  - Confidence score (Low/Medium/High)

## CLI Usage

```bash
# Install
npm install
npm run build

# Run
ANTHROPIC_API_KEY=your-key claude-review --pr https://github.com/owner/repo/pull/123
```

### Options

- `--pr <url>`: GitHub PR URL to review (required)

### Environment Variables

- `ANTHROPIC_API_KEY`: Required. Your Anthropic API key
- `GITHUB_TOKEN`: Optional. For private repos or higher rate limits

## GitHub Action Usage

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: ./bounties/pr-reviewer-agent
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Output Format

```markdown
## PR Review

### Summary
Brief description of what the PR does.

### Identified Risks
- Risk 1
- Risk 2

### Suggestions
- Suggestion 1
- Suggestion 2

### Confidence: 🟢 High
```

## Sample Outputs

See the `samples/` directory for example review outputs from real PRs.

## License

MIT
