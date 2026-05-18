# Claude Code PR Review Agent

A Claude Code sub-agent that analyzes PRs and posts structured review comments.

## Features

- **CLI Interface**: `claude-review --pr <url>`
- **GitHub Action**: Automatic review on `/claude-review` command
- **Structured Output**: Summary, Risks, Suggestions, Confidence Score

## Installation

```bash
# Clone the repo
git clone https://github.com/17chemictech/claude-builders-bounty.git
cd claude-builders-bounty

# Install dependencies
pip install anthropic openai

# Install the agent
pip install -e tools/claude-review-agent/
```

## Configuration

Set your API key as an environment variable:

```bash
# For Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# For OpenAI (GPT-4)
export OPENAI_API_KEY="sk-..."

# Optional: Specify model
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"
```

## Usage

### CLI Mode

```bash
# Review a GitHub PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review from a local diff file
claude-review --diff ./my_changes.patch

# Post review as a comment on the PR
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

# Save review to a file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action Mode

Add this workflow to your repo at `.github/workflows/pr-review.yml`:

```yaml
name: Claude Code PR Review

on:
  issue_comment:
    types: [created]

jobs:
  review:
    if: github.event.comment.body == '/claude-review'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install anthropic
      - name: Run review
        run: |
          claude-review --pr "${{ github.event.issue.pull_request.url }}"
```

Then comment `/claude-review` on any PR to trigger the review.

## Output Format

```markdown
## Summary
[2-3 sentence summary of what the PR does]

## Risks
- [Risk 1]
- [Risk 2]
- ...

## Suggestions
- [Suggestion 1]
- [Suggestion 2]
- ...

## Confidence Score
[Low / Medium / High]

## Files Changed
- Total files: [N]
- Approximate lines added/removed: [+X/-Y]
```

## Examples

See `sample_outputs/` directory for example reviews on real PRs.

## License

MIT
