# Claude PR Review Agent

A CLI tool that analyzes a GitHub PR and produces a structured Markdown review comment.

## Setup (2 commands)

```bash
# Make executable
chmod +x claude-review

# Add to PATH (optional)
sudo ln -s $(pwd)/claude-review /usr/local/bin/claude-review
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Output is written to `pr-review-<number>.md` and printed to stdout.

## Output Structure

```markdown
# PR Review: #123

**PR**: https://github.com/owner/repo/pull/123
**Title**: ...
**Author**: @...
**Changes**: +X / -Y across Z file(s)

---

## Summary
Brief description of what the PR changes.

## Identified Risks
- **file.ts**: Auth/security-related change — verify no credentials are exposed

## Improvement Suggestions
- **file.ts**: Contains console.log statements — remove before production

## Confidence: High / Medium / Low
Assessment of how comprehensive the automated review is.
```

## Risk Detection

The agent checks for:
- Database schema/migration changes
- Auth/security-related code
- Configuration/environment changes
- Empty catch blocks
- `any` type usage
- Console.log statements
- TODO/FIXME markers
- Large PRs (500+ lines)

## Confidence Scoring

| Lines changed | Confidence |
|---------------|------------|
| < 100         | High       |
| 100-500       | Medium     |
| > 500         | Low        |

## Requirements

- `gh` CLI (authenticated)
- Python 3
- Bash

## GitHub Action

To use as a GitHub Action, create `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: |
          chmod +x agents/pr-review/claude-review
          agents/pr-review/claude-review --pr ${{ github.event.pull_request.html_url }} > review.md
          gh pr comment ${{ github.event.pull_request.number }} --body-file review.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
