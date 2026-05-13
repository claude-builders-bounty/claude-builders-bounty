# claude-review — AI-Powered PR Review Agent

A Claude Code sub-agent that takes a GitHub PR URL, fetches the diff, and generates a structured Markdown code review.

## Features

- 🔍 **Automated PR analysis**: Fetches PR diff + metadata via `gh` CLI
- 🤖 **AI-powered review**: Uses Claude to generate insightful, structured reviews
- 📋 **Structured output**: Summary, Risks, Suggestions, Confidence Score
- 🔄 **GitHub Action**: Can run automatically on PR open/sync or via `/review` comment
- 💻 **CLI mode**: Run locally with a single command
- 📊 **JSON output**: Machine-readable format for integration

## Quick Start

### CLI Usage

```bash
# Prerequisites: gh CLI authenticated + Claude Code CLI in PATH
chmod +x claude-review

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123

# JSON output
./claude-review --pr https://github.com/owner/repo/pull/42 --format json
```

### GitHub Action

1. Copy `.github/workflows/pr-review.yml` to your repo
2. Add `ANTHROPIC_API_KEY` to your repository secrets
3. Reviews will auto-post on PR open/sync, or trigger manually with `/review` comment

## Output Format

Every review follows this structure:

```markdown
# PR Review: <title>

## Summary
2-3 sentence overview of changes and quality assessment.

## Identified Risks
- 🔴 Critical: <critical issues>
- 🟡 Warning: <potential problems>
- 🔵 Info: <minor observations>

## Improvement Suggestions
1. Concrete, actionable suggestions with code references.

## Confidence Score
Low / Medium / High — justification.
```

## Requirements

- **gh CLI** — authenticated with `gh auth login`
- **Claude Code CLI** — `claude` in PATH (for AI-powered reviews)
- **bash** — standard Unix shell

## How It Works

1. Parses the PR URL to extract owner/repo/number
2. Fetches PR metadata (title, author, stats) and full diff via `gh`
3. Constructs a structured review prompt
4. Sends to Claude via `claude --print` for analysis
5. Outputs formatted Markdown or JSON

## Example Output

See [sample-reviews/](sample-reviews/) for real review outputs on actual PRs.

## License

MIT
