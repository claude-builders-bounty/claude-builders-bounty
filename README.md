# claude-review — Claude Code PR Reviewer

A **Claude Code sub-agent** that reviews GitHub PRs and posts structured Markdown comments.

## Features

- **CLI**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Automatic review on every PR
- **Structured output**: Summary, risks, suggestions, confidence score
- **Powered by Claude**: Uses Claude Code (`claude -p`) for deep analysis
- **No API keys needed**: Uses your existing Claude Code setup

## CLI Usage

```bash
# Install
curl -sLO https://raw.githubusercontent.com/Andyyook/claude-builders-bounty/main/claude-review.py
chmod +x claude-review.py

# Review a PR
export GITHUB_TOKEN="ghp_xxx"
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Write to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Short form
python3 claude-review.py --pr 123 --repo owner/repo
```

### Output

```markdown
> Reviewed by **claude-review** · https://github.com/owner/repo/pull/123
>
> _2026-06-18 12:00 UTC_

## Review: PR title

### Summary
...

### Identified Risks
- ...

### Improvement Suggestions
- ...

### Confidence Score
**High**
```

## GitHub Action

Add `.github/workflows/claude-review.yml` to your repo:

```yaml
name: Claude Code PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Andyyook/claude-builders-bounty/.github/actions/claude-review@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Requirements

- **Claude Code** installed (`npm install -g @anthropic-ai/claude-code`)
- **GitHub token** with `repo` scope for private repos (public repos work without a token)

## Sample Reviews

See [sample-reviews/](sample-reviews/) for example outputs tested on real PRs.
