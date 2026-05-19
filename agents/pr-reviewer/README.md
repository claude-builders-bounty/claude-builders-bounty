# PR Reviewer Agent 🤖

An AI-powered PR reviewer that analyzes diffs and provides structured Markdown feedback.

## Features
- Fetches real-time diffs using GitHub CLI.
- Provides a structured report:
  - **Summary of Changes**: High-level overview.
  - **Identified Risks**: Security, performance, or logic issues.
  - **Improvement Suggestions**: Best practices and optimizations.
  - **Confidence Score**: AI's certainty about the review.

## Installation

1. Ensure you have [GitHub CLI](https://cli.github.com/) installed and authenticated.
2. Clone this repository.
3. Install Python dependencies (optional for the basic CLI):
   ```bash
   pip install -r agents/pr-reviewer/requirements.txt
   ```

## Usage

### CLI
Run the reviewer on any PR:
```bash
python agents/pr-reviewer/pr_reviewer.py 123 --repo owner/repo
```

### GitHub Action
Add this to your `.github/workflows/pr-review.yml`:
```yaml
name: PR Reviewer
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run PR Reviewer
        uses: ./agents/pr-reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Sample Reviews
Check out the [samples](./samples/) directory for real-world examples:
- [Review of PR #1727 (Changelog Skill)](./samples/review_1727.md)
- [Review of React PR #36485 (Security Fix)](./samples/review_36485.md)
