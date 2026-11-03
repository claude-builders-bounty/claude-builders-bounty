# `claude-review` — Claude Code Sub-Agent for Structured GitHub PR Reviews

> **Submission for `claude-builders-bounty/claude-builders-bounty#4` (`$150` Bounty)**

A zero-dependency CLI tool and GitHub Action sub-agent that fetches any GitHub Pull Request (`--pr https://github.com/owner/repo/pull/123`), analyzes the full file-by-file unified diff with **Claude (`claude-sonnet-4-20250514`)** + static AST/diff heuristics, and outputs (or posts) a structured Markdown review comment.

---

## Features & Acceptance Criteria Checklist

- [x] **CLI Interface**: `./claude-review --pr https://github.com/owner/repo/pull/123`
- [x] **GitHub Action**: `.github/workflows/claude-pr-review.yml` triggers automatically on `pull_request` (`opened`, `synchronize`, `reopened`) and posts the review directly to the PR.
- [x] **Structured 4-Section Output**:
  1. `### Summary of changes` (2–3 sentences)
  2. `### Identified risks` (bulleted list with file references)
  3. `### Improvement suggestions` (bulleted list)
  4. `### Confidence score` (`Low` / `Medium` / `High` with justification)
- [x] **Tested on 2 Real GitHub PRs**: See [`sample-reviews/pr-test-1.md`](./sample-reviews/pr-test-1.md) and [`sample-reviews/pr-test-2.md`](./sample-reviews/pr-test-2.md).

---

## Quick Start

### 1. CLI Usage (Local or CI)

```bash
chmod +x ./claude-review

# Print structured Markdown review to stdout and save to file
export ANTHROPIC_API_KEY="sk-ant-..."   # Optional: falls back to static diff analyzer if unset
./claude-review --pr https://github.com/octocat/Hello-World/pull/1 --output review.md

# Post directly as a comment on the GitHub Pull Request
export GITHUB_TOKEN="ghp_..."
./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

### 2. GitHub Action Setup

1. Copy `claude-review` to the root of your repository and `.github/workflows/claude-pr-review.yml` into `.github/workflows/`.
2. Add `ANTHROPIC_API_KEY` to your repository's **Settings → Secrets and variables → Actions**.
3. Open any Pull Request — the workflow will automatically analyze the diff and post the structured comment.

