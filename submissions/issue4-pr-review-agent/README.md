# claude-review — Claude Code PR Review Sub-Agent

> Resolves [#4 [BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A CLI tool + GitHub Action that uses Claude Code to review GitHub PRs and produce structured Markdown comments.

## What it does

1. Fetches the PR diff and metadata via `gh` CLI
2. Sends the diff to Claude (`claude-sonnet-4-6`) for analysis
3. Returns a structured Markdown review with:
   - **Summary of Changes** (2–3 sentences)
   - **Identified Risks** (bulleted list)
   - **Improvement Suggestions** (bulleted list, specific and actionable)
   - **Confidence Score** (Low / Medium / High with reasoning)

## Requirements

- Python 3.9+
- [`gh` CLI](https://cli.github.com/) authenticated
- [Claude Code CLI](https://docs.anthropic.com/claude-code) installed (`npm install -g @anthropic-ai/claude-code`)

## Setup (5 steps)

```bash
# 1. Copy the CLI tool to your PATH
cp claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review

# 2. Ensure gh CLI is authenticated
gh auth login

# 3. Ensure Claude CLI is installed and authenticated
npm install -g @anthropic-ai/claude-code
claude --version

# 4. Run a review
claude-review --pr https://github.com/owner/repo/pull/123

# 5. (Optional) Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## CLI Usage

```
usage: claude-review [-h] --pr PR [--output OUTPUT]

options:
  --pr PR          GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)
  --output OUTPUT  Save output to file instead of stdout
```

## GitHub Action Setup

Copy `pr-review.yml` to `.github/workflows/` in your repository.

Required secret: `ANTHROPIC_API_KEY` (add in Settings → Secrets → Actions).

The action triggers on every PR open/update and posts the review as a comment.

## Sample Outputs

Real review outputs on actual PRs from this repository:

- [`sample_pr932.md`](sample-outputs/sample_pr932.md) — Review of PR #932 (pre-tool-use hook)
- [`sample_pr933.md`](sample-outputs/sample_pr933.md) — Review of PR #933 (CHANGELOG skill)

## Architecture

```
claude-review (CLI)
  ├── parse_pr_url()       — extract owner/repo/number from URL
  ├── get_pr_metadata()    — gh pr view --json
  ├── get_pr_diff()        — gh pr diff
  ├── build_review_prompt() — structure prompt with metadata + diff
  ├── call_claude()        — claude CLI subprocess (no direct API calls)
  └── format_output()      — wrap in Markdown header
```

All Claude calls go through `claude` CLI subprocess — no direct `anthropic` SDK imports.
