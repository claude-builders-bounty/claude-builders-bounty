# Claude Code PR Review Agent

A **Claude Code sub-agent** that reviews a GitHub PR and posts a structured Markdown comment.

## What is this?

This is a [Claude Code agent](https://docs.anthropic.com/en/docs/claude-code) — a `.md` file that teaches Claude how to perform PR code reviews. Drop it into any project's `.claude/agents/` directory and Claude Code can review PRs on demand.

## Quick Start

### Option 1: Use as Claude Code Agent (recommended)

```bash
# Copy the agent into your project
cp .claude/agents/pr-reviewer.md YOUR_PROJECT/.claude/agents/

# In Claude Code, get a PR diff and ask the agent:
gh pr diff 123 | claude --agent pr-reviewer

# Or directly with a PR URL:
claude "Review this PR: https://github.com/owner/repo/pull/123 using the pr-reviewer agent"
```

### Option 2: Use standalone CLI (fallback without Claude)

```bash
npm install

# Review a local diff
node cli.mjs --diff samples/test-pr.diff

# Review a GitHub PR (fetches diff automatically)
export GITHUB_TOKEN=ghp_xxx
node cli.mjs --pr https://github.com/owner/repo/pull/123

# Pipe from stdin
git diff main | node cli.mjs --stdin
```

## Agent Definition

The core of this project is `.claude/agents/pr-reviewer.md` — it defines:
- **Role**: Senior software engineer conducting code review
- **Process**: Analyze diff → identify risks → suggest improvements
- **Output**: Structured Markdown with Summary, Risks, Suggestions, Confidence

## Sample Output

Tested on `samples/test-pr.diff`:

```
## 📋 Summary
This change modifies 3 files with 6 additions and 2 deletions. 
Changes span src/auth.ts, src/utils.ts, tests/auth.test.ts.

## ⚠️ Identified Risks
- Found TODO/FIXME/HACK in src/auth.ts — ensure these are tracked
- Found TODO/FIXME/HACK in src/utils.ts — ensure these are tracked
- Test file modified: tests/auth.test.ts — ensure test coverage maintained
- ⚠️ Potential hardcoded credential in src/utils.ts — use env variables

## 💡 Improvement Suggestions
- Found debug logging (console.log) — consider removing before merge
- Deleted assertion in auth.test.ts — verify test intent is preserved

## 🎯 Confidence: Medium
```

## GitHub Action (Automated PR Review)

Copy `.github/workflows/pr-review.yml` to your repo to auto-review every PR:

```yaml
name: AI PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run PR Review Agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > /tmp/pr.diff
          cat /tmp/pr.diff | claude --agent pr-reviewer > /tmp/review.md

      - name: Post Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('/tmp/review.md', 'utf-8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
```

## Project Structure

```
.
├── .claude/agents/
│   └── pr-reviewer.md     # The actual Claude Code agent definition
├── cli.mjs                # Standalone CLI (fallback mode)
├── review.mjs             # Review engine (static analysis)
├── samples/
│   └── test-pr.diff       # Sample diff for testing
├── package.json
└── README.md
```

## Requirements

- **Claude Code** (for AI-powered review via agent)
- Node.js 22+ (for standalone CLI fallback)
- `gh` CLI and `GITHUB_TOKEN` (for fetching PR diffs)

## License

MIT
