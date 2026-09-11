# claude-review

CLI agent that reviews a GitHub pull request and prints structured Markdown.

## Requirements

- [GitHub CLI (`gh`)](https://cli.github.com/) authenticated (`gh auth login`)
- Python 3.10+
- Optional: `ANTHROPIC_API_KEY` for Claude-powered reviews (falls back to heuristics)

## Install

```bash
chmod +x agents/claude_review/claude_review.py
# optional symlink
ln -sf "$(pwd)/agents/claude_review/claude_review.py" ~/.local/bin/claude-review
```

Two-command install:

```bash
git clone --depth 1 https://github.com/zzzhang1127/claude-builders-bounty.git
chmod +x claude-builders-bounty/agents/claude_review/claude_review.py
```

## Usage

```bash
python3 agents/claude_review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123
```

Save output:

```bash
python3 agents/claude_review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

Heuristic-only mode (no API key):

```bash
python3 agents/claude_review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --offline
```

Environment variables:

| Name | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | unset | Enables Claude review |
| `CLAUDE_REVIEW_MODEL` | `claude-sonnet-4-20250514` | Anthropic model id |

## GitHub Action

See [`.github/workflows/claude-review-example.yml`](../../.github/workflows/claude-review-example.yml).

Trigger manually with a PR URL or run on `pull_request` events. The workflow posts the generated Markdown as a comment when `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` are configured.

## Output format

Every review includes:

- Summary of changes (2–3 sentences)
- Identified risks (bullet list)
- Improvement suggestions (bullet list)
- Confidence score: Low / Medium / High

Sample outputs for real PRs live in [`samples/`](samples/).
