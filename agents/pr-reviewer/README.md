# claude-review — Autonomous PR Review Sub-Agent

> Autonomous Claude Code sub-agent that ingests a GitHub pull request diff, inspects code for vulnerabilities and architectural regressions, and formats a structured Markdown review.

## Features

- **CLI & CI/CD Native**: Run from your local terminal or execute automatically on every PR via GitHub Actions.
- **Strict Structured Markdown Output**:
  - 📝 **Summary of Changes**: 2–3 sentences summarizing modified files, scope, and intent.
  - ⚠️ **Identified Risks**: Static heuristic checks for hardcoded credentials, SQL injection, destructive queries, dynamic evaluations, and unhandled errors.
  - 💡 **Improvement Suggestions**: Actionable recommendations for code hygiene, performance, and best practices.
  - 🎯 **Confidence Score**: Low / Medium / High with explicit rationale based on diff volume and static analysis certainty.
- **Automated Comment Posting**: Supports posting directly back to GitHub PR review threads with `--post-comment`.

## CLI Usage

### Local Testing
```bash
# Make executable
chmod +x claude-review.js

# Review a GitHub PR (prints structured Markdown to stdout)
./claude-review.js --pr https://github.com/owner/repo/pull/123

# Review and automatically post a comment to the PR
export GITHUB_TOKEN="ghp_your_token_here"
./claude-review.js --pr https://github.com/owner/repo/pull/123 --post-comment

# Review a local diff file
./claude-review.js --diff ./changes.patch
```

## GitHub Action Setup

Add the following workflow file to your repository at `.github/workflows/claude-review.yml`:

```yaml
name: Claude Code PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Run Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node agents/pr-reviewer/claude-review.js --pr "${{ github.event.pull_request.html_url }}" --post-comment
```

## Sample Verification Outputs

The sub-agent was validated against two live GitHub pull requests:
- [Sample Output: PR #4296](sample-outputs/pr-4296.md)
- [Sample Output: PR #4297](sample-outputs/pr-4297.md)
