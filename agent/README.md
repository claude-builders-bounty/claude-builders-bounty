# 🤖 Claude Code PR Review Agent

A CLI tool that takes a GitHub PR URL as input, analyzes the diff via Claude API,
and returns a structured Markdown review.

## Quick Start

```bash
# 1. Install
sudo curl -sL https://raw.githubusercontent.com/haoyousun60-create/claude-builders-bounty/main/agent/claude-review -o /usr/local/bin/claude-review
sudo chmod +x /usr/local/bin/claude-review

# 2. Set API keys
export GITHUB_TOKEN=ghp_xxx
export CLAUDE_API_KEY=sk-ant-xxx

# 3. Review a PR
claude-review --pr https://github.com/owner/repo/pull/123
```

## CLI Options

| Flag | Description |
|------|-------------|
| `--pr <URL>` | GitHub PR URL (required) |
| `-o, --output <file>` | Save review to file |
| `--json` | Output as JSON |
| `--version` | Show version |

## Output Structure

- **Summary of Changes** — 2-3 sentence overview
- **Identified Risks** — Security, correctness, edge cases
- **Improvement Suggestions** — Actionable, prioritized
- **Code Quality Observations** — Patterns and style
- **Confidence Score** — High/Medium/Low
- **Final Verdict** — Approve / Changes Requested / Needs Discussion

## Example

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/676
```

## GitHub Action

See `.github/workflows/pr-review.yml` in the workflow output section.

## Requirements

- bash 4+, curl, python3
- GitHub token (repo scope)
- Claude API key

## License

MIT
