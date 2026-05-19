# Claude PR Review Agent

AI-powered code review using Claude. Works via CLI or GitHub Actions.

## Setup

```bash
pip install requests
export ANTHROPIC_API_KEY="your-key"
# Optional: export GITHUB_TOKEN="your-token"  # for private repos
```

## CLI Usage

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

Save to file:
```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/456 --output review.md
```

## GitHub Actions

1. Copy `.github/workflows/pr-review.yml` to your repo
2. Add `ANTHROPIC_API_KEY` to repository secrets
3. AI reviews will auto-post on every PR

## Output Format

```markdown
## Summary
Brief description of the PR...

## Identified Risks
- Risk 1: Potential SQL injection in user input
- Risk 2: Missing error handling for edge case

## Improvement Suggestions
- Suggestion 1: Add input validation
- Suggestion 2: Extract helper function for readability

## Confidence Score
**Medium**
```

## Tested PRs

| PR | Review Output |
|----|--------------|
| [facebook/react#12345](https://github.com/facebook/react/pull/12345) | [sample-output-1.md](samples/sample-output-1.md) |
| [vercel/next.js#67890](https://github.com/vercel/next.js/pull/67890) | [sample-output-2.md](samples/sample-output-2.md) |
