# Claude Code Sub-Agent: PR Reviewer (`claude-review`)

A Claude Code sub-agent and CLI tool that takes a GitHub Pull Request URL (or local diff) as input, analyzes the changeset, and generates a structured Markdown review comment.

## Features
- **CLI Execution:** `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action Integration:** Automatically triggers on PR events and posts the structured review comment (`.github/workflows/claude-pr-review.yml`).
- **Claude Code Sub-Agent Definition:** Drop-in `.claude/agents/pr-reviewer.md` prompt definition.
- **Structured Output:**
  - Summary of changes (2–3 sentences)
  - Identified risks (bulleted list)
  - Improvement suggestions (bulleted list)
  - Confidence score (`Low` / `Medium` / `High`)

## Quickstart & CLI Usage

```bash
# Run directly on any public or private GitHub PR:
export GITHUB_TOKEN="ghp_your_token"
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/overturn-ai/overturn/pull/54

# Or install as a CLI script:
ln -s $(pwd)/agents/pr-reviewer/claude_review.py /usr/local/bin/claude-review
chmod +x agents/pr-reviewer/claude_review.py
claude-review --pr https://github.com/Spectral-Finance/lux/pull/1167
```

## Running Tests

```bash
python3 -m unittest discover -s agents/pr-reviewer -p "test_*.py" -v
```

## Real PR Review Outputs

### Sample 1: `overturn-ai/overturn#54` (Gorgias Capture Adapter Package)
```markdown
## 🤖 Claude Code Sub-Agent PR Review for [https://github.com/overturn-ai/overturn/pull/54](https://github.com/overturn-ai/overturn/pull/54)

### 📋 Summary of Changes
This pull request (feat(gorgias-app): add Gorgias ticket sidebar capture adapter (#22)) modifies 14 file(s) with 863 addition(s) and 1 deletion(s). Key areas touched include packages/gorgias-app/src/capture.ts, packages/gorgias-app/src/capture.test.ts, packages/gorgias-app/src/main.ts, packages/shared/src/schemas.ts. Unit test coverage is included alongside the implementation.

### ⚠️ Identified Risks
- Large diff footprint (+863 lines) increases review complexity and merge conflict surface area.

### 💡 Improvement Suggestions
- Ensure public functions and CLI entrypoints include explicit type annotations and docstrings.

### 🎯 Confidence Score
**Medium**
```

### Sample 2: `Spectral-Finance/lux#1168` (Twitter API v2 Core Integration)
```markdown
## 🤖 Claude Code Sub-Agent PR Review for [https://github.com/Spectral-Finance/lux/pull/1168](https://github.com/Spectral-Finance/lux/pull/1168)

### 📋 Summary of Changes
This pull request (feat(twitter): implement Twitter API v2 core integration and lens suite (#58)) modifies 8 file(s) with 861 addition(s) and 0 deletion(s). Key areas touched include lux/lib/lux/integrations/twitter.ex, lux/lib/lux/integrations/twitter/client.ex, lux/lib/lux/lenses/twitter/tweets/create_tweet.ex, lux/test/unit/lux/lenses/twitter/twitter_lenses_test.exs. Unit test coverage is included alongside the implementation.

### ⚠️ Identified Risks
- Low operational risk: changes are well-scoped and include accompanying verification tests.

### 💡 Improvement Suggestions
- Ensure public functions and CLI entrypoints include explicit type annotations and docstrings.

### 🎯 Confidence Score
**High**
```
