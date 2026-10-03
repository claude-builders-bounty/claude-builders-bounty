# claude-review

A Claude Code sub-agent that reviews a GitHub PR and posts a structured Markdown comment.

## Features

- CLI tool: `claude-review <pr-url>`
- GitHub Action support for automated reviews on every PR
- Structured output: Summary, Risks, Improvement Suggestions, Confidence Score
- Works with the Anthropic Claude API

## Installation

```bash
npm install
```

## Configuration

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
```

The `GITHUB_TOKEN` needs `repo` scope for accessing PR data.

## Usage

### CLI

```bash
# Review a PR and print to stdout
npx claude-review https://github.com/owner/repo/pull/123

# Save to a specific file
npx claude-review https://github.com/owner/repo/pull/123 -o review.md

# Output only the Markdown comment (for scripting)
npx claude-review https://github.com/owner/repo/pull/123 --comment-only
```

### GitHub Action

Add the workflow file to your repository at `.github/workflows/review-pr.yml`:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]
  workflow_dispatch:
    inputs:
      pr_url:
        description: "GitHub PR URL to review"
        required: true
        type: string

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run Claude PR Review
        id: review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_URL: ${{ github.event.inputs.pr_url || github.event.pull_request.html_url }}
        run: |
          REVIEW=$(node src/claude-review.js "$PR_URL" --comment-only)
          echo "review<<EOF" >> $GITHUB_OUTPUT
          echo "$REVIEW" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT
      - name: Post review comment
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const review = process.env.REVIEW || `${{ steps.review.outputs.review }}`;
            const prNumber = context.issue.number;
            const owner = context.repo.owner;
            const repo = context.repo.repo;
            const { data: existingComments } = await github.rest.issues.listComments({ owner, repo, issue_number: prNumber });
            const botComment = existingComments.find(c => c.user?.login === 'github-actions[bot]' && c.body?.includes('## Summary'));
            const commentBody = `## Summary\n${review}\n\n---\n*Reviewed by **Claude PR Review Agent** · powered by [Opire](https://opire.dev)*`;
            if (botComment) {
              await github.rest.issues.updateComment({ owner, repo, comment_id: botComment.id, body: commentBody });
            } else {
              await github.rest.issues.createComment({ owner, repo, issue_number: prNumber, body: commentBody });
            }
```

Add secrets to your repository:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions |

## Output Format

The review is structured Markdown with these sections:

```markdown
## Summary
[2-3 sentences summarizing the purpose and scope of the changes]

## Identified Risks
- [risk 1]
- [risk 2]

## Improvement Suggestions
- [suggestion 1]
- [suggestion 2]

## Confidence Score
[Low / Medium / High]
```

## Testing

Run the test suite:

```bash
npm test
```

Sample review outputs are available in `tests/samples/`.

## Architecture

```
src/
├── claude-review.js   # CLI entry point (Commander)
├── config.js          # Environment & API configuration
├── github.js          # GitHub API client (PR info, diff, files)
├── prompts.js         # Claude prompt template builder
└── reviewer.js        # Anthropic API integration
output/                # Generated review files
tests/
├── samples/           # Sample review outputs from real PRs
└── verify-reviews.js  # Test runner
