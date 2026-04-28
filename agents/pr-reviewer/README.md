# Claude PR Reviewer Agent 🤖

A Claude Code sub-agent that reviews a GitHub PR and returns a structured Markdown review comment.

## Features
- Fetches PR metadata and diff using `gh` CLI.
- Generates a structured review using Claude.
- Summary of changes, risk identification, and improvement suggestions.

## Setup

1. **Install GitHub CLI**:
   ```bash
   brew install gh
   ```
2. **Install Claude Code CLI**:
   Follow the instructions at [anthropic.com](https://anthropic.com).
3. **Make script executable**:
   ```bash
   chmod +x agents/pr-reviewer/claude-review.py
   ```

## Usage

```bash
python3 agents/pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123
```

Alternatively, if you have `claude` in your PATH, the script will automatically pipe the review prompt to Claude.

## Structured Output Format

The agent provides output in the following format:
- **Summary of Changes**: 2-3 sentences.
- **Identified Risks**: Bulleted list.
- **Improvement Suggestions**: Bulleted list.
- **Confidence Score**: Low / Medium / High.
