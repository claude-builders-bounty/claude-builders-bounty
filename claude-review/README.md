# claude-review

AI-powered PR reviewer using Claude. Analyzes GitHub PR diffs and produces structured Markdown reviews with summary, risks, suggestions, and confidence scores.

## Features

- **CLI tool**: Review any PR with a single command
- **GitHub Action**: Automatic reviews on PR open/update
- **Structured output**: Summary, risks, suggestions, confidence score
- **Flexible models**: Works with Claude Sonnet, Opus, or any Anthropic model
- **JSON mode**: Machine-readable output for integration with other tools

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- A GitHub token (optional, for higher rate limits)

## Installation

### From source (recommended)

```bash
git clone https://github.com/gtmdev-br/claude-builders-bounty.git
cd claude-builders-bounty/claude-review
pip install .
```

### Direct install

```bash
pip install .
```

## Setup

Set your API keys:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."  # optional but recommended
```

## Usage

### CLI

```bash
# Review a PR by URL
claude-review https://github.com/anthropics/anthropic-sdk-python/pull/123

# Save review to file
claude-review https://github.com/owner/repo/pull/123 -o review.md

# JSON output
claude-review https://github.com/owner/repo/pull/123 --json

# Use a different model
claude-review https://github.com/owner/repo/pull/123 --model claude-opus-4-20250514

# Short form
claude-review owner/repo#123
```

### Python

```python
from claude_review import review_pr

review = review_pr("owner", "repo", 123)
print(review)
```

## Output Format

Each review includes:

### Summary
2-3 sentence overview of the PR's purpose and quality.

### Risks
List of potential bugs, security issues, or regressions.

### Suggestions
Actionable improvement recommendations.

### Confidence
Low / Medium / High with reasoning.

## Example

```
$ claude-review https://github.com/anthropics/anthropic-sdk-python/pull/100

# Review of PR #100

**Repository**: anthropics/anthropic-sdk-python
**PR**: [#100](https://github.com/anthropics/anthropic-sdk-python/pull/100)

---

### Summary
This PR adds streaming support for the messages API endpoint. The implementation
follows established patterns in the codebase and includes proper error handling.

### Risks
- No tests included for the new streaming functionality
- The `stream` parameter default changes behavior for existing users

### Suggestions
- Add integration tests for streaming responses
- Consider a deprecation period before changing the default `stream` parameter

### Confidence
- **Level**: High
- **Reason**: Changes are well-scoped and follow existing patterns.
```

## GitHub Action

See `.github/workflows/review.yml` for automatic PR reviews.

```yaml
# .github/workflows/review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ./claude-review
      - run: claude-review "${{ github.event.pull_request.html_url }}"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## License

MIT
