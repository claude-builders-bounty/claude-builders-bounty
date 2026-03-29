# claude-review — PR Review Agent

> A Claude Code sub-agent that fetches a GitHub PR diff and returns a structured Markdown code review.

Fixes [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment.

## Features

- Fetches PR diffs via the GitHub API (handles diffs up to 80 KB; truncates larger ones gracefully)
- Analyzes diffs using Claude (`claude-opus-4-5`)
- Returns structured Markdown with **Summary**, **Risks**, **Improvement Suggestions**, and **Confidence Score**
- Optionally saves output to a file with `--output`
- Includes a GitHub Action for automated PR review comments

## Setup

### 1. Install dependencies

```bash
cd agents/pr-reviewer
npm install
```

### 2. Set environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT with `repo` read access ([create one](https://github.com/settings/tokens)) |
| `ANTHROPIC_API_KEY` | Anthropic API key from [console.anthropic.com](https://console.anthropic.com) |

### 3. Build

```bash
npm run build
```

## Usage

### CLI

```bash
# Review a PR and print to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Save review to a file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

The included workflow (`.github/workflows/pr-review.yml`) runs automatically on every PR. To enable it:

1. Add `ANTHROPIC_API_KEY` to your repo's **Settings > Secrets and variables > Actions**
2. `GITHUB_TOKEN` is provided automatically by GitHub Actions

The action posts the review as a PR comment.

## Output Format

```markdown
## Summary
2-3 sentence overview of what the PR changes.

## Risks
- Identified security issues, breaking changes, missing error handling

## Improvement Suggestions
- Style improvements, missing tests, performance optimizations

## Confidence Score
Low / Medium / High — based on diff size and analysis certainty
```

## Testing

```bash
npm test
```

Runs Jest with coverage. See `__tests__/` for unit tests covering the agent, GitHub API client, and URL parser.
