# `claude-review` — Claude Code PR Review Sub-Agent & GitHub Action

An autonomous Claude Code sub-agent (`.claude/agents/pr-reviewer.md`), CLI (`bin/claude-review`), and GitHub Action (`.github/workflows/claude-review.yml`) that fetches any GitHub Pull Request diff, analyzes its architectural and security implications, and produces a structured Markdown review comment.

## Features

- **CLI & GitHub Action Support**:
  - Run directly from the terminal: `claude-review --pr https://github.com/owner/repo/pull/123`
  - Post review directly as a PR comment with `--post`
  - Automate on every PR via `.github/workflows/claude-review.yml`
- **Structured Markdown Output**:
  - **Summary of Changes** (2–3 sentences)
  - **Identified Risks** (bulleted list)
  - **Improvement Suggestions** (bulleted list)
  - **Confidence Score**: `Low` / `Medium` / `High`

## Setup & Usage

### 1. CLI Usage

```bash
# Make the CLI executable (or add ./bin to your PATH)
chmod +x ./bin/claude-review
export PATH="$PWD/bin:$PATH"

# Optional: Set ANTHROPIC_API_KEY and GITHUB_TOKEN for live Claude Sonnet 4 synthesis
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

# Review any public or private GitHub PR
claude-review --pr https://github.com/Parabola-org/parabola/pull/103

# Save output to a file and post as a PR comment
claude-review --pr https://github.com/Parabola-org/parabola/pull/103 --output review.md --post
```

### 2. Claude Code Sub-Agent Usage

Because `.claude/agents/pr-reviewer.md` is registered in `.claude/agents/`, you can invoke it directly inside Claude Code:

```text
> Use the pr-reviewer subagent to review https://github.com/Parabola-org/parabola/pull/103
```

### 3. GitHub Action Usage

Add `ANTHROPIC_API_KEY` to your repository secrets (`Settings -> Secrets and variables -> Actions`). The included workflow at [`.github/workflows/claude-review.yml`](../../.github/workflows/claude-review.yml) automatically triggers on `pull_request` (`opened`, `synchronize`, `reopened`) or manual `workflow_dispatch` and posts the structured review comment to the PR.

## Real PR Review Outputs

Tested against 2 real GitHub PRs:
1. [`examples/review-parabola-pr-103.md`](../../examples/review-parabola-pr-103.md) — Review of [`Parabola-org/parabola#103`](https://github.com/Parabola-org/parabola/pull/103)
2. [`examples/review-gyroflow-pr-1250.md`](../../examples/review-gyroflow-pr-1250.md) — Review of [`gyroflow/gyroflow#1250`](https://github.com/gyroflow/gyroflow/pull/1250)
