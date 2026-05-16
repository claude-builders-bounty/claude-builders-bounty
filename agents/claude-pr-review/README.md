# Claude PR Review Agent

Zero-dependency CLI agent that fetches a GitHub pull request diff and prints a
structured Markdown review comment.

## Setup

```bash
export PATH="$PWD/agents/claude-pr-review:$PATH"
claude-review --pr https://github.com/owner/repo/pull/123
```

For private repositories or higher API limits, set `GITHUB_TOKEN` before
running the command.

## Claude Code Sub-Agent

This PR includes a project sub-agent at
`.claude/agents/pr-reviewer.md`. In Claude Code, ask the `pr-reviewer`
sub-agent to review a pull request URL. It runs the local CLI and returns the
structured Markdown review.

To post the generated review back to the pull request, provide a `GITHUB_TOKEN`
with comment permission and use:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --comment
```

## Output

The review always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

This agent intentionally uses deterministic heuristics instead of a paid API, so
it can run in local Claude Code workflows and GitHub Actions without additional
secrets.

## GitHub Action

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate structured PR review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-pr-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            > claude-pr-review.md
          cat claude-pr-review.md
      - name: Post structured review comment
        if: github.event.pull_request.head.repo.full_name == github.repository
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-pr-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --comment
```

## Sample Runs

- [sample-code-server-1309.md](samples/sample-code-server-1309.md)
- [sample-waymark-1.md](samples/sample-waymark-1.md)

These were generated from real pull requests with:

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1309 > agents/claude-pr-review/samples/sample-code-server-1309.md
claude-review --pr https://github.com/XenomorphingTV/waymark/pull/1 > agents/claude-pr-review/samples/sample-waymark-1.md
```

## Verification

```bash
export PATH="$PWD/agents/claude-pr-review:$PATH"
python3 -m unittest discover agents/claude-pr-review/tests
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1309
GITHUB_TOKEN=... claude-review --pr https://github.com/owner/repo/pull/123 --comment
```
