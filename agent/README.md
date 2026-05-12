# Claude PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and posts structured markdown comments.

## Quick Start

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

python3 agent/claude-review.py --pr https://github.com/owner/repo/pull/123
```

Or use the bash wrapper:

```bash
./agent/claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output Format

Each review includes:

- **Summary** — 2-3 sentence overview of changes
- **Identified Risks** — potential issues found
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — Low / Medium / High

## GitHub Action

Add `.github/workflows/claude-review.yml` to your repo. It automatically reviews every new PR and posts the result as a comment. Requires `ANTHROPIC_API_KEY` and `GITHUB_TOKEN` secrets.

## Sample Outputs

See [`samples/`](./samples/) for example reviews on real-looking PRs.

## Files

| File | Description |
|---|---|
| `agent/claude-review.py` | Main CLI tool |
| `agent/claude-review.sh` | Bash wrapper |
| `.github/workflows/claude-review.yml` | GitHub Action |
| `samples/sample-output-1.md` | Sample: JWT auth PR |
| `samples/sample-output-2.md` | Sample: DB connection pooling |
| `samples/sample-output-3.md` | Sample: Dark mode CSS |

## Requirements

- Python 3.8+
- Anthropic API key
- GitHub token (for private repos or higher rate limits)
