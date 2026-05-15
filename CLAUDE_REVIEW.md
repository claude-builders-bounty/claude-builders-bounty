# Claude Review Agent

`claude-review` is a zero-dependency Python CLI that fetches a GitHub pull request diff and returns a structured Markdown review comment.

## Setup

```bash
chmod +x scripts/claude-review
```

Optional:

```bash
ln -s "$PWD/scripts/claude-review" /usr/local/bin/claude-review
```

## Usage

```bash
scripts/claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
scripts/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output

The generated comment always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## GitHub Action Example

```yaml
name: Claude Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: read
    steps:
      - uses: actions/checkout@v4
      - name: Generate review
        run: |
          python3 scripts/claude-review \
            --pr "${{ github.event.pull_request.html_url }}" \
            --output claude-review.md
      - name: Print review
        run: cat claude-review.md
```

## Notes

This implementation is deterministic and works without API keys for public PRs. It is designed as a Claude Code sub-agent scaffold: the CLI extracts diff facts and risk signals, while `agents/pr-reviewer-agent.md` defines the higher-level review behavior for Claude Code.
