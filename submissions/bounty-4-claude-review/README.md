# claude-review — PR Reviewer powered by Claude

A zero-dependency CLI that fetches a GitHub PR diff, sends it to Claude, and returns a structured Markdown code review.

## Requirements

- Python 3.8+
- `ANTHROPIC_API_KEY` — get one at console.anthropic.com
- `GITHUB_TOKEN` — optional, but required for private repos and to avoid rate limits

## Setup (2 commands)

```bash
git clone https://github.com/leegier/claude-builders-bounty
cd claude-builders-bounty/submissions/bounty-4-claude-review
```

No `pip install` needed — pure stdlib.

## Usage

```bash
# Basic review
ANTHROPIC_API_KEY=sk-ant-... python claude-review.py --pr https://github.com/owner/repo/pull/42

# With GitHub token (avoids rate limits, required for private repos)
ANTHROPIC_API_KEY=sk-ant-... GITHUB_TOKEN=ghp_... python claude-review.py --pr https://github.com/owner/repo/pull/42

# Post review as a comment on the PR
ANTHROPIC_API_KEY=sk-ant-... GITHUB_TOKEN=ghp_... python claude-review.py --pr https://github.com/owner/repo/pull/42 --post
```

## Output Format

Every review returns exactly four sections:

```markdown
## Summary
2–3 sentences describing what the PR does.

## Identified Risks
- Security, performance, correctness, edge cases, breaking changes
- "No significant risks identified" if clean

## Improvement Suggestions
- Specific, actionable suggestions with line references where possible
- "Code looks clean — no suggestions" if nothing to add

## Confidence Score
**[Low / Medium / High]** — one sentence explaining why
```

## Sample Outputs

- [`sample-output-1.md`](sample-output-1.md) — Review of PR #205 (CHANGELOG generator)
- [`sample-output-2.md`](sample-output-2.md) — Review of PR #206 (pre-tool-use safety hook)

## How It Works

1. Parses the PR URL to extract `owner/repo/pr_number`
2. Fetches PR metadata (title, description) via GitHub REST API
3. Fetches the raw diff via `Accept: application/vnd.github.v3.diff`
4. Sends diff + metadata to `claude-haiku-4-5-20251001` with a structured prompt
5. Prints the review to stdout (and optionally posts it as a GitHub comment)

## GitHub Action (optional)

Add this workflow to auto-review every PR:

```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Review PR
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python submissions/bounty-4-claude-review/claude-review.py \
            --pr ${{ github.event.pull_request.html_url }} \
            --post
```

## Cost

Uses `claude-haiku-4-5-20251001` — the fastest and cheapest model. Typical PR review: ~$0.001–$0.003.
