# claude-review — AI-powered PR Review Agent

**Bounty #4** — $150 | [claude-builders-bounty/claude-builders-bounty#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A Claude Code agent that reviews GitHub PRs and posts structured Markdown reviews.
Works as a CLI tool or as a GitHub Action.

## Features

- Fetches PR diff directly from GitHub API
- Structured review with: Summary, Risk Assessment, Risks, Suggestions, Confidence Score, Verdict
- Works on any public repo (or private with `GITHUB_TOKEN`)
- GitHub Action included — auto-posts review as PR comment
- Supports any Claude model (defaults to `claude-haiku-4-5-20251001` for cost efficiency)

## Setup (CLI)

**1. Set your API key**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...  # Optional but recommended
```

**2. Download the script**
```bash
curl -O https://raw.githubusercontent.com/guidou2013-bot/claude-builders-bounty/main/submissions/pr-reviewer/claude-review.sh
chmod +x claude-review.sh
```

**3. Run it**
```bash
bash claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Review a PR, print to stdout
bash claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save review to file
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md

# Use a specific model (default: claude-haiku-4-5-20251001)
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-6

# Limit diff size (default: 80000 chars)
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --max-diff 40000
```

## Setup (GitHub Action)

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Review PR with Claude
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sO https://raw.githubusercontent.com/guidou2013-bot/claude-builders-bounty/main/submissions/pr-reviewer/claude-review.sh
          bash claude-review.sh \
            --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --output review.md
          echo "REVIEW<<EOF" >> $GITHUB_ENV
          cat review.md >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV
      - uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: process.env.REVIEW
            });
```

Then add `ANTHROPIC_API_KEY` to your repo secrets.

## Output Format

```markdown
# PR Review: <title>

**PR:** [owner/repo#123](url)
**Reviewed:** 2026-03-29T18:45:00Z
**Model:** claude-haiku-4-5-20251001

---

## Summary
[2-3 sentences]

## Risk Assessment: Low / Medium / High
[One sentence rationale]

## Identified Risks
- Risk 1
- Risk 2

## Improvement Suggestions
- Suggestion 1
- Suggestion 2

## Confidence Score: Low / Medium / High
[One sentence]

## Verdict
APPROVE / REQUEST CHANGES / COMMENT — [rationale]
```

## Sample Reviews

- [sample_review_1.md](./sample_review_1.md) — pydantic/pydantic#12989 (documentation PR)
- [sample_review_2.md](./sample_review_2.md) — vitejs/vite#22070 (documentation PR)

## Requirements

- bash 4+
- curl
- python3 (standard on all systems)
- `ANTHROPIC_API_KEY` environment variable

## Cost

Using `claude-haiku-4-5-20251001` (default):
- Typical PR review: ~2,000 input tokens + ~400 output = **< $0.001 per review**

## License

MIT
