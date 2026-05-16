# Claude PR Review Agent

AI-powered PR reviewer that analyzes GitHub pull requests and generates structured review comments using Claude.

## Features

- **CLI tool** — Review any PR from your terminal
- **GitHub Action** — Auto-review PRs on open/sync
- **Structured output** — Summary, risks, suggestions, confidence score
- **Post to PR** — Optionally post the review as a comment

## Setup (CLI)

1. Install dependencies:
   ```bash
   # Requires: gh CLI, curl, python3
   gh auth login
   ```

2. Set your API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. Make executable and run:
   ```bash
   chmod +x claude-review
   ./claude-review --pr https://github.com/owner/repo/pull/123
   ```

## Setup (GitHub Action)

1. Copy `.github/workflows/claude-review.yml` to your repo
2. Add `ANTHROPIC_API_KEY` to your repo secrets (Settings → Secrets → Actions)
3. Open a PR — the review posts automatically

## Usage

```bash
# Review a PR (output to terminal)
./claude-review --pr https://github.com/octocat/hello/pull/42

# Review and post comment
./claude-review --pr octocat/hello#42 --post

# Use a different model
./claude-review --pr owner/repo#10 --model claude-sonnet-4-20250514
```

## Sample Outputs

See `samples/` directory for real review outputs:
- `sample-1-changelog-pr.md` — Review of a changelog generator PR
- `sample-2-hook-pr.md` — Review of a destructive bash hook PR

## How It Works

1. Fetches PR metadata and diff via `gh` CLI
2. Constructs a structured prompt with PR context
3. Calls Claude API for analysis
4. Outputs formatted Markdown review
5. Optionally posts as PR comment via `gh pr comment`

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--pr` | (required) | PR URL or `owner/repo#number` |
| `--post` | false | Post review as PR comment |
| `--model` | claude-sonnet-4-20250514 | Claude model to use |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `GH_TOKEN` | No | GitHub token (uses `gh auth` by default) |
