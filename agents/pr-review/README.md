# Claude Code PR Review Agent

Analyzes a GitHub PR diff and returns structured feedback in markdown.
Works both as a CLI tool and as a GitHub Action.

## CLI Usage

```bash
# Install: make the script executable (no deps beyond Python 3)
chmod +x claude_review.py

# Set your API keys
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Review a PR (output to stdout)
./claude_review.py --pr https://github.com/owner/repo/pull/123

# Review and post as a PR comment
./claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

## GitHub Action Usage

```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: your-org/your-repo/agents/pr-review@main
        with:
          pr-url: ${{ github.event.pull_request.html_url }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Output Format

```
## 🤖 Claude Review: PR Title

### Summary
2-3 sentences about what the PR does.

### Identified Risks
- risk: description
- risk: description

### Improvement Suggestions
- suggestion: description

### Confidence Score
**High** / **Medium** / **Low**
```

## Requirements

- Python 3.8+
- `ANTHROPIC_API_KEY` environment variable (required)
- `GITHUB_TOKEN` environment variable (recommended for API rate limits, required for `--post`)
