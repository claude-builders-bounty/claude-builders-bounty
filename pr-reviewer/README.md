# claude-review — PR Reviewer CLI + GitHub Action

A Claude Code sub-agent that reviews GitHub PRs and outputs structured Markdown review comments.

## Features

- ✅ **CLI tool** — `python3 claude-review.py --pr OWNER/REPO/NUMBER`
- ✅ **GitHub Action** — `uses: ./pr-reviewer/action.yml`
- ✅ **Structured Markdown output** with all 5 sections:
  - Summary of Changes (2-3 sentences)
  - Identified Risks (list)
  - Improvement Suggestions (list)
  - Confidence Score (Low/Medium/High)
  - Overall Verdict (Approve/Changes requested/Comment)
- ✅ **Powered by Claude Code** — Uses `claude -p` for review
- ✅ **Fallback mode** — Basic review without LLM if Claude unavailable

## Quick Start

### CLI Usage

```bash
# Install
curl -sLO https://raw.githubusercontent.com/your-repo/main/claude-review.py
chmod +x claude-review.py

# Set GitHub token
export GITHUB_TOKEN="ghp_xxxxx"

# Review a PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
# or
python3 claude-review.py --pr owner/repo/123

# Save to file
python3 claude-review.py --pr owner/repo/123 --output review.md
```

### GitHub Action

```yaml
name: 'PR Review'
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./pr-reviewer
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          pr-number: ${{ github.event.pull_request.number }}
          owner: ${{ github.repository_owner }}
          repo: ${{ github.event.repository.name }}
          comment: 'true'
```

## Output Format

```markdown
# PR Review: owner/repo#123

**Title:** feat: new feature
**Author:** username
**URL:** https://github.com/owner/repo/pull/123

---

### Summary of Changes
[2-3 sentences describing what this PR does]

### Identified Risks
- [List potential issues]

### Improvement Suggestions
- [List concrete suggestions]

### Confidence Score
**Medium** — [brief justification]

### Overall Verdict
**Approve** — [brief justification]
```

## Requirements

- Python 3.8+
- `claude` CLI (optional, for LLM-powered reviews)
- `GITHUB_TOKEN` environment variable

## License

MIT
