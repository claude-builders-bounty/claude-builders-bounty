# claude-review — PR Review Agent

A Claude-powered CLI tool that reviews GitHub pull requests and returns structured Markdown analysis. Runs as a standalone CLI or as a GitHub Action that auto-posts reviews as PR comments.

## Setup

**Prerequisites:** Python 3.8+, `gh` CLI authenticated (`gh auth login`), Anthropic API key

**Install:**
```bash
# Clone or copy claude-review to a directory on your PATH
cp agents/pr-review/claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
# Review a PR by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Review using shorthand
claude-review --pr owner/repo#123

# Save review to file
claude-review --pr owner/repo#123 --output review.md

# Review and post as GitHub PR comment
claude-review --pr owner/repo#123 --post
```

## Output format

```
## Summary
What the PR does in 2-3 sentences.

## Risks
- Specific risks, bugs, or concerns

## Suggestions
- Actionable improvement recommendations

## Confidence
High — clear diff with well-defined scope.
```

## GitHub Action

Add to your repo at `.github/workflows/pr-review.yml` to auto-review every PR:

1. Copy the workflow file from `agents/pr-review/.github/workflows/pr-review.yml`
2. Add `ANTHROPIC_API_KEY` to your repo's Settings → Secrets and Variables → Actions

The action posts the review as a PR comment automatically on every PR open or push.

## Claude Code Skill

To use within Claude Code sessions, copy `pr-review-agent.md` to your `~/.claude/skills/` directory. Then trigger it with: "Review this PR: https://github.com/owner/repo/pull/123"
