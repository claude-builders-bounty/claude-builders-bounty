# claude-review

> Claude Code sub-agent that reviews a GitHub PR and posts a structured comment.

Dependency-free Python CLI. Works with any OpenAI-compatible endpoint —
Anthropic, Kilo, OpenRouter, vLLM, Ollama, LM Studio — or a GitHub Action.

## Usage

```bash
export CLAUDE_REVIEW_API_KEY=sk-...
./claude-review --pr https://github.com/owner/repo/pull/123

# offline heuristic mode (no API key needed)
./claude-review --pr owner/repo#123 --dry-run

# post the review as a PR comment
export GITHUB_TOKEN=ghp_...
./claude-review --pr 123 --post
```

Accepts a PR URL, `owner/repo#123`, or a bare number (uses the `origin`
remote of the current repo).

## Options

| Flag | Default | Description |
|---|---|---|
| `--pr` | — | PR URL, `owner/repo#N`, or bare number (required) |
| `--post` | off | Post the review as a PR comment (needs `GITHUB_TOKEN`) |
| `--out FILE` | — | Also write the review to a file |
| `--dry-run` | off | Offline heuristics (file stats, force-push, TODO, secret smells) |
| `--format` | `openai` | `openai` (OpenAI-compatible) or `anthropic` (native Messages API) |
| `--base-url` | `https://api.anthropic.com/v1/` | OpenAI-compatible base URL |
| `--model` | `claude-sonnet-4-20250514` | Model id |
| `--api-key` | `$CLAUDE_REVIEW_API_KEY` | API key |

## Environment

```bash
CLAUDE_REVIEW_API_KEY=...       # required unless --dry-run
CLAUDE_REVIEW_BASE_URL=...      # e.g. https://api.anthropic.com/v1/ or https://openrouter.ai/api/v1
CLAUDE_REVIEW_MODEL=...         # e.g. claude-sonnet-4-20250514, kilo-auto/free, openrouter/auto
GITHUB_TOKEN=...                # optional for reading (raises rate limits), required for --post
```

### Works with free models

Any OpenAI-compatible gateway works, including free router tiers:

```bash
CLAUDE_REVIEW_API_KEY=... \
CLAUDE_REVIEW_BASE_URL=https://openrouter.ai/api/v1 \
CLAUDE_REVIEW_MODEL=openrouter/auto \
./claude-review --pr owner/repo#123
```

## Output format

The LLM is constrained to a strict 4-section template:

```markdown
## Summary      — 2-3 sentences on what changed and why
## Risks        — bulleted, "- None identified" when genuinely none
## Suggestions  — bulleted, concrete and actionable
## Confidence   — Low | Medium | High
```

## GitHub Action

`.github/workflows/pr-review.yml` runs the reviewer on every opened /
synchronized PR and posts the result as an `issue_comment`:

```yaml
- uses: actions/checkout@v4
- uses: ./
  with:
    api-key: ${{ secrets.CLAUDE_REVIEW_API_KEY }}
    base-url: ${{ secrets.CLAUDE_REVIEW_BASE_URL }}
    model: ${{ secrets.CLAUDE_REVIEW_MODEL }}
```

## Verified sample outputs

- [`sample-outputs/claude-builders-bounty-4734.md`](sample-outputs/claude-builders-bounty-4734.md) — safety-hook PR
- [`sample-outputs/calcom-caldiy-30265.md`](sample-outputs/calcom-caldiy-30265.md) — URI-encoding fix

Both were produced by `claude-review` against the live GitHub API with model
`kilo-auto/free`.

## How it works

1. Clones nothing. Fetches PR metadata + unified diff straight from the
   GitHub REST API (authenticated when `GITHUB_TOKEN` is present).
2. Sends a review prompt with the diff (truncated to 60k chars) to the
   configured chat-completions endpoint.
3. Prints the structured review to stdout; optionally writes to `--out`,
   posts as a PR comment with `--post`.
4. No API key / no network: falls back to `--dry-run` heuristics so CI and
   smoke tests never hard-fail.

## Requirements

Python 3.8+, stdlib only. No `pip install` needed.
