# claude-review

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![Shell: Bash](https://img.shields.io/badge/Shell-Bash-green.svg)](https://www.gnu.org/software/bash/)
[![GitHub Action](https://img.shields.io/badge/GitHub-Action-2088FF.svg)](https://github.com/features/actions)

Automated pull request reviewer powered by Claude Code. Analyzes a GitHub PR diff and produces a structured Markdown review with a summary, risks, suggestions, and a confidence score.

Works as a **CLI tool** and as a **GitHub Action**.

---

## Quick Install

```bash
# Clone the repository
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/bounty-4-pr-review-agent

# Make the CLI executable
chmod +x claude-review

# (Optional) Add to PATH
ln -s "$(pwd)/claude-review" ~/.local/bin/claude-review
```

### Prerequisites

| Tool | Install |
|------|---------|
| [GitHub CLI](https://cli.github.com/) (`gh`) | `brew install gh` / `apt install gh` |
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`) | `npm install -g @anthropic-ai/claude-code` |

Both must be authenticated before use:
```bash
gh auth login
```

---

## CLI Usage

```bash
# Review a PR — output goes to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Review and post the result as a PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Save to a file
claude-review --pr https://github.com/owner/repo/pull/123 > review.md
```

### Options

| Flag | Description |
|------|-------------|
| `--pr <url>` | **(required)** GitHub pull request URL |
| `--post` | Post the review as a comment on the PR |
| `--version` | Print version and exit |
| `--help` | Show usage information |

---

## GitHub Action

Add the workflow to any repository to get automated reviews on every pull request.

### Setup

1. Copy `.github/workflows/pr-review.yml` into your repository's `.github/workflows/` directory.
2. Add `ANTHROPIC_API_KEY` to your repository secrets (**Settings > Secrets and variables > Actions**).
3. The action triggers automatically on `pull_request` events (`opened`, `synchronize`, `reopened`).

### Workflow file

```yaml
# .github/workflows/pr-review.yml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - name: Install Claude Code CLI
        run: npm install -g @anthropic-ai/claude-code

      - name: Fetch PR diff
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr view ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,files \
            > /tmp/pr-metadata.json
          gh pr diff ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} > /tmp/pr-diff.txt

      - name: Run Claude review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Build prompt from metadata + diff (see review.sh for full logic)
          claude -p --output-format text < /tmp/review-prompt.txt > /tmp/review-output.md

      - name: Post review comment
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --body-file /tmp/review-output.md
```

> The full workflow with prompt construction is in [`.github/workflows/pr-review.yml`](.github/workflows/pr-review.yml).

---

## Output Format

Every review follows this structure:

```markdown
## Summary
2-3 sentence overview of the changes.

## Risks
- Risk 1
- Risk 2

## Suggestions
- Suggestion 1
- Suggestion 2

## Confidence
**High** / **Medium** / **Low**

Justification sentence.
```

---

## Sample Reviews

Reviews generated against real open-source PRs:

| PR | Repository | Review |
|----|-----------|--------|
| [cal.com#28636](https://github.com/calcom/cal.com/pull/28636) | calcom/cal.com | [sample-1.md](samples/sample-1.md) |
| [highlight#10353](https://github.com/highlight/highlight/pull/10353) | highlight/highlight | [sample-2.md](samples/sample-2.md) |

---

## How It Works

1. Parses the PR URL to extract `owner/repo` and PR number.
2. Fetches PR metadata (title, description, files changed, additions/deletions) via `gh`.
3. Fetches the full diff via `gh pr diff`.
4. Truncates the diff to 1500 lines if needed to stay within context limits.
5. Sends the metadata + diff to Claude Code with a structured prompt.
6. Returns the formatted Markdown review.

---

## Compatibility

| Platform | Status |
|----------|--------|
| Linux (x86_64, ARM64) | Supported |
| macOS (Intel, Apple Silicon) | Supported |
| Windows (WSL2) | Supported |

Requires Bash 4.0+ (regex match with `BASH_REMATCH`).

---

## License

[MIT](../LICENSE)
