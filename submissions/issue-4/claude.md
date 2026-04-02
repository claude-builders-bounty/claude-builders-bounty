# Claude Code PR Review Agent

This directory contains a PR review sub-agent for Claude Code that automatically reviews GitHub Pull Requests and posts structured review comments.

## Integration with Claude Code

### As a Hook

To use this agent as a Claude Code hook that automatically reviews PRs when mentioned:

1. Copy `pr_review_agent.py` to your Claude Code hooks directory
2. Add the following to your Claude Code configuration:

```json
{
  "hooks": {
    "pr-review": {
      "command": "python /path/to/pr_review_agent.py",
      "triggers": ["pr", "review", "pull-request"],
      "description": "Review a GitHub PR and post structured feedback"
    }
  }
}
```

### As a Sub-Agent

To invoke this as a sub-agent from Claude Code:

```bash
# Basic usage
python pr_review_agent.py https://github.com/owner/repo/pull/123

# With custom model
python pr_review_agent.py https://github.com/owner/repo/pull/123 --model claude-3-opus-20240229

# Security-focused review
python pr_review_agent.py https://github.com/owner/repo/pull/123 --focus security

# Dry-run (generate review without posting)
python pr_review_agent.py https://github.com/owner/repo/pull/123 --dry-run
```

## Configuration Options

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub token for `gh` CLI (usually set via `gh auth login`)

### Command-Line Arguments

- `pr_url` (positional): GitHub PR URL to review
- `--api-key`: Anthropic API key (or use env var)
- `--model`: Claude model to use (default: claude-3-5-sonnet-20241022)
- `--focus`: Review focus area (general, security, performance, readability)
- `--max-diff-size`: Maximum diff size in bytes (default: 500000)
- `--dry-run`: Generate review without posting
- `--verbose`: Enable detailed logging

## Example Integration in Claude Code Skills

Create a skill file (e.g., `pr-review/SKILL.md`):

```markdown
# PR Review Skill

Automated PR review using Claude API.

## Usage

When asked to review a PR:
1. Extract the PR URL from the conversation
2. Run: `python /path/to/pr_review_agent.py <PR_URL>`
3. The agent will automatically post the review comment

## Examples

User: "Review https://github.com/myorg/myrepo/pull/42"
Agent: [Runs review agent and confirms posted comment]
```

## Workflow Integration

### Continuous Review Pipeline

Set up automatic PR reviews on creation:

```yaml
# .github/workflows/auto-review.yml
name: Auto PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Run PR Review Agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python pr_review_agent.py \
            https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }} \
            --focus security \
            --verbose
```

### Claude Code Desktop Integration

Add to Claude Code's command palette:

```json
{
  "commands": {
    "review-pr": {
      "description": "Review a GitHub PR",
      "command": "python ${workspaceFolder}/pr_review_agent.py ${input:pr_url}"
    }
  },
  "inputs": [
    {
      "id": "pr_url",
      "type": "promptString",
      "description": "Enter the GitHub PR URL"
    }
  ]
}
```

## Features

- ✅ Automatic PR diff fetching via `gh` CLI
- ✅ Structured review with sections for:
  - Summary of changes
  - Potential bugs/issues
  - Improvement suggestions
  - Security considerations
  - Code quality assessment
- ✅ Configurable review focus (general, security, performance, readability)
- ✅ Handles large PRs with size limits
- ✅ Error handling for API failures
- ✅ Dry-run mode for testing
- ✅ Verbose logging for debugging

## Requirements

- Python 3.8+
- `requests` library
- GitHub CLI (`gh`) installed and authenticated
- Anthropic API key

## Installation

```bash
# Install dependencies
pip install requests

# Ensure gh CLI is authenticated
gh auth login

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run a review
python pr_review_agent.py https://github.com/owner/repo/pull/123
```

## License

MIT License - See LICENSE file for details.
