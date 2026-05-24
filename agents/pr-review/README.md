# Claude PR Review Agent 🔍

A Claude Code sub-agent that reviews GitHub Pull Requests and posts structured Markdown review comments.

## Features

- 🤖 CLI tool: `claude-review --pr <url>`
- ⚡ GitHub Action integration (automatic reviews on PR open/sync)
- 📋 Structured Markdown output with summary, risks, suggestions, and confidence
- 🔐 Works with GitHub API and Anthropic Claude API

## Setup

### Prerequisites

- Python 3.10+
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API Key

### Installation

```bash
cd agents/pr-review
pip install -r requirements.txt
```

### Environment Variables

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export ANTHROPIC_API_KEY="sk-ant-your_key_here"
```

## Usage

### CLI

```bash
# Review a PR by URL
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Review and post comment to the PR
python claude-review.py --pr https://github.com/owner/repo/pull/123 --post

# Review a local diff file
python claude-review.py --diff ./changes.diff

# Specify model
python claude-review.py --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-20250514
```

### GitHub Action

Copy `workflows/pr-review.yml` into `.github/workflows/pr-review.yml` in your repository (GitHub requires maintainers to add workflow files). It automatically reviews PRs when they are opened or updated.

Required repository secrets:
- `GITHUB_TOKEN` (automatically provided)
- `ANTHROPIC_API_KEY` (add manually)

### Output Format

The agent produces structured Markdown:

```markdown
## 🤖 PR Review

### Summary
<2–3 sentence summary of changes>

### ⚠️ Risks
- Risk 1
- Risk 2

### 💡 Suggestions
- Suggestion 1
- Suggestion 2

### Confidence: **Medium**
```

## Sample Outputs

See the `sample-outputs/` directory for reviews of real GitHub PRs:

- [`pr-sample-1.md`](sample-outputs/pr-sample-1.md) — Review of a React refactoring PR
- [`pr-sample-2.md`](sample-outputs/pr-sample-2.md) — Review of a Python API PR

## How It Works

1. Fetches the PR diff via GitHub API
2. Fetches PR metadata (title, description, changed files)
3. Sends the diff to Claude with a structured review prompt
4. Parses the response into structured Markdown
5. Optionally posts the review as a PR comment

## License

MIT
