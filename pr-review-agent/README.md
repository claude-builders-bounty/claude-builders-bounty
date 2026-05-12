# AI PR Review Agent

AI-powered Pull Request review agent using Claude API and GitHub API.

## Features

- 🤖 AI-powered code review using Claude
- 📊 Structured output: Summary, Risks, Suggestions, Confidence
- 🔗 Works with any public GitHub repository
- ⚙️ Configurable Claude model and token limits
- ⚡ CLI and GitHub Action support

## Installation

```bash
npm install -g pr-review-agent
# or
npm install pr-review-agent
```

## Usage

### CLI

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Options:
- `--pr, -p <url>` - GitHub PR URL (required)
- `--token, -t <token>` - GitHub token (or use `GITHUB_TOKEN` env)
- `--model, -m <model>` - Claude model (default: claude-sonnet-4-20250514)
- `--max-tokens, -c <n>` - Max response tokens (default: 4096)

### GitHub Action

```yaml
name: AI PR Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: AI PR Review
        uses: ./action.yml
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Output Format

The review is generated in Markdown with the following sections:

- **Summary** - 2-3 sentence overview
- **Risks** - Specific, actionable risks identified
- **Suggestions** - Prioritized improvement suggestions
- **Confidence** - Confidence level with rationale

## Environment Variables

- `GITHUB_TOKEN` - GitHub API token
- `ANTHROPIC_API_KEY` - Anthropic Claude API key

## Development

```bash
npm install
npm run build
npm start -- --pr https://github.com/owner/repo/pull/123
```

## License

MIT
