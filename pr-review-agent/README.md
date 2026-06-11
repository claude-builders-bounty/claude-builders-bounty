# Claude PR Review Agent

A CLI tool that analyzes a GitHub pull request diff using Claude API and outputs a structured Markdown review.

## Setup (3 steps)
1. Get an Anthropic API key from https://console.anthropic.com
2. Export it: `export CLAUDE_API_KEY=sk-ant-...`
3. Run the tool: `./claude-review.sh --pr https://github.com/owner/repo/pull/123`

## Example Output
See `sample-output.md` for a review generated for a real PR.

## Files
- `claude-review.sh` – the review agent script
- `sample-output.md` – example review output
