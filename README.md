# Claude Code PR Review Agent

Automated code review powered by Claude AI.

## CLI Usage

```sh
# Install
pip install -r requirements.txt
chmod +x claude-review

# Review a PR
export CLAUDE_API_KEY=sk-ant-...
./claude-review --pr https://github.com/owner/repo/pull/123

# Review from a local diff
./claude-review --diff changes.diff

# Pipe a diff
git diff main...feature | ./claude-review

# Save output to file
./claude-review --pr https://github.com/owner/repo/pull/123 -o review.md
```

## GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
- uses: tylerLi0/claude-builders-bounty/.github/actions/claude-review@main
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
```

Add `CLAUDE_API_KEY` repo secret in Settings → Secrets → Actions.

## Output Format

### Summary
2-3 sentence overview of the PR's purpose and approach.

### Identified Risks
Potential issues including security, performance, and correctness concerns.

### Improvement Suggestions
Actionable recommendations for code quality and maintainability.

### Confidence Score
**Low / Medium / High** — based on diff size, coverage, and pattern clarity.

## Requirements

- Python 3.10+
- Claude API key ([get one here](https://console.anthropic.com))
- GitHub token (optional, for private repos)

## Sample Outputs

See `sample-output-1.md` and `sample-output-2.md` for example reviews on real PRs.
