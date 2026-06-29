# 🤖 claude-review

> A Claude Code sub-agent that analyzes PR diffs and returns structured Markdown reviews.

## Features

- **CLI mode** — `claude-review --pr <url>` for on-demand reviews
- **GitHub Action** — auto-reviews every PR (opt-in via workflow)
- **Structured output** — Summary, Risks, Suggestions, Confidence Score
- **Configurable** — pick your Claude model, output to file, etc.

## Quick Start

### Prerequisites

- Node.js 22+
- A [GitHub PAT](https://github.com/settings/tokens) with `repo` scope
- An [Anthropic API key](https://console.anthropic.com/)

### Install

```bash
npm install -g claude-review
```

Or run directly:

```bash
npx claude-review --pr https://github.com/owner/repo/pull/123
```

### CLI Usage

```bash
claude-review --pr <url> [options]

Options:
  --pr <url>             PR URL to review (required)
  --model <name>         Claude model (default: claude-sonnet-4-20250514)
  --max-tokens <number>  Max response tokens (default: 4096)
  --output <file>        Save review to file instead of stdout
  --gh-token <token>     GitHub token (or set GITHUB_TOKEN env var)
  --anthropic-key <key>  Anthropic key (or set ANTHROPIC_API_KEY env var)
  --help                 Show help
```

### Example

```bash
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."

claude-review --pr https://github.com/facebook/react/pull/30000
```

## Output Format

```markdown
### Summary
(2-3 sentences summarizing what the PR does)

### Identified Risks
- Risk 1: description
- Risk 2: description

### Improvement Suggestions
- Suggestion 1: actionable recommendation
- Suggestion 2: actionable recommendation

### Confidence Score
**Score:** High
(Brief justification for the score)
```

## GitHub Action

Add `.github/workflows/claude-review.yml` to your repo (included in this package).
The action automatically reviews every new/synced PR and posts results as a comment.

**Required secrets:**
- `ANTHROPIC_API_KEY` — set in your repo Settings → Secrets and variables → Actions

## Development

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
cd claude-builders-bounty
npm install
npm run build
npm test
```

## License

MIT
