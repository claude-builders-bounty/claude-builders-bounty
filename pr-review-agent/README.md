# PR Review Agent — Claude Code Sub-Agent

A Claude Code sub-agent that analyzes PR diffs and posts structured Markdown review comments.

Works in **two modes**:
- **CLI** — Run locally or in CI
- **GitHub Action** — Auto-review PRs via workflow trigger

---

## Quick Start

### Prerequisites

- Python 3.10+
- An API key (OpenAI, Anthropic, or compatible OpenAI-format provider)

### Install

```bash
pip install -r requirements.txt
```

### Set API Key

```bash
# OpenAI-compatible (default: Bailian/qwen3.6-plus)
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_MODEL="qwen3.6-plus"

# Or Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-xxx"
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"
```

### CLI Usage

```bash
# Review a PR by URL
python pr_reviewer.py --pr https://github.com/owner/repo/pull/123

# Review a raw diff file
python pr_reviewer.py --diff diff.patch

# Specify model
python pr_reviewer.py --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-20250514

# Output to file
python pr_reviewer.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action Usage

Add `.github/workflows/pr-review.yml` to your repository:

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Review PR
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}
          OPENAI_MODEL: ${{ vars.OPENAI_MODEL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          pip install -r pr-review-agent/requirements.txt
          python pr-review-agent/pr_reviewer.py --pr-url "${{ github.event.pull_request.html_url }}" --post-comment
```

---

## Output Format

Every review follows this structured Markdown template:

```markdown
## 📋 PR Review

### Summary
A concise 2-3 sentence overview of what this PR changes and why.

### ⚠️ Identified Risks
- [Risk category] — description of the potential issue
- ...

### 💡 Improvement Suggestions
- [Suggestion] — actionable recommendation
- ...

### 🎯 Confidence Score
**Medium** — explanation of confidence level
```

---

## Architecture

```
┌─────────────────┐
│  GitHub API     │  ← Fetch PR diff via gh CLI or REST API
└────────┬────────┘
         │ diff
         ▼
┌─────────────────┐
│  Prompt Builder │  ← Construct analysis prompt
└────────┬────────┘
         │ prompt
         ▼
┌─────────────────┐
│  LLM API        │  ← OpenAI / Anthropic / compatible
└────────┬────────┘
         │ analysis
         ▼
┌─────────────────┐
│  Output Formatter│  → Structured Markdown
└─────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
  stdout   GitHub
  (CLI)   Comment
```

---

## Tested On

| PR | Repository | Result |
|----|-----------|--------|
| [#158](https://github.com/aryandas2911/DailyForge/pull/158) | DailyForge | ✅ Risk detection accurate |
| [#221](https://github.com/hypernetwork-research-group/hyperbench/pull/221) | hyperbench | ✅ Suggestion quality good |

See `samples/` for full review outputs.
