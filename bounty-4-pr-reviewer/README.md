# claude-review

AI-powered PR reviewer using Claude Code. Gets a PR diff, analyzes it, outputs a structured Markdown review.

## Setup

```bash
# Requires: gh (GitHub CLI) + claude (Claude Code CLI)
cp claude-review.sh /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Usage

### CLI

```bash
# Review a GitHub PR by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Review by shorthand
claude-review --pr owner/repo#123

# Review a local diff file
claude-review --diff changes.diff
```

### GitHub Action

Copy `action.yml` to `.github/workflows/claude-review.yml` in your repo.

Add `ANTHROPIC_API_KEY` to your repo's secrets (Settings > Secrets > Actions).

The action runs on every PR open/update and posts a structured review comment.

## Output format

```markdown
### Summary
[2-3 sentences describing what this PR does]

### Identified Risks
- [Risk 1]
- [Risk 2]

### Improvement Suggestions
- [Suggestion 1 with file:line reference]
- [Suggestion 2]

### Confidence Score
[Low / Medium / High] — [reason]
```

## Sample outputs

See real reviews generated on actual PRs:
- [sample-output-1.md](./sample-output-1.md) — Review of a pre-tool-use hook PR
- [sample-output-2.md](./sample-output-2.md) — Review of a changelog generator PR

## How it works

1. Fetches PR diff via `gh pr diff`
2. Truncates to 500 lines if needed (keeps review focused)
3. Sends diff + PR metadata to Claude (sonnet model, $0.50 max budget)
4. Outputs structured Markdown review

## Stack

Bash + `gh` CLI + `claude` CLI. No other dependencies.
