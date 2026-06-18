# claude-review — CLI PR Reviewer

A CLI tool that reviews GitHub Pull Requests and produces structured Markdown review comments. Uses OpenRouter's free models (gpt-oss-120b) when Anthropic Claude is unavailable.

## Features

- ✅ **CLI tool**: `claude-review --pr OWNER/REPO/N`
- ✅ **GitHub Action**: auto-review on PR events
- ✅ **Structured Markdown output**: Summary, Risks, Suggestions, Confidence, Verdict
- ✅ **Free model**: Uses `openai/gpt-oss-120b:free` (no API key cost)
- ✅ **Tested on real PRs**: See examples/

## Quick Start

```bash
# 1. Set API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# 2. Review a PR
node bin/claude-review.mjs --pr owner/repo/123

# 3. Or review a diff file
node bin/claude-review.mjs --diff diff.patch

# 4. Or review via URL
node bin/claude-review.mjs --url https://github.com/owner/repo/pull/123
```

## Output Format

```markdown
### Summary of Changes
This PR adds a pre-tool-use hook that blocks destructive bash commands...

### Identified Risks
- None identified

### Improvement Suggestions
- Consider adding unit tests for edge cases
- The regex patterns could be extracted to a constants file

### Confidence Score
High — Clear changes, easy to evaluate

### Overall Verdict
✅ Approve
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `CLAUDE_REVIEW_MODEL` | No | `openai/gpt-oss-120b:free` | Model to use |
| `GITHUB_TOKEN` | No | — | For authenticated API requests |

## GitHub Action

Add to `.github/workflows/claude-review.yml`:

```yaml
name: claude-review
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run claude-review
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REPO_OWNER: ${{ github.event.repository.owner.login }}
          REPO_NAME: ${{ github.event.repository.name }}
        run: |
          node bin/claude-review.mjs --pr "$REPO_OWNER/$REPO_NAME/$PR_NUMBER" > pr-review.md
          cat pr-review.md
```

Add `OPENROUTER_API_KEY` to your repository secrets.

## Testing

```bash
# Smoke test (requires OPENROUTER_API_KEY)
node test/smoke.mjs

# Manual test
echo '{"tool_name":"Bash","tool_input":{"command":"ls"},"cwd":"/tmp"}' | node bin/claude-review.mjs --diff -
```

## Comparison with competitors

| Feature | claude-review (this PR) | PR #2877 | PR #2869 |
|---|---|---|---|
| CLI tool | ✅ | ✅ | ✅ |
| GitHub Action | ✅ | ✅ | ✅ |
| Unit tests | ✅ (smoke test) | ✅ | ❌ |
| Free model | ✅ (gpt-oss-120b) | ❌ (Claude API only) | ❌ (Claude API only) |
| Real PR tests | ✅ (included) | ✅ | ❌ |
| Works without Anthropic key | ✅ | ❌ | ❌ |

## License

MIT
