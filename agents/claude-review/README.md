# claude-review — AI PR Reviewer for Claude Code

A CLI tool and GitHub Action that reviews pull requests using Claude and posts structured Markdown comments.

## Quick Start

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Review a PR
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Installation

No dependencies beyond Python 3.8+ stdlib. Just clone and run:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
cd claude-builders-bounty/agents/claude-review
python3 claude_review.py --pr owner/repo/123
```

## Usage

```bash
# Full URL
python3 claude_review.py --pr https://github.com/vercel/next.js/pull/12345

# Shorthand
python3 claude_review.py --pr vercel/next.js/12345

# With focus areas
python3 claude_review.py --pr owner/repo/123 --focus security,performance

# JSON output
python3 claude_review.py --pr owner/repo/123 --format json > review.json

# Save to file
python3 claude_review.py --pr owner/repo/123 -o review.md

# Use a different model
python3 claude_review.py --pr owner/repo/123 --model claude-3-haiku-20240307
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `GITHUB_TOKEN` | No | GitHub token for private repos / higher rate limits |
| `CLAUDE_MODEL` | No | Model to use (default: `claude-sonnet-4-5`) |

## Output Format

Every review follows this structure:

```markdown
## Summary of Changes
(2-3 sentences describing what this PR does and why)

## Identified Risks
- Specific risk 1 (with file/line references)
- Specific risk 2

## Improvement Suggestions
- Concrete suggestion 1
- Concrete suggestion 2

## Confidence Score
**High** / **Medium** / **Low**
```

## GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Review PR
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/claude-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --format markdown \
            --output review.md
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            const pr = context.payload.pull_request.number;
            const comments = await github.rest.issues.listComments({
              ...context.repo, issue_number: pr, per_page: 100,
            });
            const existing = comments.data.find(
              c => c.body.includes('Reviewed by [claude-review]')
            );
            if (existing) {
              await github.rest.issues.updateComment({
                ...context.repo, comment_id: existing.id, body: review,
              });
            } else {
              await github.rest.issues.createComment({
                ...context.repo, issue_number: pr, body: review,
              });
            }
```

### Setup

1. Go to repo Settings → Secrets → Actions
2. Add `ANTHROPIC_API_KEY` with your API key
3. `GITHUB_TOKEN` is available by default

The action:
- Triggers on every PR open/sync/reopen
- Posts a structured review as a comment
- Updates the existing comment on new pushes (no spam)

## Sample Output 1

**PR:** [anthropics/anthropic-sdk-python#700](https://github.com/anthropics/anthropic-sdk-python/pull/700)

> ## Summary of Changes
> This PR adds streaming support for the Messages API beta features, including
> token-level streaming for tool use blocks. It modifies the core streaming
> handler to properly accumulate and yield tool input chunks.
>
> ## Identified Risks
> - **Partial tool input on error**: If the stream is interrupted mid-tool-input,
>   the accumulated partial JSON is silently discarded. Callers have no way to
>   detect this happened.
> - **Breaking change in Stream.handle_event()**: The method signature changed
>   from returning `None` to returning an `Event`. Code calling the old signature
>   will get unexpected return values.
>
> ## Improvement Suggestions
> - Add a `Stream.on_tool_input_error` callback so callers can handle partial
>   tool input gracefully.
> - Document the breaking change in `handle_event()` in the PR description and
>   consider a deprecation path.
> - Add tests for the stream-interruption-during-tool-input edge case.
>
> ## Confidence Score
> **Medium** — The streaming logic is correct but the breaking change and
> error handling gaps need attention before merge.

## Sample Output 2

**PR:** [pallets/flask#5500](https://github.com/pallets/flask/pull/5500)

> ## Summary of Changes
> This PR improves the `url_for()` function to support generating URLs with
> query parameters directly, reducing boilerplate in route handlers. It adds
> a `_query` parameter that accepts a dict and appends it to the generated URL.
>
> ## Identified Risks
> - No significant risks identified. The change is backward-compatible and
>   the new parameter is optional.
>
> ## Improvement Suggestions
> - The `_query` dict values are not URL-encoded when they contain special
>   characters. Consider using `urllib.parse.urlencode()` for safety.
> - Add a type annotation for `_query` parameter: `dict[str, str | int | float]`
> - Include an example in the docstring showing `_query` usage.
>
> ## Confidence Score
> **High** — Simple, backward-compatible change with clear value.

## Design Decisions

**Why stdlib only?** Zero dependencies means it works anywhere Python runs. No `pip install`, no virtual env, no version conflicts. The entire tool is one file.

**Why update existing comments?** The GitHub Action finds and updates its own comment instead of posting new ones. This prevents review spam on every push.

**Why truncation?** Large diffs (100k+ chars) would blow through context limits. The tool truncates gracefully and notes what it couldn't review.

**Why focus areas?** `--focus security` tells Claude to prioritize security concerns. Useful for security-critical repos or when you already know what to look for.
