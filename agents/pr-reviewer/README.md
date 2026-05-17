# claude-review

An AI-powered pull request reviewer that analyzes PR diffs and produces structured, actionable code reviews.

```
claude-review --pr https://github.com/owner/repo/pull/123
```

## Quick Start

### 1. Get an API key

You need an LLM API key. Any OpenAI-compatible chat endpoint works:

| Provider | Model | Env setup |
|----------|-------|-----------|
| **DeepSeek** (free tier) | `deepseek-chat` | `export LLM_API_KEY=sk-...` |
| **Anthropic Claude** | `claude-sonnet-4-20250514` | `export LLM_API_KEY=sk-ant-...` `export LLM_BASE_URL=https://api.anthropic.com/v1` |
| **OpenRouter** | `anthropic/claude-sonnet-4` | `export LLM_API_KEY=sk-or-...` `export LLM_BASE_URL=https://openrouter.ai/api/v1` |
| **OpenAI** | `gpt-4o` | `export LLM_API_KEY=sk-...` |

### 2. Set your GitHub token

```bash
export GITHUB_TOKEN=ghp_...  # needs repo scope
```

### 3. Run it

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

To save to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output

The review is a structured Markdown report:

```
# PR Review: Add user authentication middleware

**PR:** https://github.com/owner/repo/pull/123
**Author:** @user
**Changes:** +245/-32 across 5 files

---

## Summary
(2–3 sentences)

## Identified Risks
- Risk 1: ...
- Risk 2: ...

## Improvement Suggestions
- Suggestion 1: ...
- Suggestion 2: ...

## Confidence Score
**High**
(Brief explanation)
```

## GitHub Action

Add the workflow to your repo at `.github/workflows/pr-review.yml`:

```yaml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run review
        run: |
          curl -sL -o /usr/local/bin/claude-review \
            "https://raw.githubusercontent.com/<org>/claude-builders-bounty/main/agents/pr-reviewer/claude-review"
          chmod +x /usr/local/bin/claude-review
          claude-review --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --output review.md
          cat review.md >> $GITHUB_STEP_SUMMARY
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

Set `LLM_API_KEY` as a repository secret (Settings → Secrets and variables → Actions).

## Requirements

- **Python 3.10+** (stdlib only — no pip dependencies)
- A GitHub personal access token with `repo` scope
- An LLM API key

## How it works

1. Parses the PR URL to extract owner, repo, and PR number
2. Fetches PR metadata, file list, and raw diff from the GitHub API
3. Builds a structured analysis prompt
4. Sends the prompt to the configured LLM
5. Formats and outputs the structured review

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | — | GitHub PAT with `repo` scope |
| `LLM_API_KEY` | Yes | `DEEPSEEK_API_KEY` | LLM provider API key |
| `LLM_MODEL` | No | `deepseek-chat` | Model name |
| `LLM_BASE_URL` | No | `https://api.deepseek.com/v1` | API base URL |
