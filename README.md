# Claude Code PR Review Agent

A CLI agent that analyzes GitHub PR diffs and returns structured Markdown reviews using Claude.

## Setup

1. Ensure `gh` CLI is authenticated (`gh auth login`)
2. Ensure `claude` CLI is installed and configured with API access
3. Make the script executable: `chmod +x claude-review.sh`

## Usage

```bash
# Review by PR URL
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Review by PR number + repo
./claude-review.sh --pr 123 --repo owner/repo
```

## Output Format

The agent returns structured Markdown with:
- **Summary**: 2-3 sentence overview of changes
- **Risks**: Bulleted list of potential issues
- **Suggestions**: Bulleted improvement recommendations
- **Confidence**: Low / Medium / High assessment

## Sample Outputs

See `samples/` directory for example reviews on real PRs.

## Payout Address

Solana: `877hj5d4ya4N2B5gPsazm1dudN61Fkjz1V9izhD5m2TU`
