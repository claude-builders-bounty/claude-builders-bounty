# claude-review — Claude-Powered PR Reviewer

A CLI tool that fetches any GitHub PR diff and generates a structured Markdown code review using Claude AI.

## Install (2 commands)

```bash
pip install anthropic httpx
curl -o claude_review.py https://raw.githubusercontent.com/Nova17000/claude-builders-bounty/bounty-4-reviewer/reviewer/claude_review.py
```

## Usage

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...

python claude_review.py --pr https://github.com/owner/repo/pull/123
# Save to file:
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

```markdown
# PR Review: feat: add dark mode

**Author:** @alice  |  **Changes:** +84 -12 across 3 file(s)

## Summary
This PR adds dark mode support using CSS custom properties...

## Identified Risks
- Missing media query fallback for browsers that don't support prefers-color-scheme
- LocalStorage key collision risk if multiple themes are stored

## Improvement Suggestions
- `theme.ts:42`: Use `window.matchMedia` check before reading localStorage
- Consider extracting color tokens to a shared constants file

## Confidence Score
**High** — Implementation is straightforward with only minor edge cases.
```

## Requirements

- Python 3.9+
- `anthropic` + `httpx` packages
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `GITHUB_TOKEN` — from github.com/settings/tokens (needs `repo` scope for private repos)
