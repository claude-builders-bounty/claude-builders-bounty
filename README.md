# Claude PR Review Agent

**Bounty**: $150 | **Author**: sungdark | **Issue**: claude-builders-bounty#4

## Overview

A CLI tool and GitHub Action that uses Claude API to analyze PR diffs and generate structured code reviews with risk assessment, improvement suggestions, and confidence scoring.

## Files

- `claude-review.sh` — CLI tool for reviewing PRs or local diffs
- `.github/workflows/pr-review.yml` — GitHub Action (see below, cannot be pushed due to token scope restriction)

## Features

- 🤖 **AI-powered analysis** — Uses Claude Sonnet 4 for code review
- 📊 **Structured output** — JSON format with summary, risks, suggestions, confidence score
- 💻 **CLI tool** — Works with GitHub PR URLs or local diff files
- ⚙️ **GitHub Action** — Automatic review on every PR (see setup below)
- 🔒 **Safe** — No code stored externally, all processing via API

## CLI Usage

### Prerequisites

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Install

```bash
curl -O https://raw.githubusercontent.com/sungdark/claude-review-agent/main/claude-review.sh
chmod +x claude-review.sh
```

### Review a GitHub PR

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

### Review a local diff

```bash
git diff > changes.diff
./claude-review.sh --diff changes.diff
```

## GitHub Action Setup

Create `.github/workflows/pr-review.yml` in your repo with this content:

```yaml
name: AI PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Get PR diff
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -s -H "Authorization: token $GH_TOKEN" \
            "${{ github.api_url }}/repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}" \
            -H "Accept: application/vnd.github.v3.diff" > pr.diff

      - name: Run Claude Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          RESPONSE=$(curl -s -X POST "https://api.anthropic.com/v1/messages" \
            -H "x-api-key: ${ANTHROPIC_API_KEY}" \
            -H "anthropic-version: 2023-06-01" \
            -H "content-type: application/json" \
            -d '{"model":"claude-sonnet-4-20250514","max_tokens":1024,"messages":[{"role":"user","content":"Review this PR diff and respond with JSON: {summary, risks[], suggestions[], confidence}. DIFF: '"$(cat pr.diff | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])')"'}]}')
          echo "## AI Code Review" >> $GITHUB_STEP_SUMMARY
          echo '```json' >> $GITHUB_STEP_SUMMARY
          echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content',[{}])[0].get('text','No response'))" >> $GITHUB_STEP_SUMMARY 2>/dev/null || echo "Parse error" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

      - name: Post PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync(process.env.GITHUB_STEP_SUMMARY, 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });
```

Add `ANTHROPIC_API_KEY` to your repo secrets.

## Sample Output

```json
{
  "summary": "This PR adds a new authentication middleware that validates JWT tokens on all protected routes. It includes proper error handling and integrates with the existing user service to fetch user details after token validation.",
  "risks": [
    "JWT secret is currently hardcoded - should use environment variable",
    "No rate limiting on authentication endpoints - potential brute force risk",
    "Missing test coverage for edge cases like expired tokens"
  ],
  "suggestions": [
    "Move JWT_SECRET to environment variable for production safety",
    "Add rate limiting middleware to auth routes",
    "Add unit tests for token validation edge cases"
  ],
  "confidence": "High"
}
```

## Acceptance Criteria

- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action YAML included (see above)
- [x] Structured output with: Summary, Risks, Suggestions, Confidence score
- [x] README with setup and usage instructions

## Payment

eB51DWp1uECrLZRLsE2cnyZUzfRWvzUzaJzkatTpQV9
