# claude-review — PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and outputs structured Markdown analysis with summary, risks, suggestions, and confidence score.

Works as a **CLI tool** and as a **GitHub Action**.

## CLI Usage

```bash
# Review by URL
bash agents/pr-review/claude-review.sh --pr https://github.com/owner/repo/pull/123

# Review by shorthand
bash agents/pr-review/claude-review.sh --pr owner/repo#123

# Review by number (uses current repo)
bash agents/pr-review/claude-review.sh --pr 123
```

### Requirements

- `gh` CLI (authenticated)
- One of: `claude` CLI (Claude Code) or `ANTHROPIC_API_KEY` environment variable

## GitHub Action Usage

1. Copy `workflow.yml` to `.github/workflows/claude-review.yml` in your repo
2. Add `ANTHROPIC_API_KEY` to your repo's secrets
3. Every PR will automatically receive a structured review comment

```yaml
# .github/workflows/claude-review.yml
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
      - uses: claude-builders-bounty/claude-builders-bounty/agents/pr-review@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Output format

Every review follows this structure:

```markdown
### Summary
2-3 sentences describing what the PR does.

### Identified Risks
- 🔴 High / 🟡 Medium / 🟢 Low — description

### Improvement Suggestions
- Specific, actionable suggestions with code references

### Confidence Score
Low / Medium / High — one-line justification
```

## Sample outputs

Two real PR reviews are included:

- [sample-output-1.md](sample-output-1.md) — Review of a PreToolUse safety hook
- [sample-output-2.md](sample-output-2.md) — Review of a CHANGELOG generator

## Design decisions

- **Truncates diffs at 500 lines** to stay within token limits while capturing the important parts
- **Tries `claude` CLI first**, falls back to direct API — works in both local and CI environments
- **Structured output enforced via prompt** — consistent format every time
- **No dependencies** beyond `gh`, `bash`, and `python3` (for JSON parsing)
