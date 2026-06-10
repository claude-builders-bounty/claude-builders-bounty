# claude-review — Claude Code PR Review Agent

A Claude Code agent that reviews GitHub pull requests and outputs structured Markdown.

## Install

```bash
# Requires: gh CLI (authenticated), Claude Code
cp claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr https://github.com/owner/repo/pull/123 --context "Focus on SQL injection risks"
```

## Sample Output

### Summary
This PR adds server-side pagination to the `/api/users` endpoint, replacing the
previous client-side approach. It introduces a `cursor` parameter and returns
`nextCursor` in the response for infinite scroll support.

### Identified Risks
- **Risk**: The `cursor` value is passed directly to the SQL query without
  sanitization — potential for cursor-based injection if the cursor comes from
  an untrusted source.
- **Risk**: Missing `LIMIT` upper bound — a malicious client could request
  `limit=999999`, causing memory exhaustion.

### Improvement Suggestions
- **Suggestion**: Validate `cursor` against expected format (UUID or base64
  encoded timestamp) before passing to the query.
- **Suggestion**: Add `Math.min(limit, 100)` server-side cap.
- **Suggestion**: Consider adding a `total` count in the first page response
  so the client can show "Showing 1-100 of 5000".

### Confidence Score
**Score**: Medium
**Reason**: The core logic is sound, but the SQL injection risk and missing
limit cap need attention before production deployment.

---

## GitHub Action (Optional)

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Claude Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          claude-review --pr "${{ github.event.pull_request.html_url }}" |
          gh pr comment "${{ github.event.pull_request.html_url }}" --body-file -
```

## Requirements

- `gh` CLI (GitHub CLI) — authenticated
- `claude` CLI (Claude Code)
- Bash 4+