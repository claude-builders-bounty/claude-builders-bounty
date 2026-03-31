# 🤖 Claude PR Review Agent

A CLI tool that uses Claude to review GitHub Pull Requests and output structured Markdown analysis.

## Features

- **CLI + GitHub Action** — use standalone or as automated CI
- **Structured output** — Summary, Risks, Suggestions, Confidence Score
- **Smart diff handling** — truncates large diffs to fit context window
- **Post-to-PR** — optionally posts the review as a GitHub comment
- **JSON output** — machine-readable format for pipelines
- **Any public/private repo** — works with GitHub tokens

## Quick Start

### 1. Set environment variables

```bash
export CLAUDE_API_KEY="sk-ant-..."      # Required
export GITHUB_TOKEN="ghp_..."           # Required for private repos + --post
```

### 2. Run a review

```bash
# Full URL
./claude-review --pr https://github.com/facebook/react/pull/28000

# Shorthand
./claude-review --pr facebook/react/28000

# Post as PR comment
./claude-review --pr owner/repo/123 --post

# JSON output
./claude-review --pr owner/repo/123 --json
```

### 3. GitHub Action (automated)

Copy `.github/workflows/claude-review.yml` to your repo. Add `CLAUDE_API_KEY` as a repository secret.

Every new PR (and push to existing PRs) will receive an automated review comment.

## Output Format

```markdown
# 🤖 Claude Code Review — owner/repo#123

## 📋 Summary
Brief overview of the PR changes.

## ⚠️ Identified Risks
- Risk 1
- Risk 2

## 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

## 🎯 Confidence Score
**High** — Clear, well-scoped changes with straightforward logic.
```

## Options

| Flag | Description |
|------|-------------|
| `--pr <ref>` | PR URL or `owner/repo/number` (required) |
| `--post` | Post review as PR comment |
| `--model <m>` | Claude model (default: `claude-sonnet-4-20250514`) |
| `--json` | JSON output instead of Markdown |
| `--help` | Show help |

## Sample Reviews

See the `examples/` directory for real review outputs.

## Requirements

- `bash`, `curl`, `python3` (standard on macOS/Linux/CI)
- Anthropic API key with Messages API access
- GitHub token (optional, for private repos and `--post`)
