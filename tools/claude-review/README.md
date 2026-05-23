# claude-review

> **AI-powered PR reviewer** — Claude Code sub-agent that analyzes a GitHub Pull Request diff and returns a structured Markdown review comment.

## ⚡ Quick Start

```bash
# Install
pip install ./tools/claude-review

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."   # Optional — required for private repos or --post-comment

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123
```

## 📋 Output Format

Every review follows this exact structure:

```markdown
## 📋 Summary of Changes
<2–3 sentence overview>

## ⚠️ Identified Risks
- Risk 1
- Risk 2

## 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

## 🎯 Confidence Score
**High / Medium / Low** — explanation
```

## 🔧 CLI Options

```
usage: claude-review [-h] --pr URL [--post-comment] [--output FILE]

options:
  --pr URL          GitHub PR URL (required)
  --post-comment    Post the review as a GitHub comment
  --output FILE     Save review to a Markdown file
```

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Always | Your Anthropic API key |
| `GITHUB_TOKEN` | For `--post-comment` or private repos | GitHub Personal Access Token |

## 🤖 GitHub Actions Integration

Add this to your repository to get automatic PR reviews:

```yaml
# .github/workflows/claude-pr-review.yml
name: PR Review (Claude)
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
          python-version: "3.12"
      - run: pip install ./tools/claude-review
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_URL="https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}"
          claude-review --pr "$PR_URL" --post-comment
```

## 📁 Sample Outputs

See [`sample-outputs/README.md`](sample-outputs/README.md) for example reviews on real PRs.
