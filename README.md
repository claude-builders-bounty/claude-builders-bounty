# claude-review

AI-powered pull request review using [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Analyzes GitHub PR diffs and produces structured Markdown reviews with summaries, risk assessments, improvement suggestions, and confidence scores.

## Features

- **CLI tool** — review any public/private GitHub PR from your terminal
- **GitHub Action** — automatically review PRs on open/sync/reopen
- **Structured output** — consistent Markdown format with summary, risks, suggestions, and confidence
- **Large diff handling** — auto-truncates oversized diffs to stay within context limits
- **Comment posting** — optionally posts the review directly as a PR comment

## Prerequisites

| Tool | Install | Purpose |
|------|---------|---------|
| [gh](https://cli.github.com) | `brew install gh` | Fetch PR data from GitHub |
| [claude](https://docs.anthropic.com/en/docs/claude-code) | `npm i -g @anthropic-ai/claude-code` | AI analysis via Claude Code |
| [jq](https://jqlang.github.io/jq/) | `brew install jq` | Parse JSON responses |

You also need:
- **GitHub CLI authenticated:** run `gh auth login`
- **Anthropic API key:** set `ANTHROPIC_API_KEY` in your environment

## Quick Start

### CLI Usage

```bash
# Clone and make executable
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
chmod +x claude-review

# Review a PR (output to terminal)
./claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as a PR comment
./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

# Use a specific model
./claude-review --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-20250514
```

### CLI Options

```
OPTIONS
  --pr <url>            GitHub pull request URL (required)
  --post-comment        Post the review as a comment on the PR
  --model <model>       Claude model to use (passed through to claude CLI)
  -h, --help            Show this help message
  -v, --version         Show version
```

## GitHub Action

### Setup

1. Add your Anthropic API key as a repository secret named `ANTHROPIC_API_KEY`
2. Copy the workflow file to your repo:

```bash
mkdir -p .github/workflows
cp .github/workflows/pr-review.yml your-repo/.github/workflows/
```

Or create `.github/workflows/pr-review.yml` in your repository:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install -g @anthropic-ai/claude-code
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x ./claude-review
          ./claude-review --pr "${{ github.event.pull_request.html_url }}" --post-comment
```

### Using as a Reusable Action

You can also reference this repository as a composite action:

```yaml
steps:
  - uses: claude-builders-bounty/claude-builders-bounty@main
    with:
      anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
      post_comment: 'true'
```

### Action Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | Yes | — | Anthropic API key |
| `github_token` | No | `${{ github.token }}` | GitHub token for posting comments |
| `model` | No | — | Claude model override |
| `post_comment` | No | `true` | Post review as PR comment |

### Action Outputs

| Output | Description |
|--------|-------------|
| `review` | The generated review in Markdown format |

## Output Format

Every review follows this structure:

```markdown
## 🔍 PR Review: <title>

### Summary
2–3 sentence overview of the changes.

### Identified Risks
- Concrete risk with file/line references and impact explanation
- ...

### Improvement Suggestions
- Specific, actionable suggestion with file references
- ...

### Confidence Score
**Low** / **Medium** / **High**

Explanation of confidence level.
```

See [`samples/`](./samples/) for full example outputs.

## How It Works

1. **Fetch** — uses `gh` CLI to retrieve PR metadata (title, author, description, file list, stats) and the full diff
2. **Truncate** — if the diff exceeds 100K characters, it's truncated with a notice to stay within Claude's context window
3. **Analyze** — pipes the PR data and a structured prompt to Claude Code (`claude -p`) for analysis
4. **Output** — prints the Markdown review to stdout and optionally posts it as a PR comment via `gh pr comment`

## Sample Outputs

- [Sample 1: JWT Authentication Middleware](./samples/sample-output-1.md) — feature PR adding auth middleware
- [Sample 2: WebSocket Race Condition Fix](./samples/sample-output-2.md) — bug fix PR resolving concurrency issue

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `error: missing required dependencies: gh` | Install GitHub CLI: `brew install gh` |
| `error: missing required dependencies: claude` | Install Claude Code: `npm i -g @anthropic-ai/claude-code` |
| `error: failed to fetch PR metadata` | Run `gh auth login` and verify the PR URL is correct |
| `error: claude returned an error` | Verify `ANTHROPIC_API_KEY` is set and valid |
| `warn: diff is N chars — truncating` | Normal for large PRs; review covers the first 100K chars |

## License

MIT
