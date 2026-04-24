# claude-review 🤖

AI-powered PR reviewer using Claude. Analyzes GitHub Pull Requests and generates structured Markdown review comments with summary, risks, suggestions, and confidence scoring.

## Features

- **CLI tool**: Review any public GitHub PR from your terminal
- **GitHub Action**: Automatically review PRs on open/sync
- **Structured output**: Summary, risks, suggestions, confidence score
- **Large PR support**: Automatically truncates huge diffs
- **Zero dependencies**: Pure Node.js, no npm install needed

## Setup

### Prerequisites
- Node.js 18+
- [Anthropic API key](https://console.anthropic.com/)
- GitHub token (optional, for private repos / higher rate limits)

### Install

```bash
# Clone the repo
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/agents/pr-review-agent

# Make CLI executable
chmod +x bin/claude-review

# Add to PATH (optional)
npm link
# OR
export PATH="$PWD/bin:$PATH"
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Required
export GITHUB_TOKEN="ghp_..."            # Optional (for private repos)
```

## Usage

### CLI

```bash
# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Verbose mode
claude-review --pr https://github.com/owner/repo/pull/123 --verbose

# Help
claude-review --help
```

### GitHub Action

Add the workflow to your repo:

1. Copy `.github/workflows/pr-review.yml` to your repo's `.github/workflows/`
2. Add `ANTHROPIC_API_KEY` to your repo's Settings → Secrets → Actions
3. PRs will be automatically reviewed when opened or updated

You can also trigger manually via Actions → Claude PR Review → Run workflow.

## Output Format

The review follows a consistent structured format:

```markdown
## 🤖 Claude PR Review: owner/repo#123
> **PR Title** by @author

### 📋 Summary
(2-3 sentence summary of what the PR does)

### ⚠️ Identified Risks
- Risk 1 with file reference
- Risk 2 with specific concern

### 💡 Improvement Suggestions
- Suggestion 1 referencing specific code
- Suggestion 2 with rationale

### 🎯 Confidence Score
**High** / **Medium** / **Low**
```

## Sample Reviews

See the `samples/` directory for real review outputs:
- [`sample-review-1.md`](samples/sample-review-1.md) — Review of a Node.js dependency update PR
- [`sample-review-2.md`](samples/sample-review-2.md) — Review of a feature addition PR

## How It Works

1. Parses the GitHub PR URL to extract owner/repo/number
2. Fetches PR metadata, file list, and diff via GitHub API
3. Constructs a detailed prompt with all PR context
4. Sends to Claude (claude-sonnet-4-20250514) for analysis
5. Outputs structured Markdown review

## License

MIT
