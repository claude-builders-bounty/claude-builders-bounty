# Claude PR Review Agent

CLI that reviews a GitHub pull request and prints a structured Markdown comment.

## Setup

```bash
chmod +x claude-review
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

The tool fetches the PR diff, asks Claude for a review when
`ANTHROPIC_API_KEY` is available, and falls back to deterministic local
heuristics when it is not.
