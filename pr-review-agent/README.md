# claude-review

A Claude Code sub-agent for automated PR review. Analyzes GitHub pull requests and generates structured, actionable feedback.

## Features

- Fetches PR data via GitHub API
- Analyzes diffs using Claude API (`claude-sonnet-4-20250514`)
- Generates structured review with: Summary, Risks, Suggestions, Confidence Score
- CLI interface for easy integration
- Zero dependencies beyond `requests`

## Setup

1. Clone and navigate to the directory
2. Install dependencies: `pip install requests`
3. Set environment variables:

```bash
export ANTHROPIC_API_KEY="your_claude_api_key"
export GITHUB_TOKEN="your_github_token"
```

## Usage

```bash
# Review a PR by full URL
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Review using short form
python3 claude-review.py --pr owner/repo/123

# Save review to file
python3 claude-review.py --pr owner/repo/123 --o review.md
```

## Output Format

The tool generates a structured review:

```markdown
## 🤖 Automated PR Review

## Summary
Brief description of what the PR does

## Risks
- Potential issues identified
- Security concerns
- Breaking changes

## Suggestions
- Actionable improvements
- Code quality recommendations

## Confidence Score
High / Medium / Low
```

## Requirements

- Python 3.7+
- `requests` library
- Claude API key
- GitHub token with repo access