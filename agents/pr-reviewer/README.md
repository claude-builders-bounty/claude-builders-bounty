# 🤖 Claude PR Reviewer — Claude Code Sub-Agent

A Claude Code sub-agent that fetches a GitHub pull request, reviews it using the Claude API, and posts a structured comment directly to the PR.

## Usage in Claude Code

```
/review-pr <owner> <repo> <pr_number>
```

Example:
```
/review-pr vercel next.js 71234
```

Claude will run the sub-agent, which:
1. Fetches the PR metadata, file list, and unified diff from GitHub
2. Sends the full context to `claude-sonnet-4-20250514` for review
3. Posts a structured comment on the GitHub PR (visible to all contributors)

## Direct CLI Usage

```bash
ANTHROPIC_API_KEY=sk-ant-... \
GITHUB_TOKEN=ghp_... \
python review-pr.py <owner> <repo> <pr_number>
```

## Review Output Format

Each review contains:

| Section | Content |
|---|---|
| 📋 Summary | One-paragraph overview and overall impression |
| ✅ Strengths | What's done well, with specifics |
| 🔍 Issues & Suggestions | Each issue with severity 🔴/🟡/🔵, file/line, and fix suggestion |
| 🧪 Testing | Assessment of test coverage |
| 🚦 Verdict | Approve / Request Changes / Comment only + justification |

## Setup

**Step 1** — Set environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # get from console.anthropic.com
export GITHUB_TOKEN="ghp_..."           # needs: repo, pull_requests:write
```

**Step 2** — Run:
```bash
python review-pr.py owner repo 42
```

## Requirements

- Python 3.8+ (stdlib only — no `pip install` needed)
- `ANTHROPIC_API_KEY` with access to `claude-sonnet-4-20250514`
- `GITHUB_TOKEN` with `repo` scope and write access to the target repo
