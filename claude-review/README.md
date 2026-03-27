# claude-review 🤖

AI-powered PR review agent that analyzes GitHub Pull Requests using the Claude API and generates structured Markdown reviews.

## Features

- 🔍 **Fetches PR diffs** directly from GitHub API
- 🤖 **AI analysis** powered by Claude (claude-sonnet-4-20250514)
- 📋 **Structured output**: Summary, Risks, Suggestions, Confidence Score
- 📁 **File output** or stdout (pipeable)
- 🔄 **GitHub Action** included — auto-review PRs on open/sync
- 🔑 **Private repo support** via GitHub token

## Quick Start

```bash
# Clone and install
cd claude-review
npm install

# Review a PR
export ANTHROPIC_API_KEY="sk-ant-..."
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

## CLI Usage

```bash
# Basic usage
claude-review --pr <github-pr-url>

# With GitHub token (for private repos or higher rate limits)
claude-review --pr <url> --token ghp_xxxxx

# Save to file
claude-review --pr <url> --output review.md

# Raw JSON output
claude-review --pr <url> --json
```

### Options

| Flag | Description | Required |
|------|-------------|----------|
| `--pr <url>` | GitHub PR URL | ✅ |
| `--token <token>` | GitHub token (or `GITHUB_TOKEN` env) | Optional |
| `--api-key <key>` | Anthropic API key (or `ANTHROPIC_API_KEY` env) | Required |
| `--output <file>` | Write review to file | Optional |
| `--json` | Output raw JSON instead of Markdown | Optional |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |
| `GITHUB_TOKEN` | GitHub personal access token (optional, for private repos) |

## GitHub Action

Add the workflow to your repo to automatically review PRs:

1. Copy `.github/workflows/claude-review.yml` to your repository
2. Add `ANTHROPIC_API_KEY` to your repository secrets (Settings → Secrets → Actions)
3. PRs will be automatically reviewed when opened or updated

## Output Format

The review includes four sections:

### 📝 Summary
A 2-3 sentence overview of the PR changes and approach.

### ⚠️ Identified Risks
- Bugs, security issues, performance problems
- Breaking changes, missing edge cases

### 💡 Improvement Suggestions
- Actionable recommendations with specific file/line references

### 📊 Confidence Score
- **🟢 High** — Clear, well-structured changes
- **🟡 Medium** — Some areas need clarification
- **🔴 Low** — Significant concerns or incomplete review (e.g., truncated diff)

## Example

```bash
$ claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/89
```

See [`examples/`](examples/) for sample outputs from real PRs.

## Architecture

```
claude-review/
├── bin/claude-review.js    # CLI entrypoint (commander)
├── src/
│   ├── github.js           # GitHub API: fetch diff + metadata
│   ├── analyzer.js         # Claude API: structured review analysis
│   └── formatter.js        # Markdown output formatting
├── .github/workflows/
│   └── claude-review.yml   # GitHub Action for auto-review
├── examples/               # Sample review outputs
└── package.json
```

## Requirements

- Node.js ≥ 18
- Anthropic API key ([get one here](https://console.anthropic.com/))

## License

MIT
