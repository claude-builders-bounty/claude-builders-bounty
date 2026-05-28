# claude-review 🤖

A **Claude Code sub-agent** that reviews pull request diffs and returns structured Markdown.

Designed for Claude Code workflows — pipe it in as a tool or run it standalone for quick reviews.

## Quick Install

```bash
npm install -g claude-review
# or just clone + run:
# node bin/claude-review.js --pr <url>
```

Requires: **Node.js v18+** and `gh` CLI (authenticated, for fetching PR data).

## Usage

```bash
# Review a PR (Markdown output)
claude-review --pr https://github.com/owner/repo/pull/123

# JSON output (for agent pipelines)
claude-review --pr https://github.com/owner/repo/pull/123 --json

# Help
claude-review --help
```

## Output

### Markdown mode (default)

| Section | Description |
|---------|-------------|
| 📋 Summary | 2-3 sentence description of the PR |
| ⚠️ Identified Risks | Security concerns, code smells, TODOs |
| 💡 Improvement Suggestions | Test gaps, branch conventions, debug logging |
| ✅ What Looks Good | Positive findings |
| 📊 Confidence Score | Low / Medium / High based on risk analysis |

### JSON mode (`--json`)

Returns a structured JSON object with `summary`, `risks[]`, `suggestions[]`, `positives[]`, and `confidence` — ready for Claude Code tool ingestion.

## GitHub Action

Include this workflow in your repo (`.github/workflows/claude-review.yml`):

```yaml
name: claude-review
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Post claude-review
        uses: actions/github-script@v7
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          script: |
            const { data: pr } = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });
            const { data: files } = await github.rest.pulls.listFiles({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });

            const risk = files.filter(f => (f.patch || '').includes('console.log')).length > 2
              ? '- Debug logging should be removed' : '';
            const body = [
              '## 🔍 PR Review',
              '',
              '**PR**: [' + pr.title + '](' + pr.html_url + ')',
              '**Author**: ' + pr.user.login,
              '**Branch**: ' + pr.base.ref + ' ← ' + pr.head.ref,
              '**Files**: ' + files.length,
              '',
              '### Summary',
              '',
              pr.body || 'No description provided.',
              '',
              '### Risks',
              '',
              risk || '- None identified',
              '',
              '🤖 Review by claude-review'
            ].join('\n');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## Sample Output

### Tested on real PRs

**PR #1**: [Add structured Claude PR review agent](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2234) by sjkim1127
- 9 files changed, 582 additions
- Identified: large file that could be split
- Branch name convention suggestion

**PR #2**: [Add destructive Bash command PreToolUse hook](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2233) by sjkim1127
- 4 files changed, 591 additions
- Identified: large file that could be split
- Branch name convention suggestion

## Architecture

```
bin/claude-review.js   → CLI entry point
  parsePrUrl()         → extract owner/repo/PR from URL
  fetchPrDiff()        → gh CLI (primary) or GitHub API (fallback)
  analyzeDiff()        → heuristic analysis engine
  renderMarkdown()     → human-readable output
  renderAgentOutput()  → machine-readable JSON (agent pipeline)
```

The tool uses:
- **gh CLI** — primary data source (supports GH_TOKEN auth natively)
- **GitHub REST API** — fallback when gh isn't available
- **Static analysis rules** — pattern matching on diff patches (no AI API key required)

## Development

```bash
# Install deps
npm install

# Run tests
npm test

# Manual test
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

## License

MIT