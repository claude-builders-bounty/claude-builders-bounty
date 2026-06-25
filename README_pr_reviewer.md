# Claude PR Reviewer Agent

A zero-dependency CLI tool and GitHub Action that fetches pull request diffs, analyzes the changes, and returns a structured Markdown review using the Claude API.

## Features

- **Zero-Dependency**: Written in pure Python using built-in libraries (no `pip install` required for dependencies).
- **Comprehensive Analysis**: Evaluates PR diffs and generates reviews with the following sections:
  - **Summary of Changes** (2-3 sentences)
  - **Identified Risks** (bugs, performance issues, security vulnerabilities)
  - **Improvement Suggestions** (clean code practices, optimizations, styling)
  - **Confidence Score** (**Low** / **Medium** / **High** with reasoning)
- **Multi-Environment Support**: Runs directly from the terminal (CLI) or integrates into CI/CD pipelines (GitHub Actions).
- **Supports Private Repositories**: Option to pass a `GITHUB_TOKEN` to retrieve diffs from private organization repositories.

---

## CLI Usage

### 1. Set the API Key
Set your Anthropic API Key in your environment:
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Run the Review Agent
Execute the script using the wrapper command:
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

---

## GitHub Action Integration

You can easily integrate this agent into your GitHub workflow.

### Example Workflow (`.github/workflows/claude-review.yml`)

Create a workflow file in your repository to review every pull request automatically:

```yaml
name: Claude PR Reviewer

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write # Required if you want to post comments
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Claude PR Reviewer
        id: reviewer
        uses: adamsithr/claude-builders-bounty@bounty/pr-reviewer
        with:
          pr_url: ${{ github.event.pull_request.html_url }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```
