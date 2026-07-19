# claude-review

CLI + GitHub Action that reviews a GitHub pull request and emits a structured Markdown comment.

Built for the Opire [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) ($150).

## Requirements

- [`gh`](https://cli.github.com/) authenticated (`gh auth login`)
- `bash`, `jq` (optional but recommended)
- Optional: `ANTHROPIC_API_KEY` for Claude-powered narrative (heuristic mode works without it)

## Setup

```bash
chmod +x claude-review
export ANTHROPIC_API_KEY=sk-ant-...   # optional
```

## Usage (CLI)

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage (GitHub Action)

1. Copy `claude-review` and `.github/workflows/claude-review.yml` into your repo.
2. (Optional) Add repo secret `ANTHROPIC_API_KEY`.
3. Open or update a PR — the workflow posts a review comment automatically.

## Output format

- **Summary** — 2–3 sentences on what changed
- **Identified risks** — bullet list
- **Improvement suggestions** — bullet list
- **Confidence** — Low / Medium / High

## Sample runs

Real PR outputs included under `samples/`:

| Sample | PR |
|--------|-----|
| [review-1.md](samples/review-1.md) | [cli/cli#13864](https://github.com/cli/cli/pull/13864) |
| [review-2.md](samples/review-2.md) | [actions/checkout#2531](https://github.com/actions/checkout/pull/2531) |

## License

MIT
