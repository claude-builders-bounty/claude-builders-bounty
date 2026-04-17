# Claude Code PR Reviewer Agent

A CLI tool that reviews GitHub Pull Requests and generates structured Markdown review comments using Claude AI.

## Features

- **CLI Interface**: `claude-review --pr <url>`
- **Structured Output**: Summary, Risks, Suggestions, Confidence Score
- **GitHub Action**: Automated PR review workflow
- **Local Fallback**: Works without Claude API key

## Installation

```bash
# Clone or copy the script
cp pr-reviewer-agent/claude-review.py /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Usage

### CLI

```bash
# Basic usage
claude-review --pr https://github.com/owner/repo/pull/123 --token YOUR_GITHUB_TOKEN

# With Claude AI analysis
claude-review --pr 123 --repo owner/repo --token TOKEN --claude-key ANTHROPIC_KEY

# Using environment variables
export GITHUB_TOKEN=your_token
export ANTHROPIC_API_KEY=your_key
claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action

```yaml
- name: Run PR Review
  uses: ./pr-reviewer-agent
  with:
    pr_url: ${{ github.event.pull_request.html_url }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Output Format

```markdown
## Summary
2-3 sentences describing what this PR does.

## Identified Risks
- Risk 1
- Risk 2

## Improvement Suggestions
- Suggestion 1
- Suggestion 2

## Confidence Score
High / Medium / Low
```

## Sample Reviews

See `samples/` directory for example outputs on real PRs.

## Requirements

- Python 3.7+
- GitHub token (for private repos)
- Optional: Anthropic API key for AI-powered analysis