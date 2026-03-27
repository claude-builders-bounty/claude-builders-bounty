# Claude PR Review

CLI tool and GitHub Action that reviews pull requests with Claude and outputs structured Markdown feedback.

## CLI Usage

```bash
chmod +x review/claude-review.sh
./review/claude-review.sh --pr https://github.com/owner/repo/pull/123
```

Uses `claude` CLI if available, falls back to Anthropic API via `ANTHROPIC_API_KEY`.

## GitHub Action

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
      - uses: ./review
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

The action posts a structured review comment on the PR.

## Output Format

```markdown
## Summary
2-3 sentence description of changes.

## Risks
- Specific risks with file/line references

## Suggestions
- Actionable improvements

## Confidence
**Score: Low/Medium/High**
Justification.
```

## Requires

- `gh` (GitHub CLI, authenticated)
- `claude` CLI or `ANTHROPIC_API_KEY` env var
- `jq`
