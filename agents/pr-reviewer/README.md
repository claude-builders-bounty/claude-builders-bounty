# claude-review — PR Review Agent

A CLI tool that uses Claude to review GitHub pull requests and produce structured markdown feedback.

## Requirements

- Python 3.8+
- `ANTHROPIC_API_KEY` environment variable
- `GITHUB_TOKEN` environment variable (optional — avoids rate limits on public repos)

## Setup

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...   # optional but recommended
```

## Usage

```bash
python3 pr-review.py https://github.com/owner/repo/pull/123

# Save to file
python3 pr-review.py https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

Every review produces the same structured sections:

```markdown
## Summary
2-3 sentences describing what the PR does.

## Risks
- Potential bugs, security issues, unintended side effects

## Suggestions
- Concrete, actionable improvements

## Confidence
**Overall assessment**: Approve / Request Changes / Needs Discussion
**Confidence**: Low / Medium / High
**Reason**: One sentence explanation
```

## Sample Outputs

- [sample-output-1.md](sample-output-1.md) — Next.js feature PR (Request Changes)
- [sample-output-2.md](sample-output-2.md) — got bug fix PR (Approve)

## How it works

1. Fetches PR metadata and diff via GitHub API
2. Truncates diff to 12k chars if needed (handles large PRs)
3. Sends to `claude-sonnet-4-6` with a structured review prompt
4. Prints markdown to stdout (or file with `--output`)

## GitHub Action usage

```yaml
# .github/workflows/pr-review.yml
name: Claude PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 pr-review.py ${{ github.event.pull_request.html_url }} --output review.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - run: cat review.md >> $GITHUB_STEP_SUMMARY
```
