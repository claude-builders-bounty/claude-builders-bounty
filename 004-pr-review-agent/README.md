# Claude PR Review Agent ($150 Bounty)

A Claude Code-powered sub-agent that automatically reviews GitHub pull requests and posts structured markdown comments.

## Features

- **CLI mode**: `claude-review --pr <PR_URL>` — standalone review from terminal
- **GitHub Action**: Auto-reviews every PR when triggered
- **Structured output**: Summary, positives, risks, suggestions, confidence score
- **Direct Claude API** or **Claude Code CLI** fallback

## Quick Start

### CLI Usage

```bash
# Set credentials
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

1. Copy `.github/workflows/pr-review.yml` to your repo
2. Add `ANTHROPIC_API_KEY` to your repo's **Actions secrets**
3. Every new/updated PR gets auto-reviewed!

Triggers:
- Automatically on `opened` and `synchronize` pull request events
- On-demand via `/claude-review` comment on any PR

## Output Format

Each review contains:

```
## PR Review: owner/repo #123
**Title** by @author
main ← feature-branch | +150/-42 | 8 files

---
## Summary
2-3 sentence overview.

## What's Good
- Well-structured error handling...
- Good test coverage...

## Risks & Concerns
- `src/api/handler.go:45` — Potential nil pointer dereference...
- `db/migrations/004.sql` — Missing rollback...

## Improvement Suggestions
- Consider using `context.WithTimeout` instead of raw context...

## Confidence Score
**High** — Diff is small, well-scoped, and patterns are clear.
```

## Test Results

✅ **Test PR #1** — `claude-builders-bounty/claude-builders-bounty` PR #3306 (n8n workflow)
   [View sample output →](samples/pr-3306-review.md)

✅ **Test PR #2** — `MervinPraison/PraisonAIDocs` PR #1734 (docs compliance)
   [View sample output →](samples/pr-1734-review.md)

## Requirements

- **GitHub Token** — `GITHUB_TOKEN` environment variable (or `gh` CLI authenticated)
- **Claude API Key** — `ANTHROPIC_API_KEY` environment variable (or `claude` CLI installed)

## Architecture

```
User runs:  claude-review --pr <URL>
               │
               ▼
     ┌─────────────────┐
     │  Parse PR URL   │  owner/repo/PR#
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  GitHub API     │  PR metadata, diff, file list
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  Build Prompt   │  Structured review prompt
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  Claude API     │  claude-sonnet-4-20250514
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  Format Output  │  Structured markdown
     └─────────────────┘
```

## Verification

✅ CLI works: `claude-review --pr <URL>`  
✅ GitHub Action: auto-review on PR open/update  
✅ Structured markdown: Summary / Risks / Suggestions / Confidence  
✅ Tested on 2 real PRs (sample outputs included)  
✅ README with setup and usage
