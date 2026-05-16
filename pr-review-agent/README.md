# 🤖 Claude PR Review Agent

Claude Code sub-agent that reviews GitHub pull requests and posts structured Markdown comments.

**Bounty $150** • [View bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Features

- 📥 Fetches PR diff + metadata via GitHub API
- 🤖 Analyzes with Claude, GPT-4o, or DeepSeek
- 📊 Structured output: Summary, Risks, Suggestions, Confidence score
- 💬 Posts review as a PR comment
- 🔧 CLI + GitHub Action

## Quick Start

### Prerequisites

```bash
pip install requests  # only stdlib used, but ensure Python 3.10+
```

Set environment variables:
```bash
export GITHUB_TOKEN=ghp_your_token       # Classic PAT, repo scope
export ANTHROPIC_API_KEY=sk-ant-...       # Claude (recommended)
# OR
export DEEPSEEK_API_KEY=sk-...            # DeepSeek (cheaper)
# OR
export OPENAI_API_KEY=sk-...              # GPT-4o
```

### CLI Usage

```bash
# Review a PR
python3 pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123

# Dry run (print, don't post)
python3 pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123 --dry-run

# Specify model
python3 pr-review-agent/claude-review --pr URL --model claude-opus-4-5
```

### GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo. Set these secrets:
- `GITHUB_TOKEN` (auto-provided in Actions)
- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` / `DEEPSEEK_API_KEY`)

The action runs automatically on PR open, sync, and reopen events.

## Output Format

```markdown
## 🤖 AI PR Review

**Confidence:** 🟢 High | **Model:** claude-sonnet-4

---

### 📝 Summary
This PR adds a caching layer to the XYZ service, reducing database load by ~40%.
Changes are focused and well-structured.

### ⚠️ Risks
1. **Missing cache invalidation** in `src/cache.py:45` — stale data if updates occur between TTL windows
2. **Memory leak potential** in `src/worker.py:128` — cache entries never evicted under high load

### 💡 Suggestions
1. Add `@cache.invalidate_on_update` decorator pattern in `src/cache.py`
2. Consider adding cache hit/miss metrics in `src/metrics.py`

---
*Automated review by Claude PR Review Agent*
```

## Tested PRs

### 1. open-review #1 — Initial commit
- **PR:** https://github.com/kunci115/open-review/pull/1
- **Model:** DeepSeek Chat
- **Confidence:** High
- **Result:** Posted structured review ✅

### 2. thesis-assist snippet
- **PR:** (internal test)
- **Model:** Claude Sonnet 4
- **Confidence:** Medium
- **Result:** Identified 2 real issues ✅

## Requirements

- Python 3.10+
- GitHub Classic PAT (repo scope)
- Any LLM API key (Claude recommended per bounty spec)

## License

MIT — see [LICENSE](../LICENSE)
