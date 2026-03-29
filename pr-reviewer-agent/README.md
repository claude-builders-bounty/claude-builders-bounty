# claude-review

Structured PR reviews powered by Claude.

## Install

```bash
# No install needed — single-file Python script, stdlib only.
# Just download and run.
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-reviewer-agent/claude-review
chmod +x claude-review
```

## Usage

```bash
# Review a PR (prints to stdout + saves to .claude-reviews/)
python3 claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as comment
python3 claude-review --pr https://github.com/owner/repo/pull/123 --post

# Save to custom file
python3 claude-review --pr https://github.com/owner/repo/pull/123 -o review.md
```

## Setup (2 steps)

1. Install and authenticate the [GitHub CLI](https://cli.github.com/): `gh auth login`
2. Set your Anthropic API key: `export ANTHROPIC_API_KEY=sk-ant-...`

## Output Format

```markdown
## Summary
2-3 sentences: what this PR does and why.

## Identified Risks
- Specific bug/security/performance concern with file reference
- If none: "No significant risks identified"

## Improvement Suggestions
- Actionable recommendations, prioritized

## Confidence Score
Low / Medium / High with justification
```

## GitHub Action

Copy `.github/workflows/pr-review.yml` into your repo. Add `ANTHROPIC_API_KEY` to your repository secrets. Reviews post automatically on every PR.

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Model to use |

## Requirements

- Python 3.8+ (stdlib only — no pip install)
- `gh` CLI authenticated
- Anthropic API key

## License

MIT
