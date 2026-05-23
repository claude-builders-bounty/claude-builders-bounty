# claude-review — AI-Powered PR Review Agent

An AI agent that reviews pull requests and posts structured Markdown comments. Works as a CLI tool or GitHub Action.

## Features

- 🔍 **Fetches PR diff** via GitHub API
- 🤖 **AI-powered analysis** using any OpenAI-compatible LLM
- 📋 **Structured output** — summary, risks, suggestions, confidence score
- ⚡ **GitHub Action** — runs automatically on PR events

## Quick Start

### 1. Set up environment variables

```bash
export GITHUB_TOKEN="your_github_token"
export LLM_API_KEY="your_llm_api_key"
export LLM_API_BASE="https://api.deepseek.com/v1"   # default
export LLM_MODEL="deepseek-chat"                     # default
```

### 2. Run

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### 3. Post to GitHub

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 | gh pr comment 123 -F -
```

Or save to file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Copy `.github/workflows/claude-review.yml` to your repo. The action:

- Triggers on `pull_request` events (opened, synchronize)
- Runs `claude-review` on the PR
- Posts the result as a PR comment

**Required secrets:**
- `GITHUB_TOKEN` — auto-provided by Actions
- `LLM_API_KEY` — your LLM API key

## Output Format

```markdown
## 🤖 AI Code Review

### Summary
2–3 sentence summary of what this PR changes.

### Identified Risks
- Risk description and explanation

### Improvement Suggestions
- Concrete, actionable suggestion

### Confidence Score
Low / Medium / High
```

## Requirements

- Python 3.8+
- A GitHub token with `pull_requests: read` scope
- An LLM API key (DeepSeek, OpenAI, or any compatible provider)