# claude-review 🤖

AI-powered structured PR review agent for GitHub.

Given a GitHub pull request URL, `claude-review` fetches the diff and generates a detailed structured Markdown review with:

- **Summary of changes** — what the PR does at a glance
- **Identified risks** — security, performance, correctness concerns
- **Improvement suggestions** — actionable code quality improvements
- **Confidence score** — High / Medium / Low

Two review modes:
- **AI mode** (default) — uses an LLM via [OpenRouter](https://openrouter.ai) for deep semantic code understanding
- **Heuristic mode** (`--no-llm`) — rule-based analysis, no API key needed

## Quick Start

```bash
# Install
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
cp claude-review/claude-review /usr/local/bin/

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Use heuristic-only (no API key)
claude-review --pr https://github.com/owner/repo/pull/123 --no-llm

# Post review as a PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

## Prerequisites

- **Python 3.10+**
- **GitHub authentication** — either:
  - [`gh` CLI](https://cli.github.com/) authenticated (`gh auth login`), OR
  - `GITHUB_TOKEN` environment variable
- **OpenRouter API key** (optional, for AI-powered reviews):
  - Get one free at https://openrouter.ai/keys
  - Set: `export OPENROUTER_API_KEY=sk-or-v1-...`

Without an API key, the tool falls back to heuristic review automatically.

## GitHub Action Integration

Add to `.github/workflows/pr-review.yml`:

```yaml
name: AI PR Review
on:
  pull_request_target:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python3 claude-review --pr ${{ github.event.pull_request.html_url }} --post
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

Set `OPENROUTER_API_KEY` in your repo's Actions secrets for AI-powered reviews.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub token for API access |
| `OPENROUTER_API_KEY` | No | Enables AI-powered review |

## Sample Output

See [`samples/`](./samples/) for example reviews of real PRs.

## Project Structure

```
claude-review/
├── claude-review                 # CLI tool (Python)
├── .github/workflows/
│   └── pr-review.yml             # GitHub Action workflow
└── samples/
    ├── review-destructive-bash-guard.md
    └── review-changelog-skill.md
```
