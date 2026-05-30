# PR Review Agent

A Claude Code sub-agent that reviews pull requests and posts structured Markdown comments.

## Usage

```bash
# Via CLI (standalone)
python3 agents/pr-review/claude-review.py --pr https://github.com/owner/repo/pull/123

# Via CLI with local diff
python3 agents/pr-review/claude-review.py --diff /path/to/pr.diff

# In Claude Code, load this agent
claude --agent agents/pr-review/AGENTS.md
```

## GitHub Action

Add `.github/workflows/pr-review.yml` to any repo to auto-review PRs:

```yaml
name: PR Review Agent
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/pr-review/claude-review.py \
            --pr "${{ github.server_url }}/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --output review.md
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

## Output Structure

```markdown
## PR Review: Title
**Confidence Score:** High / Medium / Low

### Summary
2-3 sentences about the changes.

### Changes by File
Table with file paths, +/- counts, and change types.

### Identified Risks
List of potential issues found.

### Improvement Suggestions
List of actionable suggestions.

### Detailed File Analysis
Per-file breakdown of added/removed lines.
```

## Requirements

- Python 3.10+
- Internet access for GitHub API (when using `--pr`)
- `GITHUB_TOKEN` env var (optional, for private repos or higher rate limits)
