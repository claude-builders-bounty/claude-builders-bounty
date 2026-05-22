# claude-review — structured PR review agent

A Claude-powered CLI that reviews any public GitHub pull request and produces structured Markdown with:

- **Summary** — 2–3 sentences on what the PR changes
- **Risks** — bulleted list, each tied to a specific file or behavior
- **Suggestions** — bulleted list of concrete improvements
- **Confidence** — `Low` / `Medium` / `High` with justification

## Setup (3 steps)

1. Install dependencies:
   ```bash
   pip install anthropic
   gh auth login   # if not already
   ```

2. Set your API key (either an Anthropic API key, or a Claude Pro/Code OAuth token from `claude setup-token`):
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Run it:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123
   ```

Or install as an alias:
```bash
chmod +x claude_review.py
ln -s "$(pwd)/claude_review.py" /usr/local/bin/claude-review
claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage examples

```bash
# Default (Sonnet, output to stdout)
python claude_review.py --pr https://github.com/expressjs/express/pull/7212

# Write to a file too
python claude_review.py --pr https://github.com/owner/repo/pull/42 --output review.md

# Override the model (e.g. cheaper Haiku for small PRs)
python claude_review.py --pr https://github.com/owner/repo/pull/42 --model claude-haiku-4-5

# Larger diff budget for big PRs
python claude_review.py --pr https://github.com/owner/repo/pull/42 --max-diff-chars 120000
```

## GitHub Action variant

Create `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  pull-requests: write
  contents: read
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with: { python-version: '3.13' }
      - run: pip install anthropic
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py --pr "${{ github.event.pull_request.html_url }}" --output review.md
          gh pr comment "${{ github.event.pull_request.number }}" --body-file review.md
```

## Sample outputs

See [`example_outputs/`](example_outputs/) for real reviews against:

- `expressjs/express#7218` — small CI bump
- `expressjs/express#7191` — typo fix

## How it works

1. `gh pr view --json` fetches PR metadata (title, body, additions, deletions, refs)
2. `gh pr diff` fetches the unified diff
3. Diff truncated to `--max-diff-chars` (default 60K) to fit in context
4. Prompt instructs Claude to emit ONLY the structured Markdown sections — no preamble, no closing remarks
5. Output goes to stdout and optionally `--output <file>`

## Limitations / honest downsides

- For PRs above ~120K chars of diff, Claude misses context outside the truncation window. Mitigate by chunking by file in a future revision.
- Architectural / cross-cutting issues are easier for humans than Claude.
- Confidence label is calibrated, not certified — treat it as a hint, not a verdict.
- Style / lint nits are intentionally pushed to Suggestions; CI lint should still run.

## License

MIT
