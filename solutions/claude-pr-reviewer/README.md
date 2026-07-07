# Claude PR Reviewer

An automated code review tool and GitHub Action powered by Claude 3.5 Sonnet. It retrieves the code diff of a GitHub Pull Request, performs an intelligent code review using Claude, and prints a structured Markdown report or comments it directly onto the PR.

## Features

- **CLI Usage**: Review any public or private GitHub PR from your local terminal.
- **GitHub Action**: Automatically post structured review comments on new PRs.
- **Zero-Dependency**: Written in pure Python 3 using standard libraries (`urllib` etc.), requiring no external packages.

---

## Setup & CLI Usage

### 1. Set environment variables
You need an Anthropic API Key to use Claude. Set it in your terminal:

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

If reviewing a private repository, also provide your GitHub Personal Access Token:

```bash
export GITHUB_TOKEN="your-github-token"
```

### 2. Run the reviewer
You can run the script directly passing the PR URL:

```bash
python solutions/claude-pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

---

## GitHub Actions Integration

To run this review automatically on every new Pull Request, create a file at `.github/workflows/claude-review.yml`:

```yaml
name: Automated Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Claude PR Reviewer
        uses: ./solutions/claude-pr-reviewer
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Output Format

The output is structured markdown containing:
- **Summary of Changes**: 2-3 sentences summarizing the PR modifications.
- **Identified Risks**: List of bugs, performance, or security concerns.
- **Improvement Suggestions**: Actionable code-quality feedback.
- **Confidence Score**: Low / Medium / High assessment.

## Running Tests

To run the unit tests:

```bash
python -m unittest solutions/claude-pr-reviewer/test_pr_reviews.py
```
