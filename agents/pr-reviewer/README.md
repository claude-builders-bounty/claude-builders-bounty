# Claude PR Review Agent

A Claude Code sub-agent that takes a PR URL, analyzes the diff, and returns a structured markdown review with risks, improvement suggestions, and a confidence score.

**Bounty:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Features

- Fetches PR metadata, diff, commits, and changed files via GitHub API
- Analyzes the diff for security risks (credentials, destructive operations)
- Checks for code quality issues (debug logging, TODOs, large diffs)
- Optionally uses Claude API for AI-powered analysis
- Outputs a structured markdown review ready to post as a PR comment

## Quick Setup

1. Save your GitHub token:
   ```bash
   export GITHUB_TOKEN="ghp_..."
   ```

2. (Optional) Set Anthropic API key for AI-powered analysis:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. Make the script executable:
   ```bash
   chmod +x agents/pr-reviewer/claude-review.sh
   ```

## Usage

```bash
./agents/pr-reviewer/claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output Structure

The review includes:
- **Summary** -- 2-3 sentence overview of changes
- **Identified Risks** -- security concerns, edge cases, regressions
- **Improvement Suggestions** -- actionable code-level feedback
- **Confidence Score** -- Low / Medium / High based on diff size and complexity

## GitHub Action Integration

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          chmod +x agents/pr-reviewer/claude-review.sh
          ./agents/pr-reviewer/claude-review.sh --pr "${{ github.event.pull_request.html_url }}"
```

## Sample Output

See `sample-outputs/` for example reviews on real GitHub PRs.
