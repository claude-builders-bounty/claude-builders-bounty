# claude-review — AI-Powered PR Review Agent

> A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

Bounty #4 ($150) for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty).

## Features

- 🤖 Uses Claude `claude-sonnet-4-20250514` for intelligent code review
- 📋 Structured Markdown output: Summary, Risks, Suggestions, Confidence
- 🔗 Works with any GitHub PR via URL, shorthand, or number
- 💬 Optional `--post` flag to post review as PR comment
- 🔄 GitHub Action workflow included for automated reviews on every PR
- 📁 Saves review to local file for archival

## Quick Start

### CLI Usage

```bash
# Set required environment variables
export GITHUB_TOKEN=$(gh auth token)
export ANTHROPIC_API_KEY=sk-ant-...

# Review a PR by URL
node claude-review.mjs --pr https://github.com/owner/repo/pull/123

# Review by shorthand
node claude-review.mjs --pr owner/repo#123

# Review and post as comment
node claude-review.mjs --pr owner/repo#123 --post

# Review by number (requires --repo)
node claude-review.mjs --pr 123 --repo owner/repo

# Custom output directory
node claude-review.mjs --pr https://github.com/owner/repo/pull/123 --output ./my-reviews
```

### GitHub Action

1. Copy `.github/workflows/pr-review.yml` to your repo
2. Add `ANTHROPIC_API_KEY` to your repository secrets
3. Every new PR will automatically get an AI review comment

## Output Format

Every review follows this structure:

```markdown
# PR Review: [PR Title]

## 📋 Summary
2–3 sentences describing what the PR does and why.

## ⚠️ Risks
- Enumerated list of potential issues
- Security concerns, bugs, breaking changes

## 💡 Suggestions
- Concrete improvement ideas
- References specific files and patterns

## 🎯 Confidence: Low / Medium / High
```

## Sample Outputs

See `sample-outputs/` for reviews generated from real GitHub PRs:

- `review-claude-builders-bounty-2147.md` — Review of a safety hook PR
- `review-claude-builders-bounty-2149.md` — Review of a changelog generator PR

## Requirements

- Node.js 18+
- `gh` CLI authenticated (`gh auth login`)
- Anthropic API key with Claude access
- `curl` (for API calls)

## Installation

```bash
# No npm install needed — uses only Node.js built-ins + curl + gh
# Just download and run:
curl -O https://raw.githubusercontent.com/.../claude-review.mjs
chmod +x claude-review.mjs
```

## Acceptance Criteria

- [x] Works via CLI: `node claude-review.mjs --pr <url>`
- [x] GitHub Action workflow YAML included (`.github/workflows/pr-review.yml`)
- [x] Structured Markdown output with Summary, Risks, Suggestions, Confidence
- [x] Tested on 2 real GitHub PRs (sample outputs included)
- [x] README with setup and usage instructions
