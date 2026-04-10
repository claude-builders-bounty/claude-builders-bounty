# PR Review Agent — claude-builders-bounty#4

**Bounty:** $150 — powered by [Opire](https://opire.dev)  
**Issue:** [claude-builders-bounty#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A Claude Code agent that takes a PR diff as input, analyzes it with the Claude API, and returns a structured Markdown review comment.

## Features

- **CLI tool**: `claude-review --pr <url>` — review any public GitHub PR
- **GitHub Action**: posts review as a PR comment automatically
- **Structured output**: Summary / Risks / Suggestions / Confidence Score
- **Streaming**: review prints as Claude generates it

## CLI Usage

```bash
# Review a PR by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Review a PR by number
claude-review --pr 123 --repo owner/repo

# Review a local .diff file
claude-review --diff ./my-changes.diff

# Post review as a GitHub PR comment
claude-review --pr 123 --repo owner/repo --output comment
```

## GitHub Action Usage

Add this to your workflow file (e.g., `.github/workflows/pr-review.yml`):

```yaml
name: Claude PR Review

on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install & Run Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: |
          npm install -g @teapoyy/pr-review-agent
          claude-review --pr ${{ github.event.pull_request.html_url }} --output comment
```

Or reference the action from this repo directly.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CLAUDE_API_KEY` | Always | Anthropic API key |
| `GITHUB_TOKEN` | For `--pr` mode | GitHub PAT with `repo` scope |

## Setup & Installation

```bash
# From this repo
npm install
npm run build

# Or install globally
npm install -g .
claude-review --pr 123 --repo owner/repo
```

## Output Format

````markdown
## Claude Code PR Review

### Summary
This PR adds user authentication via OAuth2, integrating with GitHub and Google providers. It introduces a new auth service, updates the user schema, and adds login/logout endpoints.

### Risks
- OAuth tokens are stored in plaintext in the session — consider encrypting at rest
- No rate limiting on the `/auth/login` endpoint — brute force risk
- New dependency on `passport-github2` — verify it has no known vulnerabilities

### Suggestions
- Add integration tests for the OAuth callback flow
- Document the new environment variables in `.env.example`
- Consider adding a `User.authProviders` array to support multiple OAuth providers per user

**Confidence Score:** High
````

## Acceptance Criteria

- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action workflow YAML included
- [x] Structured Markdown output with: Summary, Risks, Suggestions, Confidence Score
- [x] README with setup and usage instructions
