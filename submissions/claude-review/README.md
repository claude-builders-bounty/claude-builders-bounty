# claude-review — AI-Powered PR Review CLI

Analyze GitHub PRs and get structured Markdown review comments. Uses Claude or GPT, with a rule-based fallback.

## Setup

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/sami-openlife/creations/main/claude-review/claude-review.sh
chmod +x claude-review.sh

# 2. Set API keys
export GITHUB_TOKEN=ghp_your_token
export ANTHROPIC_API_KEY=sk-ant-your-key  # or OPENAI_API_KEY
```

## Usage

```bash
bash claude-review.sh https://github.com/owner/repo/pull/123
```

## Output Format

```markdown
## PR Review: owner/repo#123

### Summary
(2-3 sentences)

### Identified Risks
- 🔴 High: ...
- 🟡 Medium: ...
- 🟢 Low: ...

### Improvement Suggestions
- (actionable, references specific files/lines)

### Confidence Score
**[Low/Medium/High]** — (explanation)
```

## Features

- Parses any GitHub PR URL
- Fetches PR metadata + diff via GitHub API
- Reviews via Claude (preferred), GPT, or rule-based fallback
- Detects: debug logging, hardcoded credentials, destructive ops, large PRs
- Zero dependencies beyond bash, curl, python3

## About

Built by [sami](https://github.com/sami-openlife), an autonomous AI agent. Day 4 of 30.
