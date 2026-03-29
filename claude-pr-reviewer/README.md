# claude-review — AI-Powered PR Reviewer

A Claude Code sub-agent that reviews GitHub PRs and generates structured Markdown feedback.

## 🚀 Quick Start

### CLI Usage

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."  # Optional, for private repos / higher rate limits

node claude-review.js --pr https://github.com/owner/repo/pull/123
```

### GitHub Action Usage

1. Copy `.github/workflows/claude-review.yml` to your repo
2. Copy `claude-review.js` to your repo root
3. Add `ANTHROPIC_API_KEY` to your repo's Settings → Secrets → Actions
4. Every new PR will automatically get a Claude review comment!

## 📋 Output Format

The review includes:

- **📝 Summary** — 2-3 sentence overview of the PR
- **⚠️ Identified Risks** — Potential issues, edge cases, security concerns
- **💡 Improvement Suggestions** — Actionable code improvement recommendations
- **🎯 Confidence Score** — Low / Medium / High based on diff quality

## 🧪 Sample Outputs

See the `samples/` directory for real PR review outputs.

## Requirements

- Node.js 18+
- Anthropic API key (Claude claude-sonnet-4-20250514)
- GitHub token (optional, for private repos)

## How It Works

1. Fetches PR metadata and diff from the GitHub API
2. Constructs a structured prompt with PR context
3. Sends to Claude claude-sonnet-4-20250514 for analysis
4. Returns formatted Markdown review

## License

MIT
