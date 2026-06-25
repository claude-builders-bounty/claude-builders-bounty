# Claude PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured feedback.

## Installation

```bash
pip install requests
```

## Usage

```bash
# Review a PR
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

The workflow automatically reviews PRs when they are opened or updated.

## Output Format

- **Summary**: Brief overview of changes
- **Risks**: Potential issues or concerns
- **Suggestions**: Improvement recommendations
- **Confidence**: Low / Medium / High
