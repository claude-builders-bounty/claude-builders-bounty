# Claude PR Review CLI

A CLI tool that reviews GitHub PRs using Claude and outputs structured Markdown.

## Installation (2 commands)

```bash
curl -O https://raw.githubusercontent.com/bdz2007-antgroup/claude-builders-bounty/bounty-4-pr-review/claude-review.sh && chmod +x claude-review.sh
export GITHUB_TOKEN=ghp_your_token_here  # optional, for private repos
```

## Usage

```bash
./claude-review.sh https://github.com/owner/repo/pull/123
```

## Output Format

Every review follows this structure:

| Section | Purpose |
|---------|---------|
| **Summary** | One-paragraph overview of the PR |
| **✅ Strengths** | Good decisions and patterns |
| **⚠️ Suggestions** | Non-blocking improvements with reasoning |
| **🐛 Issues** | Bugs/security with severity + fix |
| **Verdict** | APPROVE / REQUEST_CHANGES / COMMENT |

## Requirements

- Bash 4+
- `curl`, `python3` (for JSON parsing)
- Claude CLI (`npm install -g @anthropic-ai/claude-code`) — falls back to diff stats if unavailable
- `GITHUB_TOKEN` env var for private repos (optional)
