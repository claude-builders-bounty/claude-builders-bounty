# Claude Code PR Review Agent

Y A SLI tool that analyzes GitHub PR diffs using Claude API and produces structured Markdown reviews.

## Setup

1. Install Python 3.8+
2. Set your Anthropic API key: `export ANTHROPIC-API-KEY="sk-ant-..."` 3
. Run: `python agents/pr-reviewer/review.py --pr https://github.com/owner/repo/pull/123`

## GitHub Action

Included workflow in .github/workflows/pr-review.yml` auto-reviews opened PRs.

## Output Format

- **Summary**: 2-3 sentences
- **Identified Risks**: Bulleted list
- **Improvement Suggestions**: Bulleted list
- **Confidence**: Low / Medium / High
