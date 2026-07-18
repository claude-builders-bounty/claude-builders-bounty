# Claude PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured feedback.

## CLI Usage

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Review any PR
./claude-review/claude-review --pr https://github.com/owner/repo/pull/123
```

## GitHub Action Setup

1. Add your `ANTHROPIC_API_KEY` to repo Secrets
2. Copy `.github/workflows/pr-review.yml` to your repo
3. PRs will be reviewed automatically

## Output Format

```
### Summary
(2-3 sentences)

### Identified Risks
- Risk 1
- Risk 2

### Improvement Suggestions
1. **Suggestion** — explanation

### Confidence Score
**High** — (reason)
```

## Requirements
- `bash`, `curl`, `python3`
- `ANTHROPIC_API_KEY` environment variable

## Example Outputs

Tested on real PRs — sample outputs included in PR #3465.
