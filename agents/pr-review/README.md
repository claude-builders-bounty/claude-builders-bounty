# Claude Code PR Review Agent

An AI-powered pull request review tool that uses Claude to generate structured, actionable code reviews. Works as a CLI tool or a GitHub Action.

## Features

- Structured Markdown output with summary, risks, suggestions, and confidence score
- CLI usage for local review workflows
- GitHub Action for automated PR reviews
- Handles large diffs with automatic truncation
- Supports both `claude` CLI and direct Anthropic API access
- JSON output format option

## Quick Start

### CLI Usage

```bash
# Make the script executable
chmod +x agents/pr-review/claude-review.sh

# Symlink for convenience (optional)
ln -s "$(pwd)/agents/pr-review/claude-review.sh" /usr/local/bin/claude-review

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123
```

### Prerequisites

1. **GitHub CLI** (`gh`) installed and authenticated:
   ```bash
   # Install: https://cli.github.com
   gh auth login
   ```

2. **One of:**
   - `claude` CLI installed (Claude Code), OR
   - `ANTHROPIC_API_KEY` environment variable set

### CLI Options

| Option          | Description                          | Default                    |
|-----------------|--------------------------------------|----------------------------|
| `--pr <url>`    | GitHub PR URL (required)             | -                          |
| `--model <m>`   | Claude model to use                  | `claude-sonnet-4-20250514` |
| `--output <f>`  | Write review to file                 | stdout                     |
| `--format <f>`  | Output format: `markdown` or `json`  | `markdown`                 |
| `--verbose`     | Show debug info                      | off                        |
| `--help`        | Show usage                           | -                          |

### Examples

```bash
# Basic review
claude-review --pr https://github.com/facebook/react/pull/28000

# Save to file
claude-review --pr https://github.com/owner/repo/pull/42 --output review.md

# JSON output
claude-review --pr https://github.com/owner/repo/pull/42 --format json

# Use a specific model
claude-review --pr https://github.com/owner/repo/pull/42 --model claude-opus-4-20250514

# Verbose mode
claude-review --pr https://github.com/owner/repo/pull/42 --verbose
```

## GitHub Action

### Setup

1. Add your Anthropic API key as a repository secret:
   - Go to **Settings > Secrets and variables > Actions**
   - Click **New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: your API key

2. Create `.github/workflows/claude-pr-review.yml` in your repository:

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
      - name: Checkout
        uses: actions/checkout@v4

      - name: Claude PR Review
        uses: claude-builders-bounty/claude-builders-bounty/agents/pr-review@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          post_comment: "true"
```

### Action Inputs

| Input              | Description                        | Required | Default          |
|--------------------|------------------------------------|----------|------------------|
| `anthropic_api_key`| Anthropic API key                  | Yes      | -                |
| `github_token`     | GitHub token for PR access         | No       | `GITHUB_TOKEN`   |
| `model`            | Claude model                       | No       | `claude-sonnet-4-20250514` |
| `post_comment`     | Post review as PR comment          | No       | `true`           |
| `fail_on_risks`    | Fail workflow if risks found       | No       | `false`          |

### Action Outputs

| Output       | Description                          |
|--------------|--------------------------------------|
| `review`     | Full review in Markdown              |
| `confidence` | Confidence score (Low/Medium/High)   |

## Output Format

Every review contains these sections:

### Summary
A 2-3 sentence overview of what the PR does, the approach taken, and scope.

### Identified Risks
A bulleted list of specific risks found, covering:
- Security concerns
- Performance issues
- Correctness bugs or edge cases
- Breaking changes
- Missing error handling

### Improvement Suggestions
Actionable suggestions for improving the code:
- Better naming or organization
- Missing tests
- Documentation needs
- Alternative approaches

### Confidence Score
One of **Low**, **Medium**, or **High** with a brief explanation.

## Example Reviews

See the `examples/` directory for sample review outputs run against real public PRs:

- [`example-react-pr.md`](examples/example-react-pr.md) - Review of a React PR
- [`example-astro-pr.md`](examples/example-astro-pr.md) - Review of an Astro PR

## Development

```bash
# Run locally
export ANTHROPIC_API_KEY="sk-ant-..."
./agents/pr-review/claude-review.sh --pr https://github.com/owner/repo/pull/123 --verbose

# Test with output file
./agents/pr-review/claude-review.sh --pr https://github.com/owner/repo/pull/123 --output test-review.md
```

## License

MIT - see [LICENSE](../../LICENSE) in the repo root.
