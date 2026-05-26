# Claude Code PR Reviewer Agent 🤖

A zero-dependency Python script and GitHub Action that fetches a PR diff, conducts an automated code review focusing on security, concurrency, performance, and correctness, and publishes a structured review comment using Claude.

## CLI Usage

### Step 1: Set environment variables
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export GITHUB_TOKEN="your-github-personal-access-token" # Optional: to write comments/fetch private diffs
```

### Step 2: Run the script
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

---

## GitHub Action Integration

Add this workflow file to your repository under `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Reviewer
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Claude PR Reviewer
        uses: claude-builders-bounty/claude-builders-bounty/agents/pr-reviewer@feat/pr-reviewer-agent
        with:
          anthropic-key: ${{ secrets.ANTHROPIC_API_KEY }}
```
