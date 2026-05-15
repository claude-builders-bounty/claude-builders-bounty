# Claude Code PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and returns structured Markdown review comments — with risk analysis, improvement suggestions, and a confidence score.

**Sponsored by Opire — $150 Bounty** | [Issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Install (1 command)

```bash
cp claude-review /usr/local/bin/ && chmod +x /usr/local/bin/claude-review
```

Requires: `gh` CLI (authenticated), Python 3.7+

## Usage

```bash
# Fetch PR info and generate a review template
claude-review --pr https://github.com/owner/repo/pull/123

# Output raw PR data as JSON (for piping to other tools)
claude-review --pr https://github.com/owner/repo/pull/123 --json

# Generate a Claude-ready review prompt
claude-review --pr https://github.com/owner/repo/pull/123 --prompt > prompt.txt
```

## Output Format

```markdown
## 🤖 Claude Code PR Review

> 🔗 [owner/repo#123](...)
> 👤 **Author:** username
> 📊 **Changes:** +150/-30 in 5 files

### 📋 Summary of Changes
2-3 sentence summary of what changed

### ⚠️ Identified Risks
1. Risk description
2. Risk description

### 💡 Improvement Suggestions
1. Suggestion
2. Suggestion

### 🟢 Confidence: `[Low / Medium / High]`
```

## GitHub Action (Automated PR Review)

Add `.github/workflows/claude-review.yml` to any repo:

```yaml
name: Claude Code PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Fetch PR diff
        run: |
          gh pr diff ${{ github.event.pull_request.number }} > pr.diff
        env:
          GH_TOKEN: ${{ github.token }}
      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const diff = fs.readFileSync('pr.diff', 'utf8');
            // Format and post review
```

## Sample Reviews

This repo includes real review outputs:

| PR | Project | Result |
|----|---------|--------|
| [#1394](sample-reviews/1394.md) | Destructive command guard hook | Medium confidence |
| [#1393](sample-reviews/1393.md) | CHANGELOG generator SKILL | Medium confidence |

## How It Works

1. `claude-review` uses `gh` CLI to fetch PR metadata and diff
2. The output can be used as a structured template for Claude Code to fill in
3. Or consumed as JSON by other automation tools
4. The GitHub Action version posts reviews automatically on PR open/update

## Files

- `claude-review` — main CLI script (250+ lines Python)
- `.github/workflows/claude-review.yml` — GitHub Action workflow
- `sample-reviews/1394.md` — sample review output
- `sample-reviews/1393.md` — sample review output
- `README.md` — this file
