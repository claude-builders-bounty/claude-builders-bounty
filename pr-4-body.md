## 💰 Bounty: $150 — powered by [Opire](https://opire.dev)

## What

Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Deliverables

- `agents/claude-review/claude-review.py` — CLI tool + agent
- `agents/claude-review/github-action.yml` — GitHub Action workflow
- `agents/claude-review/README.md` — Setup and usage instructions
- `agents/claude-review/sample-output-1.md` — Review of real PR (footprinter pdip)
- `agents/claude-review/sample-output-2.md` — Review of real PR (dsn-converter fix)

## Acceptance Criteria Met

- ✅ Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- ✅ GitHub Action workflow included (`github-action.yml`)
- ✅ Structured Markdown output with:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High
- ✅ Tested on 2 real GitHub PRs (sample outputs included)
- ✅ README with setup and usage instructions

## Usage

```bash
# Review a PR (outputs to stdout)
claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Review a local diff
claude-review --diff-file changes.diff

# JSON output
claude-review --pr URL --output json
```

## How It Works

1. Fetches PR metadata + diff via GitHub API
2. Sends diff to Claude for analysis (tries CLI → API → static fallback)
3. Outputs structured Markdown review
4. Optionally posts as a comment on the PR

/opire try

Closes #4
