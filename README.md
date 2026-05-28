# Claude PR Review Agent

A Claude Code sub-agent that takes a PR URL, analyzes the diff, and returns a structured markdown review.

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
   chmod +x claude-review
   ```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Structure

The review includes:
- **Summary** — 2-3 sentence overview of changes
- **Identified Risks** — security concerns, edge cases, regressions
- **Improvement Suggestions** — actionable code-level feedback
- **Confidence Score** — Low / Medium / High

## GitHub Action

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
        run: |
          chmod +x claude-review
          ./claude-review --pr "${{ github.event.pull_request.html_url }}"
```

## Tested On

See sample-outputs/ for example reviews on real GitHub PRs.
