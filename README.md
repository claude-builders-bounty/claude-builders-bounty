# claude-review — PR Review Agent

A Claude Code sub-agent that reviews a GitHub PR and outputs a structured Markdown comment.

## Setup

1. Ensure `gh` CLI is authenticated (`gh auth login`)
2. Ensure `claude` CLI is installed and configured with GhostCLI or Anthropic API
3. Make the script executable: `chmod +x claude-review.sh`

## Usage

```bash
# Print review to stdout
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Post review as PR comment
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post
```

## Output Format

- **Summary**: 2–3 sentences describing changes
- **Identified Risks**: Bullet list of potential issues
- **Improvement Suggestions**: Actionable recommendations
- **Confidence Score**: Low / Medium / High

## Sample Outputs

See `samples/` directory for real PR review examples.
