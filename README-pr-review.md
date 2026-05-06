# claude-review — AI-Powered PR Code Review via Claude Code

A CLI tool that takes a GitHub PR URL, fetches the diff, and runs Claude Code to produce a structured Markdown code review.

**Bounty:** [#4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Prerequisites

- [GitHub CLI](https://cli.github.com/) (`gh`) — authenticated
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`claude`) — installed and authenticated
- Bash 4+

## Quick Start

```bash
# Make executable
chmod +x claude-review

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123

# With a specific model
CLAUDE_MODEL=claude-opus-4-7 ./claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
./claude-review --pr https://github.com/owner/repo/pull/123 > review.md
```

## Output Format

Structured Markdown with four sections:

| Section | Content |
|---------|---------|
| **Summary** | 2–3 sentence summary of what changed and why |
| **Identified Risks** | Bullet list of security, performance, correctness, and breaking-change risks |
| **Improvement Suggestions** | Bullet list of actionable code quality suggestions |
| **Confidence Score** | Low / Medium / High with explanation |

## How It Works

1. Parses the GitHub PR URL to extract owner, repo, and PR number
2. Fetches PR diff via `gh pr diff`
3. Constructs a structured prompt with reviewer instructions
4. Pipes to `claude` CLI for analysis
5. Outputs formatted Markdown to stdout

## GitHub Action (Alternative)

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Claude Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ./claude-review --pr "${{ github.event.pull_request.html_url }}" > review.md
          gh pr comment "${{ github.event.pull_request.html_url }}" --body-file review.md
```

## Sample Outputs

See [`samples/`](samples/) for reviews of real PRs.

## License

MIT
