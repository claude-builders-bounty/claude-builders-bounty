# Claude PR Review Agent

A CLI tool and GitHub Action that uses Claude to analyze GitHub PRs and produce structured review comments.

## Features

- Fetches PR diffs directly from GitHub API
- Structured Markdown output with summary, risks, suggestions, and confidence score
- Posts reviews as GitHub PR comments
- Works as CLI tool or GitHub Action
- No dependencies beyond Python 3.8+ stdlib

## Quick Setup (2 commands)

```bash
export ANTHROPIC_API_KEY=your-key-here
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

### CLI

```bash
# Review a PR and post comment (requires GITHUB_TOKEN)
export GITHUB_TOKEN=ghp_...
export ANTHROPIC_API_KEY=sk-ant-...
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Review and print only (no comment posted)
python claude-review.py --pr owner/repo/123 --no-post

# Review from a local diff file
python claude-review.py --pr owner/repo/123 --diff-file changes.diff

# Output as JSON
python claude-review.py --pr owner/repo/123 --output json --no-post
```

### GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run Claude PR Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python agents/pr-reviewer/claude-review.py --pr "${{ github.event.pull_request.html_url }}"
```

**Required secrets:**
- `ANTHROPIC_API_KEY` — Your Anthropic API key
- `GITHUB_TOKEN` — Automatically provided by GitHub Actions

## Output Format

```markdown
## 🔍 PR Review: https://github.com/owner/repo/pull/123

**Confidence:** High

### Summary
This PR adds user authentication using JWT tokens. It implements login/logout endpoints
and middleware for protecting routes.

### ⚠️ Identified Risks
- Risk 1: JWT secret is hardcoded in config — should use environment variable
- Risk 2: No token expiration handling

### 💡 Suggestions
- Suggestion 1: Add rate limiting to login endpoint
- Suggestion 2: Implement token refresh mechanism

---
*Reviewed by claude-review using Claude*
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `GITHUB_TOKEN` | For posting | GitHub token with PR comment permissions |
