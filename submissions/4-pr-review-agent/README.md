# 🤖 Claude Code PR Review Sub-Agent

**Bounty:** [#4 — AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)
**Reward:** $150
**Status:** ✅ Submitted

## Overview

A Claude Code sub-agent that analyzes Pull Request diffs and generates structured Markdown reviews. Supports both CLI and GitHub Action workflows.

## Features

- 🔍 Analyzes PR diffs using GitHub API
- 📊 Generates structured review: Summary, Risks, Improvements, Confidence Score
- 🚀 Works as CLI tool or automated GitHub Action
- 🎨 Colorized terminal output
- 💾 Save reviews to file for CI pipelines

## Quick Start

### CLI Mode

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_xxx"

# Review any PR
bash claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save to file
bash claude-review.sh --pr https://github.com/owner/repo/pull/456 --output review.md
```

### GitHub Action Mode

Copy `.github/workflows/pr-review.yml` to your repo. The action automatically:
1. Triggers on new PRs
2. Fetches the diff
3. Runs the review
4. Posts the result as a PR comment
5. Adds a `🤖 reviewed` label

## Output Format

The review includes:

```markdown
# 🔍 PR Review

## 📋 Summary
- Repository stats, branch info, PR metadata

## 📂 Files Changed
- +125/−43 lines across 5 files

## 🔬 Code Review
### ✅ Strengths
### ⚠️ Identified Risks (table)
### 💡 Improvement Suggestions

## 📊 Review Confidence
**Medium** 🟡 - Automated review
```

## Tested PRs

1. ✅ **claude-builders-bounty/claude-builders-bounty#1** — CHANGELOG skill PR
2. ✅ **claude-builders-bounty/claude-builders-bounty#3** — Hook PR

## Files

- `claude-review.sh` — Main CLI script
- `.github/workflows/pr-review.yml` — GitHub Action config
- `README.md` — This file
