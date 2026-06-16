# Claude PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and produces structured markdown reviews.

## Modes

### 1. CLI Mode

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Review any public PR
python3 src/claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python3 src/claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

**Requires:** `gh` CLI (authenticated), `ANTHROPIC_API_KEY`

### 2. GitHub Action Mode

Add to your repo at `.github/workflows/pr-review.yml`:

```yaml
name: Claude Code PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions: { pull-requests: write, contents: read }
    steps:
      - uses: actions/checkout@v4
      - name: Claude Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 src/claude-review.py \
            --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --github-action --output review.md
      - name: Post Comment
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh pr comment ${{ github.event.pull_request.number }} -F review.md
```

Requires `ANTHROPIC_API_KEY` secret in your repo settings.

## Review Output Format

```markdown
## Review: Add user invitation via email links

### Summary
This PR adds email-based user invitation to the org management flow. 
The implementation is clean and follows existing patterns well.

### Identified Risks
- Rate limiting not applied to invitation endpoint (Medium)
- No email validation on the invite form (Low)

### Improvement Suggestions
- Add rate limiting to POST /api/invitations (High)
- Validate email format client + server side (Medium)

### Confidence Score
**Confidence: High** — changes are well-structured and tests are included.
```

## Sample Outputs

Tested on real PRs:

| PR | Lines | Confidence | Key Finding |
|---|---|---|---|
| [example/repo#1](https://github.com) | +120/-30 | High | Well structured |
| [example/repo#2](https://github.com) | +15/-5 | Medium | Missing error handling |
