# Claude Review

A Claude Code agent that reviews GitHub PRs and posts structured review comments.

## Features

- **Structured Markdown Output**: Provides reviews with summary, risks, suggestions, and confidence score
- **CLI Tool**: Review any PR with a single command
- **GitHub Action**: Integrate into your CI/CD workflow
- **Template-Based Fallback**: Works without API keys using pattern analysis

## Installation

### CLI Tool

```bash
npm install -g claude-review
```

Or use directly with npx:

```bash
npx claude-review --pr https://github.com/owner/repo/pull/123
```

### From Source

```bash
git clone https://github.com/sungdark/claude-builders-bounty.git
cd claude-builders-bounty
npm install
npm link  # Optional: link globally
```

## Usage

### CLI

```bash
# Basic review
claude-review --pr https://github.com/owner/repo/pull/123

# Post review as GitHub comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Use specific Claude model
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-3-5-sonnet

# With custom GitHub token
GITHUB_TOKEN=xxx claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action

```yaml
name: PR Review
on:
  workflow_dispatch:
    inputs:
      pr_url:
        description: 'PR URL to review'
        required: true

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install
      - run: npx claude-review --pr "${{ inputs.pr_url }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token (defaults to `gh auth` credentials) |
| `ANTHROPIC_KEY` | Anthropic API key for enhanced AI-powered reviews |

## Output Format

The review provides structured Markdown with:

### Summary
2-3 sentences describing what the PR does

### Identified Risks
- Security concerns
- Potential bugs
- Breaking changes

### Improvement Suggestions
- Code quality improvements
- Testing recommendations
- Best practices

### Confidence Score
- **High**: Clean PR, well-tested, minimal risks
- **Medium**: Minor concerns, typical PR
- **Low**: Significant risks or issues detected

## Demo: Tested on Real PRs

### Test 1: Block Destructive Commands Hook (PR #6)

```bash
$ claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/6
```

**Output:**

## PR Review: feat(hook): PreToolUse hook to block destructive bash commands (#3)

### Summary
## Fixes #3

This PR implements a Claude Code `PreToolUse` hook that intercepts dangerous bash commands before they execute.

### What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm --recursive --force` | Recursive force delete |
| `DROP TABLE` | SQL table destruction |
| `git push --force` / `git push -f` | Rewrites remote history |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |

### How it works

1. Intercepts every `Bash` tool call via Claude Code's `PreToolUse` hook
2. Checks the command against destructive patterns
3. **Blocks** the command and shows Claude why it was denied
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with UTC timestamp, reason, command, and working directory
5. **Allows** safe commands to pass through unchanged

This PR modifies 1 file(s), adding 184 lines and removing 0 lines. The changes are authored by DrGalio.

### Identified Risks
✅ No obvious risks detected

### Improvement Suggestions
✅ Code looks good overall

### Confidence Score: Medium
```

---

### Test 2: n8n Weekly Dev Summary Workflow (PR #7)

```bash
$ claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/7
```

**Output:**

## PR Review: Fix #5: [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary

### Summary
## Summary

Fixes #5

## Changes

# PR Description

This PR introduces a complete n8n workflow that automates weekly GitHub repository summaries using Claude AI. The workflow fetches commits, closed issues, and merged PRs from a GitHub repo on a weekly schedule (Friday at 5pm), then uses Claude Sonnet 4 to generate a narrative summary of development activity. Two new files have been added: the exportable workflow JSON file and comprehensive documentation in the workflows README explaining setup, configuration, and usage.

## Testing

- Ran existing test suite
- Added tests where applicable

---

**Disclosure:** This contribution was created by an autonomous AI agent.

This PR modifies 1 file(s), adding 527 lines and removing 0 lines. The changes are authored by sixty-dollar-agent.

### Identified Risks
✅ No obvious risks detected

### Improvement Suggestions
✅ Code looks good overall

### Confidence Score: High

---

## License

MIT
