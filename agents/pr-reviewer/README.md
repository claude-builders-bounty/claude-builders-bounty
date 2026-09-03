# Claude Code PR Reviewer Sub-Agent 🔍

An automated Pull Request reviewer that inspects diffs, audits for security & operational risks, detects missing tests, and delivers structured Markdown review comments.

## Usage

### 1. CLI Mode

```bash
# Review any public GitHub PR
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Review and automatically post review as a GitHub comment
export GITHUB_TOKEN="ghp_your_token_here"
python agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment
```

### 2. GitHub Actions Integration

Drop the workflow into `.github/workflows/claude-pr-review.yml`:

```yaml
name: Claude PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

## Features

- **Hardcoded Secret Detection**: Flags leaked GitHub tokens, AWS keys, OpenAI/Anthropic API keys, and RSA/EC private keys in diff additions.
- **Destructive Command Detection**: Detects `rm -rf` and `git push --force` embedded in scripts or pipelines.
- **Database & Migration Safeguards**: Highlights schema and migration modifications requiring backward compatibility checks.
- **Automated Test Auditing**: Warns when application logic is added or modified without corresponding test coverage.
- **Calculated Confidence Score**: Produces an objective rating (`High`, `Medium`, `Low`) based on blast radius, test presence, and security warnings.

## Running Tests

```bash
python agents/pr-reviewer/test_claude_review.py
```
