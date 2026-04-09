# Claude Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown comments.

## 🚀 Quick Start

### 1. Install
```bash
cd agents/claude-review
npm install
npm run build
```

### 2. Configure
```bash
export ANTHROPIC_API_KEY="sk-ant-xxx"
export GITHUB_TOKEN="ghp_xxx"  # Optional, for private repos
```

### 3. Run
```bash
npx claude-review --pr https://github.com/owner/repo/pull/123
```

## 📋 Output Format

```markdown
## Summary
Brief description of the PR changes.

## Identified Risks
- Risk 1
- Risk 2

## Improvement Suggestions
- Suggestion 1
- Suggestion 2

## Confidence Score
**Confidence: High**
```

## 🔧 GitHub Action

Use the included workflow to automatically review PRs:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/claude-review
        with:
          pr-url: ${{ github.event.pull_request.html_url }}
          api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## 💰 Bounty

Created for [claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)