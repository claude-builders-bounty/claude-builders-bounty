# Claude Code PR Review Agent

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Features

- **CLI**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **Python**: `python3 claude-review-agent.py --pr <url> [--post]`
- **GitHub Action**: `.github/workflows/pr-review.yml`
- **Structured output**: Summary, Risks, Improvements, Confidence Score

## Usage

### CLI

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Python Script

```bash
# Review and print to stdout
python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123

# Review and post as GitHub PR comment
python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123 --post
```

### GitHub Action

```yaml
name: PR Review Agent
on:
  pull_request:
  workflow_dispatch:
    inputs:
      pr_url:
        description: 'GitHub PR URL'
        required: true
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: python-version: '3.11'
      - run: pip install anthropic
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 claude-review-agent.py --pr "${{ inputs.pr_url || github.event.pull_request.html_url }}" --post
```

## Output Format

The agent produces structured Markdown with:

- **Summary**: 2-3 sentence overview of PR
- **Risks**: Identified security/functional risks
- **Improvements**: Actionable suggestions
- **Confidence**: Low / Medium / High with reasoning

## Sample Output

```
## 📋 Summary
This PR by @author modifies 30 file(s) (1355 lines added, 58 removed) for the project "Fix critical bugs...". The changes appear focused on Python implementation updates.

## ⚠️ Risks
✅ No obvious security issues detected in the changed code

## 💡 Improvements
📦 Large PR (>500 lines added) - consider breaking into smaller PRs
📁 Many files changed (>10) - ensure each commit is focused

## 🎯 Confidence
Confidence: Low
Reasoning: Static analysis only - manual review recommended for critical changes.

## 📁 Files Changed
30 files changed: py (19), tsx (5), md (4), ts (2)

## 📊 Diff Statistics
- Lines added: 1355
- Lines removed: 58
```

## Requirements

- `gh` CLI (authenticated)
- Python 3.8+
- `anthropic` package: `pip install anthropic` (optional, falls back to static analysis)

## Tested On

✅ PR #1 on ErnestHysa/agent-scout - 30 files, 1413 lines changed - [Comment](https://github.com/ErnestHysa/agent-scout/pull/1#issuecomment-4502767687)

✅ PR #2 on ErnestHysa/agent-scout - 37 files, 1878 lines changed - [Comment](https://github.com/ErnestHysa/agent-scout/pull/2#issuecomment-4502784148)